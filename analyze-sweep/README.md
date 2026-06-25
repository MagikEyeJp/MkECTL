# analyze-sweep

A tool that evaluates the **Accuracy** and **Precision** of wall-distance
measurements, per distance, from PLY point clouds, and outputs both a console
table and a plot (`accuracy_precision_plot.png`).

The trailing 4 digits of each directory name `dist_XXXX` are treated as the
Ground Truth (mm).

## Installation

```bash
pip install analyze-sweep            # from the distributed wheel
# e.g. pip install dist/analyze_sweep-1.0.0-py3-none-any.whl
```

To use open3d (it works with plyfile alone if open3d is absent):

```bash
pip install "analyze-sweep[open3d]"
```

## Usage

From a location that has a `sweep` directory containing `dist_0200`,
`dist_0300`, ...:

```bash
analyze-sweep                        # analyze ./sweep, write ./accuracy_precision_plot.png
analyze-sweep -s path/to/sweep -o out.png -t 50
python -m analyze_sweep --help       # can also be run as a module
```

| Option | Default | Description |
|---|---|---|
| `-s, --sweep-dir` | `./sweep` | directory containing `dist_XXXX` |
| `-o, --output` | `./accuracy_precision_plot.png` | output PNG path |
| `-t, --threshold` | `50` | outlier filter threshold in mm (wall median ± this value) |

## Use as a library

```python
from analyze_sweep import analyze, print_table, plot_results

results = analyze("sweep", threshold=50)
print_table(results)
plot_results(results, "out.png")
```

## Metric definitions

- **Accuracy** = (mean Z after filtering) − (Ground Truth)
- **Accuracy (%)** = Accuracy / Ground Truth × 100
- **Precision** = standard deviation of Z after filtering

The outlier filter keeps points within "measured-Z median ± threshold". Because
the real data has a systematic offset relative to GT, the wall is isolated
around the median rather than around GT. That offset itself is reported as
Accuracy.

## Building the wheel

```bash
python -m build       # produces a wheel and sdist under dist/
```
