# ILT-Pico Distance Accuracy Evaluation Procedure (for first-time operators)

A step-by-step guide for evaluating the **distance accuracy / precision** of an
ILT-Pico sensor at multiple distances using the CalibratorV2 rig, written so that
someone doing it for the first time can follow along.

Related tools: `wall_align.py` (→ `README_wall_align.md`),
`script/slider_sweep_pointcloud.txt`, MkECTL GUI (→ `README.md`).

---

## 0. What this procedure does (overview)

Make the sensor **face** a large flat wall, then **sweep the distance** with the
slider and capture many point-cloud frames at each distance. From the Z (depth)
of the points that hit the wall, the sensor-to-wall distance is computed at each
distance.

- **accuracy (bias)** = (mean measured distance) − (commanded slider distance)
  - The ground truth is the "commanded slider distance", assuming the wall is
    flat and the slider axis is perpendicular to the wall.
- **precision (spread)** = standard deviation of the measured distance
  (across frames at the same distance)

```
            ground truth (commanded)
                |
  precision →  |←→|   (frame-to-frame spread)
        ●●●●●●●|●●●●●
        └──────┘
       accuracy = offset of the mean
```

### Overall flow

| Step | Content | Tools |
| --- | --- | --- |
| Prereq | Generate the sensor calibration data (`out/`) (first time, per model — Chapter 4) | mkestudio / pc_calibration |
| A | Make the sensor face the wall | `wall_align.py` |
| B | Determine the mounting offset and apply it to the script | distance meter + script edit |
| C | Run the slider sweep and collect point clouds | MkECTL GUI |
| D | Compute accuracy / precision from the point clouds | `analyze-sweep` tool (Chapter 8) |

> **Important prerequisites (check first)**
> - The wall must be **flat and large**, filling the sensor FOV at both the
>   shortest and longest distance.
> - The **slider travel direction must be perpendicular to the wall** (the
>   accuracy ground truth depends on this).
> - A Keigan motor serial port can be **held by only one process**.
>   Do **not** run `wall_align.py` and MkECTL at the same time (finish A before C).

---

## 1. What you need

**Hardware**
- CalibratorV2 rig (3-axis Keigan motors: slide / pan / tilt, IR light, ILT-Pico USB sensor)
- A large flat wall
- A distance meter (tape measure or laser distance meter) — for the offset calibration in Step B

**Software / data** (see [[pyiltrs2-env-split]])
- **MkECTL Python environment** (a venv with `PyQt5` / `qtutils` / `matplotlib` /
  `timeout_decorator` / `pyserial`). Install the point-cloud engine into it:
  ```bash
  pip install ./pyiltrs2-0.1.0-py3-none-any.whl
  ```
  pyusb is an optional dependency of pyiltrs2, so for live USB (`--input usb`)
  install it via the extra instead of a separate install:
  ```bash
  pip install "./pyiltrs2-0.1.0-py3-none-any.whl[usb]"   # [usb] is the extra name (per the whl)
  ```
- Sensor calibration data: an `out/` directory containing `trajectory_data.bin`.
  Example: `~/iltpico/pc_calibration/calib/ILT001/209/out`. **If not yet generated, create it in Chapter 4.**
- The location of `reconstruct.py`. Example: `~/iltpico/pc_reconstruction/reconstruct.py`

---

## 2. Physical setup

1. Mount the ILT-Pico sensor on the rig.
2. Place the rig facing the wall, aligning so the **slider travel direction is perpendicular to the wall**.
3. Confirm the wall fills the sensor FOV at both the shortest (200 mm, below) and
   longest (1000 mm) distance.

---

## 3. Software setup (first time only)

The `movslide` / `exec` commands and the script for this procedure live on the
**`feat/iltpico-eval` branch** of the MkECTL repository. Check out that branch first.

```bash
cd <MkECTL>
git checkout feat/iltpico-eval
```

1. Activate the MkECTL environment (e.g. `source venv/bin/activate`).
2. Confirm the wheel above and `pyusb` are installed.
3. Confirm the `--calib-dir` path.
4. Open `script/slider_sweep_pointcloud.txt` and verify the following match your
   environment (no spaces in paths):
   - the absolute path to `reconstruct.py`
   - the `--calib-dir` path
   - the leading `python3` (if pyusb/iltrecon live in a separate venv, replace it
     with that interpreter's absolute path)

---

## 4. Prepare the calibration data (first time / per sensor model)

Both `wall_align.py` and `reconstruct.py` require the sensor calibration data
(`trajectory_data.bin` etc. inside an `out/` directory). If you don't have it
yet, generate it in this chapter. **Once created it can be reused for the same
sensor model**, so if `out/` already exists, skip this chapter and go to Step A.

Generation has two stages:

1. **Create the near / far images** (synthetic DOE dot-pattern images) — `make_doe_image.py`
2. **Generate the calibration data from those two images** — `pc_calibration` (`calibrate.py`)

> Both run in a **Python virtual environment where mkestudio works** (one with
> `pymkeds` installed). The `pyiltpicocalib` (`calibrate.py`) wheel can be
> installed into this same mkestudio venv, so there is no need for a separate
> venv. Keep it separate from the MkECTL environment.

### 4-1. Generate the near / far images

`make_doe_image.py` renders the DOE dot pattern of an mkecc session (`.msf`) onto
a billboard placed at a given distance and saves it as a PNG.

**Run it in a Python virtual environment where mkestudio works** (one that can
import `pymkeds`).

Example generating two images, near=190 mm and far=715 mm:

```bash
# activate the mkestudio venv first
# near: 190mm
python make_doe_image.py <session.msf> -z 190 -o MkeccCamera0_000_slide=190.png

# far: 715mm
python make_doe_image.py <session.msf> -z 715 -o MkeccCamera0_001_slide=715.png
```

- `<session.msf>` is the mkecc session file for the target sensor.
- `-z` is the billboard distance [mm], `-o` is the output PNG path.
- The file names are referenced by `config.json` (4-3), so a name that encodes
  the distance is easier to manage (following the example: `..._slide=190.png` /
  `..._slide=715.png`).

### 4-2. Set up the pc_calibration tool (install the wheel into the mkestudio venv)

The calibration-data generator is in `tools/pc_calibration` on the
`feat/pc_calibration` branch of the `usb-rp2040-spi` repository. Build and install
the wheel into the **same mkestudio venv as 4-1** (no dedicated venv needed).

```bash
# with the mkestudio venv activated
cd <usb-rp2040-spi>/tools/pc_calibration   # feat/pc_calibration branch

# build and install the wheel
pip install build
python -m build --wheel            # -> dist/pyiltpicocalib-<version>-py3-none-any.whl
pip install dist/pyiltpicocalib-*.whl
```

After installation the `pyiltpicocalib` console command is available (or run
`python calibrate.py` directly from the source tree).

> To just run from source you can skip the wheel and use
> `pip install -r requirements.txt` (numpy / scipy / Pillow). Building the wheel
> is recommended for distribution / reproducibility.

### 4-3. Write config.json

Specify the two images from 4-1 and their distances in JSON. Use the tool's
`sample_config.json` as a template and `calib/ILT001/064/config.json` as a real
example.

The first four fields are the ones you replace in this procedure:

```json
{
  "near_image": "MkeccCamera0_000_slide=190.png",
  "far_image":  "MkeccCamera0_001_slide=715.png",
  "z_near": 190.0,
  "z_far":  715.0,

  "camera":    { "...": "values from sample_config.json (sensor-model build-time constants)" },
  "lens":      { "...": "lens coefficients" },
  "projector": { "...": "projector origin" },
  "meta":      { "...": "h_total / exposure / gain / laser, etc." }
}
```

- **`near_image` / `far_image`**: paths to the PNGs generated in 4-1 (relative to
  `config.json` or absolute).
- **`z_near` / `z_far`**: the distance [mm] at which each image was generated.
  **Match the `-z` values from 4-1** (190.0 / 715.0 in this example).
- The `camera` / `lens` / `projector` / `meta` blocks are the per-model constants,
  lens coefficients and capture metadata. Fill them in for the target sensor using
  `sample_config.json` and the existing `calib/ILT001/064/config.json` as
  templates (check with the calibration owner here).

### 4-4. Generate the calibration data (`out/`)

Run `calibrate.py` with config.json as input. Use `-o` to specify the output directory.

```bash
# with the mkestudio venv activated
cd <usb-rp2040-spi>/tools/pc_calibration   # feat/pc_calibration branch

python calibrate.py config.json -o out
#   or with the console command after installing the wheel:
# pyiltpicocalib config.json -o out
```

- On success, `out/` will contain `trajectory_data.bin` (+ related files).
- Metrics such as reprojection error are printed during the run. If they are
  extremely large, review the images / config.
- Pass the **absolute path** of this `out/` to `--calib-dir` in the following
  steps (e.g. `<usb-rp2040-spi>/tools/pc_calibration/out`).

> Once `out/` is ready, proceed to Step A. The following commands run in the
> **MkECTL environment** (not the mkestudio venv).

---

## 5. Step A — Make the sensor face the wall

Drive pan / tilt with `wall_align.py` to make the sensor optical axis
perpendicular to the wall. **The slider is not moved.** See `README_wall_align.md`
for details.

### A-1. Verify the signs first (mandatory on real hardware)

`--pan-sign` / `--tilt-sign` depend on the mounting and cannot be determined on
paper. In manual mode, first confirm that "one step reduces the error".

```bash
python3 wall_align.py --manual --calib-dir ~/iltpico/pc_calibration/calib/ILT001/209/out/
```

The defaults for `CalibratorV2_REV` are `--pan-sign -1 / --tilt-sign +1`. If an
axis makes the error grow, flip that sign and re-check.

### A-2. Auto-align

```bash
python3 wall_align.py --auto \
    --calib-dir ~/iltpico/pc_calibration/calib/ILT001/209/out/ \
    --frame 40 --threshold 0.3
```

- Converged when the report's **`total tilt vs wall`** drops below `--threshold` (0.3°).
- If it stops with `DIVERGING` / does not converge, see the troubleshooting in
  `README_wall_align.md` (increase `--frames`, raise `--threshold`, lower `--gain`).
- Once converged, **quit `wall_align.py`** (ending the process releases the motors).

> The faced pan / tilt pose is preserved even after `Initialize` in MkECTL
> (`Initialize` does not home) [[keiganrobot-axis-and-init]]. From here, **do not
> touch pan / tilt** (move only the slider).

---

## 6. Step B — Determine the mounting offset and apply it to the script

The sensor mounting position is offset by a constant amount from the slider's z
command. Without correcting this, the "commanded distance" and the "true
sensor-to-wall distance" disagree and accuracy is biased systematically.
[[slider-sensor-mount-offset]]

### B-1. Find the offset from a single-point measurement

1. With MkECTL (started in Step C) or `wall_align.py` running in any state, put
   the slider at some command value `z0` (e.g. 500).
2. Measure the **true distance `D0`** from the sensor to the wall with the distance meter.
3. Offset = `z0 − D0` (additive-offset assumption).
   - Example: command 500 but measured 615 mm → offset = `500 − 615 = −115`.

### B-2. Apply it to the script

Update the `offset` line at the top of `script/slider_sweep_pointcloud.txt`.
**Arguments must be comma-separated** (space-separated values get concatenated
and the digits get mangled) [[dsl-args-comma-separated]].

```text
offset -115, 0, 0
```

With this, the `movslide 200` … `movslide 1000` arguments represent the "true
sensor-to-wall distance", and the output folder names `dist_0200` … `dist_1000`
become correct ground-truth labels.

> **Note on the slider origin**: the offset value depends on "where slide=0 was
> taken". Always measure from the same machineFile / origin reference, and
> re-calibrate the offset if the mounting or rig changes. The physical position
> shifts to `true distance + offset`, so also confirm it stays within the travel
> range (roughly 0–1000 mm) (e.g. with offset −115, physical 85–885 mm).

---

## 7. Step C — Run the slider sweep (MkECTL)

Because `reconstruct.py` occupies the USB sensor, **do not connect the sensor in
MkECTL** (connect to the robot only).

1. Launch MkECTL:
   ```bash
   python3 MkECTL.py
   ```
2. **Select a machineFile** (e.g. `machineFiles/CalibratorV2_REV.json`) and press
   the **`connect` button** to connect to the robot. pan / tilt stay in the Step A
   pose (connecting does not move them to the origin).
3. **Do not open the sensor window / do not connect the sensor** (to avoid USB contention).
4. **`Select Script button`** → choose `script/slider_sweep_pointcloud.txt`.
5. **`Execute Script button`** to run from the top. Progress appears in the
   `Progress` window.
   - At each distance: `movslide` (slider only) → settle → `exec` runs
     `reconstruct.py`, which writes that distance's PLY frames.
   - To stop midway, use the `Progress` window's **`Stop button`**.
6. Done when all 9 locations (200–1000 mm, 100 mm steps) finish.

> **It is recommended to test with one location first.** Try a copy of the script
> with a single block (`movslide 200` + the following `exec`), confirm the PLY is
> produced, then run all 9 locations.

### Output data layout

```
data/sweep/
  dist_0200/ frame0000.ply frame0001.ply ... frame0099.ply (+ depth npy)
  dist_0300/ ...
  ...
  dist_1000/ ...
```

- PLY coordinates are in **mm**. Folder name = true distance label (offset-corrected).
- 100 frames per distance (`--max-frames 100` / `--frame all`). All frames are
  needed for precision; at N=100 the relative uncertainty of the std is about 7%
  (≈ `1/sqrt(2(N-1))`). The more frames, the more stable.

---

## 8. Step D — Analysis (compute accuracy / precision)

The `analyze-sweep` tool computes per-distance **Accuracy / Precision** from the
PLYs in each `dist_XXXX` folder and outputs a console table plus a PNG plot
(`accuracy_precision_plot.png`). The **trailing 4 digits** of the folder name
`dist_XXXX` are treated as the **Ground Truth (mm)**.

### 8-1. Installation

Build the wheel from the `analyze-sweep/` directory in this repository.

```bash
cd analyze-sweep
pip install build
python -m build --wheel    # -> dist/analyze_sweep-1.0.0-py3-none-any.whl
```

Install analyze_sweep into any Python environment (the MkECTL environment is fine).

```bash
pip install dist/analyze_sweep-1.0.0-py3-none-any.whl
```

The dependencies (numpy / matplotlib / plyfile) install automatically. To use
open3d for PLY loading, `pip install "analyze-sweep[open3d]"` (it works with
plyfile alone if open3d is absent).

### 8-2. Run

Run with the sweep output (`data/sweep/dist_XXXX`) as input.

```bash
# analyze data/sweep and write accuracy_precision_plot.png
analyze-sweep -s data/sweep -o accuracy_precision_plot.png

# with defaults (analyze ./sweep, output ./accuracy_precision_plot.png) no args needed
# analyze-sweep
# can also be run as a module: python -m analyze_sweep --help
```

| Option | Default | Description |
|---|---|---|
| `-s, --sweep-dir` | `./sweep` | directory containing `dist_XXXX` |
| `-o, --output` | `./accuracy_precision_plot.png` | output PNG path |
| `-t, --threshold` | `50` | outlier filter threshold [mm] (isolate the wall as measured-Z median ± this value) |

### 8-3. Metric definitions and how to read them

- **Accuracy** = (mean Z after filtering) − (Ground Truth). Positive = biased far, negative = biased near.
- **Accuracy (%)** = Accuracy / Ground Truth × 100.
- **Precision** = standard deviation of Z after filtering (spread; smaller is more
  stable; typically grows with distance).

The outlier filter keeps points within "measured-Z median ± `--threshold`" as the
wall. Because the real data has a systematic offset relative to the Ground Truth,
the wall is isolated around the median rather than around GT, and that offset
itself is reported as Accuracy.

In addition to the console table, a distance vs Accuracy / Precision plot is
written to `accuracy_precision_plot.png`.

---

## 9. Interpreting the results and pass/fail

- **A roughly constant bias in accuracy** → possibly residual from the offset
  calibration (Step B). If the deviation is similar at all distances, fine-tune
  the offset and re-evaluate. A deviation that grows proportionally with distance
  suggests a scale error (sensor unit variation or calibration).
- **Precision growing with distance** is a general ToF / triangulation trend.
  Compare against the spec value.
- **Precision large at every distance / values unstable** → possibly insufficient
  facing or a non-flat wall. Redo Step A. If needed, review `--threshold` to check
  the wall isolation.
- Look not only at a single distance but at the trend in
  `accuracy_precision_plot.png` (distance vs accuracy / precision).

---

## 10. Troubleshooting

| Symptom | Action |
| --- | --- |
| `wall_align` won't converge / `DIVERGING` | See `README_wall_align.md` (`--frames`↑ `--threshold`↑ `--gain`↓, check signs) |
| Script fails outside the slider travel range | Check the Step B offset format (comma-separated) and the origin [[dsl-args-comma-separated]] |
| `exec` fails to run `reconstruct.py` | Check the paths / `--calib-dir` / `python3` in the script. Make sure the sensor window isn't holding the USB |
| PLY empty / few valid frames | Is the wall filling the FOV, laser on, distance not too near/far |
| Cannot connect to the motors | Are `wall_align` and MkECTL running at the same time (port contention)? Quit one |

---

## Appendix: Execution checklist

- [ ] Wall flat / large / fills the FOV. Slider axis perpendicular to the wall.
- [ ] pyiltrs2 wheel + pyusb installed in the MkECTL environment. `--calib-dir` confirmed.
- [ ] `wall_align.py --auto` converged below threshold for `total tilt`. Quit it.
- [ ] Offset determined from a single-point measurement and applied to the script **comma-separated**.
- [ ] Verified the reconstruct.py path / `--calib-dir` / `python3` in the script.
- [ ] MkECTL: select machineFile → `connect` (do not connect the sensor).
- [ ] Test one location first → run all 9 with `Execute Script`.
- [ ] Computed accuracy / precision with `analyze-sweep` and compared to the spec.

---

## Related documents

- `README_wall_align.md` — details of the alignment tool
- `README.md` — MkECTL GUI and script grammar
- `script/slider_sweep_pointcloud.txt` — the sweep script itself
