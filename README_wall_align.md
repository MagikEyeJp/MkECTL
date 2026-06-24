# `wall_align.py` — Wall-facing Pan/Tilt alignment helper

A standalone CLI that makes the ILT-Pico sensor's optical axis perpendicular to
a large flat wall. It grabs a point cloud, fits the wall plane (RANSAC + least
squares), turns the plane normal into Pan/Tilt corrections, and either prints
them (manual) or drives the Keigan Pan/Tilt motors until the residual tilt is
below a threshold (auto). The slider axis is never touched.

This is a separate tool from the main `MkECTL.py` GUI (documented in
`README.md`); it reuses the same robot stack (`MachineBuilder`, `KeiganRobot`,
`machineFiles/*.json`) but acquires clouds through `pyiltrs2` / `reconstruct.py`.

## Coordinate convention

`pyiltrs2` vertices are in metres:

| axis | meaning      | correction |
| ---- | ------------ | ---------- |
| x    | left / right | Pan        |
| y    | up / down    | Tilt       |
| z    | depth (toward the wall) | — |

A perfectly facing sensor sees a wall normal of `(0, 0, ±1)`. The normal is
oriented so `nz ≥ 0`; `total tilt = acos(nz)` is the overall angle vs. the wall.

## Environment / install

Run in the **MkECTL Python environment** — the one that has the robot stack
(`PyQt5`, `qtutils`, `matplotlib`, `timeout_decorator`, `pyserial`). The
`pc_calibration` / `pc_reconstruction` venv usually lacks the robot deps, so
running there fails when it tries to connect the motors.

Install the point-cloud engine into that same env once:

```bash
pip install .../pc_reconstruction/dist/pyiltrs2-0.1.0-py3-none-any.whl
pip install pyusb        # only needed for --input usb (live)
```

If `wall_align.py` is run from outside the MkECTL repo, point it at the sources
with `--mkectl-dir /path/to/MkECTL` (or set `MKECTL_DIR`).

## Quick start

```bash
# 1) math self-check, no hardware
python3 wall_align.py --self-test

# 2) offline dry-run from a capture (no robot needed with --no-move)
python3 wall_align.py --calib-dir out --input file --capture cap.bin --no-move

# 3) live manual assist (measure & suggest; operator adjusts by hand)
python3 wall_align.py --calib-dir out --input usb

# 4) live auto optimisation (recommended robust settings)
python3 wall_align.py --auto --calib-dir ../pc_calibration/calib/ILT001/209/out/ \
    --frame 40 --threshold 0.3
```

`--calib-dir` is the directory holding `trajectory_data.bin` (+ `trajectory.json`).

## Modes

- **`--manual`** (default): measure once, print the current tilt and the
  recommended new Pan/Tilt, then wait. `Enter` re-measures, `Ctrl-C` quits. The
  operator turns the knobs.
- **`--auto`**: iterate. Each step measures, applies
  `new = cur + sign · gain · error` (clamped to `--max-step`), moves only Pan/Tilt,
  settles, re-measures. Stops on convergence, `--max-iter`, or the divergence
  guard.
- **`--no-move` / `--dry-run`**: never drive the robot; print suggestions only.
  Lets `--auto` simulate the loop for inspection without hardware.

## Capture backends

`--capture-backend`:

- `reconstruct` (auto-selected for `--input usb`): spawns `reconstruct.py` fresh
  per measurement. Robust for live USB across robot moves — a fresh subprocess
  opens/closes the device cleanly, avoiding stream stalls while a move blocks.
- `inproc` (auto-selected for `--input file`): keeps one `pyiltrs2` pipeline open
  and loops `wait_for_frames()`.

## Sign calibration (read before trusting `--auto`)

`--pan-sign` / `--tilt-sign` map the measured normal tilt to the direction the
motor must move. They depend on the rig/sensor mounting and **cannot be known on
paper**. Defaults are the known-good values for `CalibratorV2_REV`:
**`--pan-sign -1`, `--tilt-sign +1`** (the motors are mounted with opposite
rotation senses).

Before relying on `--auto`, FIRST run `--manual` (or `--auto --no-move`) and
confirm that one correction step *reduces* the error. If an axis runs the wrong
way, flip its sign.

### Divergence guard

After a move, if an axis you **actually moved** by at least `--diverge-margin`
sees its error grow by more than that margin, its sign is almost certainly
inverted and the loop stops with a message naming the axis to flip.

The "axis you actually moved" condition matters: near convergence an axis is
barely commanded, so measurement noise (or cross-coupling from the *other*
axis' large move) can bump its error without the sign being wrong. The guard
ignores an axis whose last commanded move was below `--diverge-margin`, so it
no longer false-trips on a barely-moved axis.

## Tuning for a noisy measurement

Plane-normal noise of ~0.5° is common. If so:

- the loop cannot reach a `--threshold` below the noise floor → raise it
  (e.g. `--threshold 0.3`);
- per-measurement noise can be comparable to `--diverge-margin`.

Mitigations:

| symptom | knob |
| --- | --- |
| noisy normal / non-convergence | `--frames 30…50` (averages more frames) |
| unrealistic convergence target | `--threshold 0.3` |
| oscillation / overshoot | lower `--gain` (e.g. `0.5`) |
| guard trips on noise | raise `--diverge-margin` (e.g. `1.0`) |
| too few in-range points | widen `--z-min`/`--z-max`, check laser/wall in view |

## Key CLI options

Run `python3 wall_align.py -h` for the full list. Frequently used:

```
Calibration / input (pyiltrs2)
  --calib-dir DIR        dir with trajectory_data.bin (+ trajectory.json)
  --bin / --json PATH    explicit paths instead of --calib-dir
  --input {usb,file}     usb = live (default), file = replay a --capture dump
  --capture PATH         captured EP1 dump (for --input file)
  --format {s16p0,s16p16}  default s16p0
  --scale-factor INT     default -2
  --h-total / --exposure   sensor timing/exposure passed to reconstruct.py

Robot
  --mkectl-dir DIR       where MkECTL sources live (default $MKECTL_DIR or script dir)
  --machine-file PATH    machineFiles/*.json (default machineFiles/CalibratorV2_REV.json)

Mode / control
  --auto | --manual      iterative optimise | measure & suggest (default)
  --no-move / --dry-run  never drive the robot
  --frames N             frames averaged per measurement (default 10)
  --threshold DEG        convergence angle (default 0.1)
  --gain G               correction gain 0<g<=1 (default 0.8)
  --max-iter N           default 20
  --max-step DEG         max move per iter (default 5.0)
  --settle S             post-move settle seconds (default 1.0)
  --pan-sign {1,-1}      default -1   (CalibratorV2_REV)
  --tilt-sign {1,-1}     default +1   (CalibratorV2_REV)
  --diverge-margin DEG   wrong-sign safeguard (default 0.5)
  --capture-backend {auto,reconstruct,inproc}

Point-cloud filtering
  --z-min / --z-max M    keep points in this depth window (default 0.05 / 5.0)
  --ransac-thresh M      inlier distance (default 0.005)
  --ransac-iter N        RANSAC hypotheses (default 300)

  --self-test            run the plane-fit math self-check and exit (no hardware)
```

> Note: `argparse` abbreviation means `--frame` is accepted as `--frames`.

## Reading the report

```
   current pan / tilt   :   2.031 /  -3.216 deg   ← robot getPosition()
   plane inliers        : 12056 / 24806  (RMS residual 2.797 mm)
   normal (nx, ny, nz)  : (-0.0094, +0.0125, +0.9999)
   pan error  (x tilt)  :  -0.536 deg   ← atan2(nx, nz); drives Pan
   tilt error (y tilt)  :  +0.718 deg   ← atan2(ny, nz); drives Tilt
   total tilt vs wall   :   0.896 deg   ← acos(nz)
   status               : NOT facing (threshold 0.100 deg)
```

Converged when `|pan error| ≤ threshold` **and** `|tilt error| ≤ threshold`.

## Troubleshooting

- **`ArrayMemoryError: Unable to allocate … (N, N)` during the SVD** — caused by
  too many points for a full-matrix SVD. Fixed in this tool (the plane fit uses
  `full_matrices=False`); if you see it again, reduce `--frames`.
- **`DIVERGING … wrong sign` immediately** — confirm `--pan-sign` / `--tilt-sign`
  with `--manual` first. If it only trips after a large move on the *other* axis
  while this axis was near zero, it is noise; raise `--frames` / `--diverge-margin`.
- **Never converges, errors hover ~0.5–1°** — measurement noise floor above the
  threshold. Raise `--frames` and `--threshold`; lower `--gain`.
- **`only N in-range points`** — wall not in view, laser off, or wrong z window.
  Adjust `--z-min`/`--z-max`; check the sensor sees the wall.
- **Missing robot dependency / cannot import MkECTL modules** — you are not in the
  MkECTL env, or `pyiltrs2` was installed into a different venv. Install the wheel
  into the MkECTL env, or pass `--mkectl-dir`.

## Relationship to the slider sweep

`wall_align.py` sets the Pan/Tilt pose so the sensor faces the wall; the
slider-sweep script (`script/slider_sweep_pointcloud.txt`) then sweeps the
slider distance with Pan/Tilt held. Align first, then run the sweep.
