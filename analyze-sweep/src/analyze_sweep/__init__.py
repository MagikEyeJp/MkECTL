#!/usr/bin/env python3
"""
Evaluate the Accuracy and Precision of wall-distance measurements, per distance,
from PLY point clouds contained in a ``sweep`` directory.

The trailing 4 digits of each directory name ``dist_XXXX`` are treated as the
Ground Truth (mm).

For each PLY the Z coordinate is extracted, background/floor/noise points are
removed as outliers, and then:
  - Accuracy  = (mean Z) - (Ground Truth)
  - Precision = standard deviation of Z
are computed, printed as a table and rendered as a plot.

The outlier filter is centered on the *median* of the measured Z (a robust
estimate of the wall location), keeping points within ``± threshold``.
The real data contains a systematic offset of +100 mm or more relative to GT;
filtering around GT would discard the wall itself, so the median is used as the
center. That systematic offset is correctly captured by Accuracy = (mean - GT).

PLY loading prefers open3d and falls back to plyfile when open3d is unavailable.
"""

import os
import re
import sys
import glob
import argparse

import numpy as np

# Use a non-interactive backend for matplotlib (savefig only).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


__version__ = "1.0.0"

__all__ = [
    "load_z_from_dir",
    "discover_distance_dirs",
    "filter_outliers",
    "compute_metrics",
    "analyze",
    "print_table",
    "plot_results",
    "main",
]


# ---- Defaults ---------------------------------------------------------------

DEFAULT_SWEEP_DIR = "sweep"                          # relative to cwd
DEFAULT_OUTPUT_PNG = "accuracy_precision_plot.png"   # relative to cwd
DEFAULT_THRESHOLD_MM = 50.0   # keep points within wall-median ± this value
DIR_PATTERN = re.compile(r"^dist_(\d+)$")


# ---- PLY loading ------------------------------------------------------------

def _load_ply_open3d(path):
    """Load a point cloud with open3d as an (N, 3) ndarray. Return None on miss."""
    try:
        import open3d as o3d
    except ImportError:
        return None
    pcd = o3d.io.read_point_cloud(path)
    pts = np.asarray(pcd.points)
    return pts if pts.size else None


def _load_ply_plyfile(path):
    """Load a point cloud with plyfile as an (N, 3) ndarray."""
    from plyfile import PlyData
    ply = PlyData.read(path)
    v = ply["vertex"].data
    return np.column_stack([v["x"], v["y"], v["z"]]).astype(np.float64)


def _select_loader():
    """Pick the available loader once (avoids importing on every call)."""
    try:
        import open3d  # noqa: F401
        return _load_ply_open3d, "open3d"
    except ImportError:
        return _load_ply_plyfile, "plyfile"


_PLY_LOADER, PLY_BACKEND = _select_loader()


def load_z_from_dir(dir_path):
    """Concatenate all PLYs in a directory and return the Z coordinates (1-D)."""
    z_all = []
    for ply_path in sorted(glob.glob(os.path.join(dir_path, "*.ply"))):
        pts = _PLY_LOADER(ply_path)
        if pts is None or pts.size == 0:
            continue
        z_all.append(pts[:, 2])
    if not z_all:
        return np.empty(0, dtype=np.float64)
    return np.concatenate(z_all)


# ---- Directory discovery ----------------------------------------------------

def discover_distance_dirs(sweep_dir):
    """Return ``dist_XXXX`` dirs as (ground_truth_mm, path), sorted by GT asc."""
    entries = []
    for name in os.listdir(sweep_dir):
        full = os.path.join(sweep_dir, name)
        if not os.path.isdir(full):
            continue
        m = DIR_PATTERN.match(name)
        if m:
            entries.append((int(m.group(1)), full))
    entries.sort(key=lambda e: e[0])
    return entries


# ---- Filtering and metrics --------------------------------------------------

def filter_outliers(z, threshold=DEFAULT_THRESHOLD_MM):
    """Keep points within the robust wall center (median) ± threshold.

    Removes background/floor/edge noise. Because GT has a large systematic
    offset, the filter is centered on the measured median rather than GT.
    Returns (inliers, removed_count, center).
    """
    center = float(np.median(z))
    mask = np.abs(z - center) <= threshold
    return z[mask], int(np.sum(~mask)), center


def compute_metrics(z_inliers, ground_truth):
    """Return Accuracy (mean error) and Precision (standard deviation)."""
    mean_z = float(np.mean(z_inliers))
    accuracy = mean_z - ground_truth       # signed deviation from GT
    precision = float(np.std(z_inliers))   # spread
    return mean_z, accuracy, precision


def analyze(sweep_dir=DEFAULT_SWEEP_DIR, threshold=DEFAULT_THRESHOLD_MM):
    """Process every directory and return a list of result dicts."""
    results = []
    for gt, dir_path in discover_distance_dirs(sweep_dir):
        z_raw = load_z_from_dir(dir_path)
        if z_raw.size == 0:
            print(f"[warning] {os.path.basename(dir_path)}: no valid points found. Skipping.",
                  file=sys.stderr)
            continue

        z_in, removed, center = filter_outliers(z_raw, threshold)
        if z_in.size == 0:
            print(f"[warning] {os.path.basename(dir_path)}: "
                  f"no points left after filtering. Skipping.", file=sys.stderr)
            continue

        mean_z, accuracy, precision = compute_metrics(z_in, gt)
        results.append({
            "ground_truth": gt,
            "center": center,
            "n_total": int(z_raw.size),
            "n_inliers": int(z_in.size),
            "n_removed": removed,
            "removed_pct": 100.0 * removed / z_raw.size,
            "mean_z": mean_z,
            "accuracy": accuracy,
            "accuracy_pct": 100.0 * accuracy / gt,   # error relative to GT
            "precision": precision,
        })
    return results


# ---- Display ----------------------------------------------------------------

def print_table(results):
    """Print the results to the console as a table."""
    header = (f"{'GT(mm)':>8} | {'Median(mm)':>10} | {'MeanZ(mm)':>10} | "
              f"{'Accuracy(mm)':>13} | {'Accuracy(%)':>12} | {'Precision(mm)':>14} | "
              f"{'Total':>8} | {'Inliers':>8} | {'Removed':>8} | {'Removed%':>8}")
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for r in results:
        print(f"{r['ground_truth']:>8} | {r['center']:>10.2f} | "
              f"{r['mean_z']:>10.2f} | {r['accuracy']:>+13.2f} | "
              f"{r['accuracy_pct']:>+11.2f}% | {r['precision']:>14.2f} | "
              f"{r['n_total']:>8} | {r['n_inliers']:>8} | {r['n_removed']:>8} | "
              f"{r['removed_pct']:>7.2f}%")
    print(sep)


# ---- Plotting ---------------------------------------------------------------

def plot_results(results, output_png=DEFAULT_OUTPUT_PNG,
                 threshold=DEFAULT_THRESHOLD_MM):
    """Render Accuracy (mm), Accuracy (%) and Precision as 3 stacked panels."""
    gts = [r["ground_truth"] for r in results]
    acc = [r["accuracy"] for r in results]
    acc_pct = [r["accuracy_pct"] for r in results]
    prec = [r["precision"] for r in results]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 11), sharex=True)

    # Panel 1: Accuracy in mm (deviation from GT; error bars show Precision).
    ax1.errorbar(gts, acc, yerr=prec, fmt="o-", color="tab:blue",
                 capsize=4, label="Accuracy (mean Z − GT)")
    ax1.axhline(0.0, color="gray", linestyle="--", linewidth=1,
                label="ideal (error = 0)")
    ax1.set_ylabel("Accuracy / Error (mm)")
    ax1.set_title("Wall Distance Measurement: Accuracy in mm "
                  "(error bars = Precision / std)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="best")

    # Panel 2: Accuracy as a percentage of GT.
    ax2.plot(gts, acc_pct, "D-", color="tab:green",
             label="Accuracy (% of GT) = (mean Z − GT) / GT × 100")
    ax2.axhline(0.0, color="gray", linestyle="--", linewidth=1,
                label="ideal (error = 0%)")
    ax2.set_ylabel("Accuracy / Error (% of GT)")
    ax2.set_title("Wall Distance Measurement: Accuracy as % of distance")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="best")
    # Annotate each point with its % value.
    for x, y in zip(gts, acc_pct):
        ax2.annotate(f"{y:+.1f}%", (x, y), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8)

    # Panel 3: Precision (standard deviation).
    ax3.plot(gts, prec, "s-", color="tab:red", label="Precision (std of Z)")
    ax3.set_xlabel("Ground Truth distance (mm)")
    ax3.set_ylabel("Precision / Std (mm)")
    ax3.set_title("Wall Distance Measurement: Precision")
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc="best")
    # Annotate each point with its Precision value.
    for x, y in zip(gts, prec):
        ax3.annotate(f"{y:.1f}", (x, y), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8)
    # Add headroom on top so annotations don't collide with the frame.
    pmin, pmax = min(prec), max(prec)
    margin = (pmax - pmin) * 0.12 or 1.0
    ax3.set_ylim(pmin - margin, pmax + margin * 1.8)

    ax3.set_xticks(gts)

    fig.suptitle(f"Accuracy & Precision vs Ground Truth "
                 f"(outlier filter: wall median ±{threshold:.0f} mm)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    print(f"\nSaved plot to: {output_png}")


# ---- Entry point ------------------------------------------------------------

def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="analyze-sweep",
        description="Evaluate Accuracy / Precision of distance measurements "
                    "from PLY point clouds in a sweep directory.",
    )
    parser.add_argument(
        "-s", "--sweep-dir", default=DEFAULT_SWEEP_DIR,
        help=f"sweep directory containing dist_XXXX (default: ./{DEFAULT_SWEEP_DIR})",
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT_PNG,
        help=f"output PNG path (default: ./{DEFAULT_OUTPUT_PNG})",
    )
    parser.add_argument(
        "-t", "--threshold", type=float, default=DEFAULT_THRESHOLD_MM,
        help=f"outlier filter threshold in mm: wall-median ± this value "
             f"(default: {DEFAULT_THRESHOLD_MM:.0f})",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """CLI entry point."""
    args = parse_args(argv)

    if not os.path.isdir(args.sweep_dir):
        print(f"[error] sweep directory not found: {args.sweep_dir}",
              file=sys.stderr)
        return 1

    print(f"PLY loading backend: {PLY_BACKEND}")
    print(f"sweep directory: {os.path.abspath(args.sweep_dir)}")
    print(f"outlier filter: wall median ± {args.threshold:.0f} mm\n")

    results = analyze(args.sweep_dir, args.threshold)
    if not results:
        print("[error] no valid results were produced.", file=sys.stderr)
        return 1

    print_table(results)
    plot_results(results, args.output, args.threshold)
    return 0


if __name__ == "__main__":
    sys.exit(main())
