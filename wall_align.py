#!/usr/bin/env python3
"""Wall-facing Pan/Tilt alignment helper for the MkECTL calibration rig.

Acquires a point cloud from the ILT-Pico sensor (via the pyrealsense2-compatible
``pyiltrs2`` wheel), fits the wall plane (RANSAC + least squares), and turns the
plane normal into Pan/Tilt corrections so the sensor optical axis can be made
perpendicular to a large flat wall at Z=0.

Two modes:
  * ``--manual``  (default) measure and print the current tilt and the
    recommended Pan/Tilt values; the operator adjusts by hand. Press Enter to
    re-measure, Ctrl-C to quit.
  * ``--auto``    iteratively drive Pan/Tilt (only those axes; the slider is
    left untouched) until the residual tilt is below ``--threshold`` degrees.

Coordinate convention (pyiltrs2 vertices, metres):
  x = left/right  -> Pan,  y = up/down -> Tilt,  z = depth (toward the wall).
A perfectly facing sensor sees a wall normal of (0, 0, +-1).

Environment
-----------
Run in the MkECTL Python environment (the one with PyQt5/qtutils for the robot).
Install the point-cloud engine into that same env once:

    pip install .../pc_reconstruction/dist/pyiltrs2-0.1.0-py3-none-any.whl
    pip install pyusb        # only needed for --input usb (live)

Examples
--------
    # math self-check, no hardware
    python3 wall_align.py --self-test

    # offline dry-run from a capture (no robot needed with --no-move)
    python3 wall_align.py --calib-dir out --input file --capture cap.bin --no-move

    # live manual assist (default machine file)
    python3 wall_align.py --calib-dir out --input usb

    # live auto optimisation
    python3 wall_align.py --calib-dir out --input usb --auto

Sign calibration
----------------
``--pan-sign`` / ``--tilt-sign`` map the measured normal tilt to the direction
the motor must move; they depend on the rig/sensor mounting and CANNOT be known
on paper. On real hardware, FIRST run ``--manual`` (or ``--auto --no-move``) and
check that one correction step reduces the error before trusting ``--auto``.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Where the MkECTL sources (MachineBuilder, KeiganRobot, machineFiles/, ...) live.
# Defaults to the env var MKECTL_DIR, else this script's own directory (the case
# when wall_align.py is run from inside the MkECTL repo). Override with
# --mkectl-dir when wall_align.py has been copied elsewhere (e.g. ~/iltpico).
DEFAULT_MKECTL_DIR = os.environ.get("MKECTL_DIR", _SCRIPT_DIR)
DEFAULT_MACHINE_FILE_NAME = os.path.join("machineFiles", "CalibratorV2_REV.json")


# --------------------------------------------------------------------------- #
# Geometry / plane fitting (pure numpy, no hardware)
# --------------------------------------------------------------------------- #
def fit_plane_ransac(pts, thresh=0.005, iters=300, rng=None):
    """Fit a plane to ``pts`` (N,3) with RANSAC, refined by least squares.

    :param thresh: inlier point-to-plane distance [same unit as pts, i.e. m]
    :param iters:  number of RANSAC hypotheses
    :returns: (normal(3,), point_on_plane(3,), inlier_mask(N,)).
              The normal is unit length and oriented so that nz >= 0.
    """
    pts = np.asarray(pts, dtype=np.float64)
    n = len(pts)
    if n < 3:
        raise ValueError("need at least 3 points to fit a plane (got %d)" % n)
    if rng is None:
        rng = np.random.default_rng()

    best_inliers = None
    best_count = -1
    for _ in range(iters):
        idx = rng.choice(n, size=3, replace=False)
        p0, p1, p2 = pts[idx]
        normal = np.cross(p1 - p0, p2 - p0)
        norm = np.linalg.norm(normal)
        if norm < 1e-12:
            continue                                   # degenerate (collinear)
        normal = normal / norm
        dist = np.abs((pts - p0) @ normal)
        inliers = dist < thresh
        count = int(inliers.sum())
        if count > best_count:
            best_count = count
            best_inliers = inliers

    if best_inliers is None or best_count < 3:
        # fall back to a plain least-squares fit over everything
        best_inliers = np.ones(n, dtype=bool)

    normal, point = _lsq_plane(pts[best_inliers])
    # final inlier set against the refined plane
    dist = np.abs((pts - point) @ normal)
    inliers = dist < thresh
    if inliers.sum() >= 3:
        normal, point = _lsq_plane(pts[inliers])
    else:
        inliers = best_inliers

    if normal[2] < 0:                                  # orient toward the sensor
        normal = -normal
    return normal, point, inliers


def _lsq_plane(pts):
    """Least-squares plane through ``pts`` via SVD. Returns (normal, centroid)."""
    centroid = pts.mean(axis=0)
    # full_matrices=False keeps U at (N,3) instead of (N,N): we only need vh (3,3),
    # and a full U for tens of thousands of points would need many GiB.
    _, _, vh = np.linalg.svd(pts - centroid, full_matrices=False)
    normal = vh[-1]                                    # smallest singular vector
    return normal / np.linalg.norm(normal), centroid


def plane_residual_mm(pts, normal, point):
    """RMS point-to-plane distance in millimetres (pts in metres)."""
    dist = (np.asarray(pts) - point) @ normal
    return float(np.sqrt(np.mean(dist ** 2)) * 1000.0)


def normal_to_errors(normal):
    """Map a wall normal (nz>=0) to (pan_err, tilt_err, total_tilt) in degrees.

    pan_err  > 0 : normal leans toward +x -> sensor yawed; correct Pan.
    tilt_err > 0 : normal leans toward +y -> sensor pitched; correct Tilt.
    total_tilt   : overall angle between the normal and the z axis.
    """
    nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])
    pan_err = math.degrees(math.atan2(nx, nz))
    tilt_err = math.degrees(math.atan2(ny, nz))
    total_tilt = math.degrees(math.acos(max(-1.0, min(1.0, nz))))
    return pan_err, tilt_err, total_tilt


# --------------------------------------------------------------------------- #
# Point-cloud acquisition (pyiltrs2)
# --------------------------------------------------------------------------- #
def _build_pipeline(args):
    """Create and start a pyiltrs2 pipeline from CLI args. Returns (pipe, rs)."""
    import pyiltrs2 as rs                              # imported lazily

    pipe = rs.pipeline()
    cfg = rs.config()
    cfg.enable_ilt_calibration(calib_dir=args.calib_dir,
                               bin_path=args.bin_path, json_path=args.json_path)
    cfg.enable_stream(rs.stream.depth, args.width, args.height, rs.format.z16, 30)
    cfg.set_ilt_format(args.format, args.scale_factor)

    if args.input == "file":
        if not args.capture:
            raise SystemExit("error: --input file requires --capture")
        cfg.enable_device_from_file(args.capture)
    else:
        cfg.set_ilt_camera(vid=args.vid, pid=args.pid,
                           h_total=args.h_total, exposure=args.exposure,
                           v_total=args.v_total, gain=args.cam_gain,
                           blc_target=args.blc_target, laser=args.laser)
    pipe.start(cfg)
    return pipe, rs


class InsufficientPointsError(RuntimeError):
    """Raised when a measurement returns too few in-range points to fit a plane."""


class PointCloudSource:
    """A pyiltrs2 pipeline kept open across measurements.

    Opening the pipeline once (rather than per measurement) matters for live
    USB: re-running the start-up sequence each time can leave the sensor
    returning empty / all-zero frames. The realsense idiom is to start once and
    loop ``wait_for_frames()``.
    """

    def __init__(self, args):
        self.pipe, self.rs = _build_pipeline(args)
        self.pc = self.rs.pointcloud()
        self.frames = args.frames
        self.z_min = args.z_min
        self.z_max = args.z_max
        self.min_points = args.min_points
        self._drain(args.warmup)                       # discard partial first frames

    def _drain(self, n):
        for _ in range(max(0, n)):
            try:
                self.pipe.wait_for_frames()
            except RuntimeError:
                break

    def capture(self):
        """Grab frames and return filtered (N,3) points [m].

        Raises InsufficientPointsError if fewer than ``min_points`` survive,
        so callers can retry instead of crashing on a transient empty frame.
        """
        chunks = []
        grabbed = 0
        empty = 0
        while grabbed < self.frames:
            try:
                frames = self.pipe.wait_for_frames()
            except RuntimeError:
                break                                  # end of a file capture
            depth = frames.get_depth_frame()
            if not depth:
                continue
            verts = (np.asanyarray(self.pc.calculate(depth).get_vertices())
                     .view(np.float32).reshape(-1, 3).astype(np.float64))
            verts = filter_points(verts, self.z_min, self.z_max)
            if len(verts) == 0:
                empty += 1
                if empty > 2 * self.frames:            # give up on a dead stream
                    break
                continue
            chunks.append(verts)
            grabbed += 1

        pts = np.concatenate(chunks, axis=0) if chunks else np.empty((0, 3))
        if len(pts) < self.min_points:
            raise InsufficientPointsError(
                "only %d in-range points (need >= %d); is the wall in view / "
                "laser on / z window [%.2f, %.2f] m correct?"
                % (len(pts), self.min_points, self.z_min, self.z_max))
        return pts

    def close(self):
        try:
            self.pipe.stop()
        except Exception:
            pass


def load_ply_xyz(path):
    """Read an ASCII PLY (x y z per vertex) into an (N,3) array. Units as-stored."""
    pts = []
    with open(path, "r") as fp:
        in_body = False
        for line in fp:
            if not in_body:
                if line.strip() == "end_header":
                    in_body = True
                continue
            parts = line.split()
            if len(parts) >= 3:
                pts.append((float(parts[0]), float(parts[1]), float(parts[2])))
    return np.array(pts, dtype=np.float64).reshape(-1, 3)


class ReconstructSource:
    """Capture by spawning reconstruct.py fresh each measurement.

    The in-process live pipeline can stall across iterations: while the robot
    move blocks for seconds nobody drains the USB stream, so the bulk buffer
    overflows and later frames come back empty / partial. A fresh subprocess
    opens and closes the USB device cleanly every time (the path proven by the
    slider-sweep ``exec`` workflow), which is robust to that.
    """

    def __init__(self, args):
        import shutil
        self.args = args
        self.python = args.python
        self.reconstruct_py = args.reconstruct_py
        if not os.path.isfile(self.reconstruct_py):
            raise SystemExit(
                "error: reconstruct.py not found at %r; pass --reconstruct-py"
                % self.reconstruct_py)
        self._tmp = None
        self._shutil = shutil

    def capture(self):
        import subprocess
        import tempfile
        import glob

        a = self.args
        tmp = tempfile.mkdtemp(prefix="wall_align_")
        try:
            argv = [self.python, self.reconstruct_py,
                    "--calib-dir", a.calib_dir,
                    "--input", "usb",
                    "--frame", "all", "--max-frames", str(a.frames),
                    "--format", a.format, "--scale-factor", str(a.scale_factor),
                    "--h-total", str(a.h_total), "--exposure", str(a.exposure),
                    "--emit", "ply", "--out", tmp, "--prefix", "frame"]
            if a.bin_path:
                argv += ["--bin", a.bin_path]
            if a.json_path:
                argv += ["--json", a.json_path]
            res = subprocess.run(argv, capture_output=True, text=True)
            if res.returncode != 0:
                raise InsufficientPointsError(
                    "reconstruct.py failed (rc=%d): %s"
                    % (res.returncode, (res.stderr or res.stdout).strip()[-300:]))

            files = sorted(glob.glob(os.path.join(tmp, "frame*.ply")))
            chunks = [load_ply_xyz(f) for f in files]
            chunks = [c for c in chunks if len(c)]
            pts_mm = np.concatenate(chunks, axis=0) if chunks else np.empty((0, 3))
        finally:
            self._shutil.rmtree(tmp, ignore_errors=True)

        pts = filter_points(pts_mm / 1000.0, a.z_min, a.z_max)   # mm -> m
        if len(pts) < a.min_points:
            raise InsufficientPointsError(
                "only %d in-range points (need >= %d); is the wall in view / "
                "laser on / z window [%.2f, %.2f] m correct?"
                % (len(pts), a.min_points, a.z_min, a.z_max))
        return pts

    def close(self):
        pass


def filter_points(pts, z_min, z_max):
    """Keep finite points whose z lies in [z_min, z_max] (drops zero/NaN dots)."""
    pts = np.asarray(pts, dtype=np.float64)
    mask = np.isfinite(pts).all(axis=1)
    mask &= (pts[:, 2] >= z_min) & (pts[:, 2] <= z_max)
    return pts[mask]


# --------------------------------------------------------------------------- #
# Robot (KeiganRobot via MachineBuilder)
# --------------------------------------------------------------------------- #
def connect_robot(machine_file, mkectl_dir):
    """Build, connect and initialize the robot. Returns the robot controller.

    initialize() only enables the motors (no homing / no movement), so the
    current Pan/Tilt pose is preserved. ``mkectl_dir`` is prepended to sys.path
    so the MkECTL modules (MachineBuilder, KeiganRobot, ...) import even when
    wall_align.py was copied outside the repo.
    """
    if mkectl_dir and mkectl_dir not in sys.path:
        sys.path.insert(0, mkectl_dir)
    # Third-party deps that the robot stack (KeiganRobot) imports at module load.
    _ROBOT_DEPS = {"PyQt5", "qtutils", "matplotlib", "timeout_decorator", "serial"}
    try:
        from MachineBuilder import MachineBuilder
    except ModuleNotFoundError as e:
        if e.name in _ROBOT_DEPS or (e.name or "").split(".")[0] in _ROBOT_DEPS:
            raise SystemExit(
                "error: missing robot dependency %r.\n"
                "       wall_align.py must run in the MkECTL Python environment\n"
                "       (the one with PyQt5/qtutils/matplotlib/timeout_decorator/\n"
                "       pyserial), and pyiltrs2 must be installed INTO that same env:\n"
                "         <mkectl-env>/pip install pyiltrs2-0.1.0-py3-none-any.whl\n"
                "       The pc_calibration/pc_reconstruction venv usually lacks the\n"
                "       robot deps, so running there fails here." % e.name)
        raise SystemExit(
            "error: cannot import MkECTL modules (%s) from %r.\n"
            "       Run wall_align.py from inside the MkECTL repo, or pass\n"
            "       --mkectl-dir /path/to/MkECTL (or set MKECTL_DIR)."
            % (e.name, mkectl_dir))

    with open(machine_file) as f:
        params = json.load(f)
    machine = MachineBuilder.build(params)
    if machine is None or machine.robot is None:
        raise SystemExit("error: could not build a robot from %s" % machine_file)

    robot = machine.robot
    robot.connect()
    if not robot.initialize():
        raise SystemExit("error: robot.initialize() failed "
                         "(motors not all found / not ready)")
    return robot


def read_pan_tilt(robot):
    """Return (pan, tilt) in degrees from the robot, or (None, None)."""
    pos = robot.getPosition()
    if not isinstance(pos, dict):
        return None, None
    return pos.get("pan"), pos.get("tilt")


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def print_report(iteration, cur_pan, cur_tilt, normal, residual_mm,
                 n_inliers, n_total, pan_err, tilt_err, total_tilt, threshold):
    converged = abs(pan_err) <= threshold and abs(tilt_err) <= threshold
    def fmt(v):
        return "  n/a " if v is None else "%7.3f" % v
    print("=" * 60)
    print(" Wall alignment  -  iteration %d" % iteration)
    print("-" * 60)
    print("   current pan / tilt   : %s / %s deg" % (fmt(cur_pan), fmt(cur_tilt)))
    print("   plane inliers        : %d / %d  (RMS residual %.3f mm)"
          % (n_inliers, n_total, residual_mm))
    print("   normal (nx, ny, nz)  : (%+.4f, %+.4f, %+.4f)"
          % (normal[0], normal[1], normal[2]))
    print("   pan error  (x tilt)  : %+7.3f deg" % pan_err)
    print("   tilt error (y tilt)  : %+7.3f deg" % tilt_err)
    print("   total tilt vs wall   : %7.3f deg" % total_tilt)
    print("   status               : %s (threshold %.3f deg)"
          % ("FACING (converged)" if converged else "NOT facing", threshold))
    print("=" * 60)
    return converged


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #
def _clamp(v, limit):
    return max(-limit, min(limit, v))


def measure(args, source):
    """Capture, fit, return (normal, residual_mm, n_inliers, n_total, errs).

    Retries a few times on a transient empty capture before giving up.
    """
    last = None
    for _ in range(max(1, args.measure_retries)):
        try:
            pts = source.capture()
            break
        except InsufficientPointsError as e:
            last = e
            print("   warning: %s -- retrying" % e)
    else:
        raise last
    normal, point, inliers = fit_plane_ransac(
        pts, thresh=args.ransac_thresh, iters=args.ransac_iter)
    residual_mm = plane_residual_mm(pts[inliers], normal, point)
    errs = normal_to_errors(normal)
    return normal, residual_mm, int(inliers.sum()), len(pts), errs


def run_manual(args, robot, source):
    cur_pan, cur_tilt = read_pan_tilt(robot) if robot else (None, None)
    it = 0
    while True:
        it += 1
        normal, residual_mm, n_in, n_tot, (pan_err, tilt_err, total) = measure(args, source)
        print_report(it, cur_pan, cur_tilt, normal, residual_mm, n_in, n_tot,
                     pan_err, tilt_err, total, args.threshold)
        if cur_pan is not None:
            new_pan = cur_pan + args.pan_sign * args.gain * pan_err
            new_tilt = cur_tilt + args.tilt_sign * args.gain * tilt_err
            print("   suggested  pan -> %7.3f  (%+.3f)" %
                  (new_pan, new_pan - cur_pan))
            print("   suggested tilt -> %7.3f  (%+.3f)" %
                  (new_tilt, new_tilt - cur_tilt))
        else:
            print("   (no robot connected: showing tilt only)")
        try:
            input("\n[Enter] to re-measure, [Ctrl-C] to quit ... ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if robot:
            cur_pan, cur_tilt = read_pan_tilt(robot)


def run_auto(args, robot, source):
    import time

    cur_pan, cur_tilt = read_pan_tilt(robot) if robot else (None, None)
    prev_abs = None                                    # (|pan_err|, |tilt_err|) pre-move
    prev_d = None                                      # (d_pan, d_tilt) of the last move
    for it in range(1, args.max_iter + 1):
        normal, residual_mm, n_in, n_tot, (pan_err, tilt_err, total) = measure(args, source)
        converged = print_report(it, cur_pan, cur_tilt, normal, residual_mm,
                                  n_in, n_tot, pan_err, tilt_err, total,
                                  args.threshold)
        if converged:
            print("Converged after %d iteration(s)." % it)
            return
        if cur_pan is None:
            print("error: --auto needs a connected robot (or use --no-move)")
            return

        # Divergence guard: if a move we actually commanded on an axis made that
        # axis' error grow, its sign is almost certainly inverted. Only judge an
        # axis we moved by at least diverge_margin: with the right sign such a move
        # reduces the error by ~|d|, so a wrong sign grows it by ~|d|. A smaller
        # move therefore cannot push the error past the margin, so any growth after
        # one is measurement noise (or cross-coupling from the other axis' move),
        # not a sign error -- don't blame an axis that barely moved.
        if prev_abs is not None and prev_d is not None and not args.no_move:
            bad = []
            if (abs(prev_d[0]) >= args.diverge_margin
                    and abs(pan_err) > prev_abs[0] + args.diverge_margin):
                bad.append("--pan-sign (try %d)" % (-args.pan_sign))
            if (abs(prev_d[1]) >= args.diverge_margin
                    and abs(tilt_err) > prev_abs[1] + args.diverge_margin):
                bad.append("--tilt-sign (try %d)" % (-args.tilt_sign))
            if bad:
                print("DIVERGING: error grew after a real move on that axis -> "
                      "wrong sign: %s. Stopping." % ", ".join(bad))
                return
        prev_abs = (abs(pan_err), abs(tilt_err))

        d_pan = _clamp(args.pan_sign * args.gain * pan_err, args.max_step)
        d_tilt = _clamp(args.tilt_sign * args.gain * tilt_err, args.max_step)
        prev_d = (d_pan, d_tilt)
        new_pan, new_tilt = cur_pan + d_pan, cur_tilt + d_tilt
        print("   move pan %+.3f -> %.3f , tilt %+.3f -> %.3f"
              % (d_pan, new_pan, d_tilt, new_tilt))

        if args.no_move:
            print("   --no-move: not driving the robot.")
            cur_pan, cur_tilt = new_pan, new_tilt      # simulate for the report
        else:
            # moveTo with only pan/tilt leaves the slider untouched.
            if robot.moveTo({"pan": new_pan, "tilt": new_tilt}, True):
                print("Aborted by robot.")
                return
            time.sleep(args.settle)
            cur_pan, cur_tilt = read_pan_tilt(robot)

    print("Reached --max-iter (%d) without converging." % args.max_iter)


# --------------------------------------------------------------------------- #
# Self-test (no hardware)
# --------------------------------------------------------------------------- #
def self_test():
    """Synthesise a tilted noisy wall and check the math recovers the angles."""
    rng = np.random.default_rng(0)
    pan_deg, tilt_deg = 3.0, -2.0
    # Build a wall normal tilted by pan about y and tilt about x, then sample a
    # planar patch ~2 m away with gaussian noise and 10% outliers.
    rp, rt = math.radians(pan_deg), math.radians(tilt_deg)
    normal_true = np.array([math.sin(rp) * math.cos(rt),
                            math.cos(rp) * math.sin(rt),
                            math.cos(rp) * math.cos(rt)])
    normal_true /= np.linalg.norm(normal_true)
    # two in-plane basis vectors
    a = np.cross(normal_true, [0, 0, 1.0]); a /= np.linalg.norm(a)
    b = np.cross(normal_true, a)
    center = normal_true * 2.0
    n = 4000
    uv = rng.uniform(-0.5, 0.5, size=(n, 2))
    pts = center + uv[:, :1] * a + uv[:, 1:] * b
    pts += rng.normal(0, 0.001, size=pts.shape)        # 1 mm noise
    n_out = n // 10
    pts[:n_out] += rng.normal(0, 0.3, size=(n_out, 3)) # outliers

    normal, point, inliers = fit_plane_ransac(pts, thresh=0.005, iters=400, rng=rng)
    pan_err, tilt_err, total = normal_to_errors(normal)
    print("self-test: recovered pan=%.4f (exp %.1f), tilt=%.4f (exp %.1f), "
          "inliers=%d/%d" % (pan_err, pan_deg, tilt_err, tilt_deg,
                             int(inliers.sum()), n))
    ok = abs(pan_err - pan_deg) < 0.1 and abs(tilt_err - tilt_deg) < 0.1
    if not ok:
        print("SELF-TEST FAILED", file=sys.stderr)
        return 1
    print("SELF-TEST PASSED")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_arg_parser():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

    g = ap.add_argument_group("calibration / input (pyiltrs2)")
    g.add_argument("--calib-dir", help="dir with trajectory_data.bin (+ trajectory.json)")
    g.add_argument("--bin", dest="bin_path", help="path to trajectory_data.bin")
    g.add_argument("--json", dest="json_path", help="path to trajectory.json")
    g.add_argument("--input", choices=("usb", "file"), default="usb")
    g.add_argument("--capture", help="captured EP1 dump (for --input file)")
    g.add_argument("--format", choices=("s16p0", "s16p16"), default="s16p0")
    g.add_argument("--scale-factor", type=int, default=-2)
    g.add_argument("--width", type=int, default=640)
    g.add_argument("--height", type=int, default=480)
    g.add_argument("--vid", type=lambda s: int(s, 0), default=None)
    g.add_argument("--pid", type=lambda s: int(s, 0), default=None)
    g.add_argument("--h-total", type=int, default=1280)
    g.add_argument("--exposure", type=int, default=30)
    g.add_argument("--v-total", type=int, default=None)
    g.add_argument("--cam-gain", dest="cam_gain", type=int, default=None,
                   help="sensor analog gain (passed to set_ilt_camera)")
    g.add_argument("--blc-target", type=int, default=None)
    g.add_argument("--laser", type=int, default=None)

    g = ap.add_argument_group("robot")
    g.add_argument("--mkectl-dir", default=DEFAULT_MKECTL_DIR,
                   help="directory holding the MkECTL sources (MachineBuilder, "
                        "KeiganRobot, machineFiles/). Default: $MKECTL_DIR or the "
                        "wall_align.py directory.")
    g.add_argument("--machine-file", default=None,
                   help="machineFiles/*.json describing the Keigan motors "
                        "(default: <mkectl-dir>/%s)" % DEFAULT_MACHINE_FILE_NAME)

    g = ap.add_argument_group("mode / control")
    mode = g.add_mutually_exclusive_group()
    mode.add_argument("--auto", action="store_true", help="iterative auto optimisation")
    mode.add_argument("--manual", action="store_true",
                      help="measure & suggest, operator adjusts (default)")
    g.add_argument("--no-move", "--dry-run", dest="no_move", action="store_true",
                   help="never drive the robot; show suggestions only")
    g.add_argument("--frames", type=int, default=10, help="frames averaged per measurement")
    g.add_argument("--warmup", type=int, default=2,
                   help="frames discarded after the pipeline opens (partial first frames)")
    g.add_argument("--min-points", type=int, default=50,
                   help="min in-range points required for a valid measurement")
    g.add_argument("--measure-retries", type=int, default=3,
                   help="retries on a transient empty capture before giving up")
    g.add_argument("--capture-backend", choices=("auto", "reconstruct", "inproc"),
                   default="auto",
                   help="how to grab clouds: 'reconstruct' spawns reconstruct.py "
                        "fresh per measurement (robust for live USB across moves); "
                        "'inproc' keeps a pyiltrs2 pipeline open. "
                        "auto = reconstruct for usb, inproc for file.")
    g.add_argument("--reconstruct-py",
                   default=os.path.normpath(os.path.join(
                       DEFAULT_MKECTL_DIR, "..", "pc_reconstruction", "reconstruct.py")),
                   help="path to reconstruct.py (for --capture-backend reconstruct)")
    g.add_argument("--python", default=sys.executable,
                   help="interpreter used to run reconstruct.py (default: this one)")
    g.add_argument("--threshold", type=float, default=0.1, help="convergence [deg]")
    g.add_argument("--gain", dest="gain", type=float, default=0.8,
                   help="correction gain (0<g<=1)")
    g.add_argument("--max-iter", type=int, default=20)
    g.add_argument("--max-step", type=float, default=5.0, help="max move per iter [deg]")
    g.add_argument("--settle", type=float, default=1.0, help="post-move settle [s]")
    # Known-good signs for CalibratorV2_REV: pan -1, tilt +1 (motors mounted with
    # opposite rotation senses). Flip if the rig diverges (the guard will say so).
    g.add_argument("--pan-sign", type=int, choices=(1, -1), default=-1)
    g.add_argument("--tilt-sign", type=int, choices=(1, -1), default=1)
    g.add_argument("--diverge-margin", type=float, default=0.5,
                   help="stop if an axis error grows by more than this [deg] after a "
                        "move (wrong sign safeguard)")

    g = ap.add_argument_group("point-cloud filtering")
    g.add_argument("--z-min", type=float, default=0.05, help="min z [m]")
    g.add_argument("--z-max", type=float, default=5.0, help="max z [m]")
    g.add_argument("--ransac-thresh", type=float, default=0.005, help="inlier dist [m]")
    g.add_argument("--ransac-iter", type=int, default=300)

    ap.add_argument("--self-test", action="store_true",
                    help="run the plane-fit math self-check and exit (no hardware)")
    return ap


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.calib_dir and not args.bin_path:
        raise SystemExit("error: provide --calib-dir (or --bin) for the sensor")

    # Connect the robot unless we are only measuring (--no-move).
    robot = None
    if not args.no_move:
        # Create a QApplication as a safety net for any Qt-bound robot code.
        try:
            from PyQt5 import QtWidgets
            if QtWidgets.QApplication.instance() is None:
                QtWidgets.QApplication(sys.argv[:1])
        except Exception:
            pass
        machine_file = args.machine_file or os.path.join(
            args.mkectl_dir, DEFAULT_MACHINE_FILE_NAME)
        robot = connect_robot(machine_file, args.mkectl_dir)
    else:
        print("--no-move: robot not connected (measurement only).")

    # Choose the capture backend. Live USB defaults to spawning reconstruct.py
    # fresh per measurement (robust to stream stalls across robot moves); file
    # input uses the in-process pyiltrs2 pipeline.
    backend = args.capture_backend
    if backend == "auto":
        backend = "reconstruct" if args.input == "usb" else "inproc"
    if backend == "reconstruct":
        source = ReconstructSource(args)
    else:
        source = PointCloudSource(args)
    try:
        if args.auto:
            run_auto(args, robot, source)
        else:
            run_manual(args, robot, source)
    finally:
        source.close()
        if robot is not None:
            try:
                robot.disconnect()
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
