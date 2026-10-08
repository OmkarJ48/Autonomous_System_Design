# Autonomous_System_Design

**ME7027 – Design of Autonomous Systems**
Development and Comparison of Autonomous Navigation Systems using Fuzzy Logic, Computer Vision, and Deep Learning.

School of Engineering, Department of Mechanical Engineering.
Assessment set by Dr Olga Duran and Esfandiar Khaleghi.

This repository holds the coursework for building and comparing autonomous
navigation pipelines on two platforms: the **LEGO MINDSTORMS EV3** robot and the
**Quanser QCar** (physical and virtual). It covers sensor characterisation and
fusion, classical computer vision, deep-learning object detection, fuzzy-logic
and PD navigation control, and the mechanical design of a custom camera mount.

---

## Documentation

Full reports live in [`docs/`](docs/):

| Document | Description |
| --- | --- |
| [`ME7027_Design_of_Autonomous_Systems_Group_3_Report.pdf`](docs/ME7027_Design_of_Autonomous_Systems_Group_3_Report.pdf) | Group 3 technical report (Parts 1–5 plus appendices): platform description, sensor characterisation, sensor fusion, computer vision, deep learning, navigation control, camera-mount design, CAD models and simulation results. |
| [`K2441768_Omkar_Anant_Joshi_Individual_Conclusion.docx`](docs/K2441768_Omkar_Anant_Joshi_Individual_Conclusion.docx) | Individual submission (Part 6): evaluation, discussion and comparison — LEGO EV3 vs QCar, transfer learning vs custom CNN, classical CV vs deep learning, and navigation-strategy assessment. |

## Group members

| K Number | Name |
| --- | --- |
| K2445563 | Joshva Jonathan Joseph |
| K2447273 | Rahul R Menon |
| K2441768 | Omkar Joshi |
| K2454461 | Sarath Kumar Komathukattil |

---

## Platforms

### LEGO EV3

A compact, modular educational platform: a programmable EV3 brick, onboard
sensors and motorised actuators.

| Sensor | Type | Key specifications |
| --- | --- | --- |
| Ultrasonic | Distance | Range 3–250 cm, accuracy ±1 cm |
| Touch | Binary contact | Touched / bumped / released, debounced |
| Gyro | Orientation | Resolution ±1°, range ±440°/s, drift up to 3°/min |
| Colour | Reflectance / colour | 7 colours, reflective and ambient light modes |
| Logitech C270 webcam | Vision | 640 × 480 |

Actuators: large DC motors with integrated encoders for the drive wheels.

### Quanser QCar

A research-grade autonomous ground vehicle for perception and AI-based control.

| Sensor | Type | Key specifications |
| --- | --- | --- |
| LiDAR | Laser range scanner | 360°, up to 12 m, 0.5° resolution, 8000 samples/s |
| CSI / RGB cameras | Vision | 720p–1080p, 30–60 fps, ~160° FOV each |
| Intel RealSense D435 | RGB-D | Depth 0.2–10 m, 30 fps |
| IMU | Orientation + motion | 9-DOF, ±1° orientation, ±0.05 m/s² |
| Wheel encoders | Rotary position | ~2048 counts/rev |

Actuators: 4 × brushless DC drive motors with encoders. Onboard compute is an
NVIDIA Jetson TX2 / Intel i7 NUC class processor, programmable through
MATLAB/Simulink, Python and ROS, with real-time loops via QUARC or the QCar
Python SDK.

---

## Project parts

### Part 1 — Sensor fusion and actuator characterisation

Sensors on both platforms were characterised for accuracy, precision,
resolution and response time under realistic operating conditions.

Selected EV3 results:

| Sensor | Finding |
| --- | --- |
| Ultrasonic | +0.3 cm error at 10 cm rising to +2.1 cm at 30 cm; response 6–8 ms |
| Colour | 100 % on white/red, 50 % on green, 0 % on blue/black surfaces |
| Gyro | 2.00° resolution, 113.58 ms sampling interval, negligible drift over 30 s |
| Motors/encoders | Mean 620.20° per trial, std dev 13.44°, 1.00° resolution |
| Webcam | Average latency 1.34–1.47 ms across 45–65 cm |

Selected QCar results:

| Sensor | Accuracy | Precision | Resolution | Response |
| --- | --- | --- | --- | --- |
| LiDAR | ±3 cm | ±0.008 m | 0.18°–0.9° | ~95–97 ms |
| CSI cameras | Clarity via variance of Laplacian | — | 160° FOV | ~43–55 ms |
| RealSense D435 | ±2 cm | ±0.007 m | ~1–5 mm | Real-time stream |

**Fusion.** A Kalman filter fuses the front ultrasonic sensor (reliable at
10–30 cm) with the rear-facing webcam (usable at 45–65 cm). The fused estimate
holds better than ±1.0 cm across the full 10–65 cm range, suppressing
ultrasonic spikes and correcting the webcam's positional bias.

### Part 2 — Computer vision

* **Stop-sign detection** — red colour mask, morphological cleanup
  (`imopen`/`imclose`), Canny edge detection on the masked greyscale, blob
  filtering by area (800–150 000 px) and solidity (> 0.65), polygon
  approximation with `reducepoly` accepting 7–10 sides, octagon uniformity
  checks on side lengths and interior angles, red-dominance validation, and a
  0–100 % confidence score thresholded at 80 %.
* **Traffic-light classification** — dual HSV + RGB masks for red and green,
  combined with a logical OR and cleaned morphologically (noise removal, hole
  filling, blobs > 150 px), then verified by shape and position. Yellow was
  deliberately excluded to avoid false positives.
* **Lane detection and steering (EV3)** — HSV thresholding for yellow lane
  markers (H 15°–45°, S 0.15–1.0, V 0.6–1.0) inside a bottom-of-frame ROI,
  centroid estimation, normalised error against the image centre, and a PD
  controller (`Kp = 0.3`, `Kd = 0.1`) driving the left (port C) and right
  (port B) motors. The robot stops when no lane is found.

### Part 3 — Deep-learning object detection

Two dataset variants were assembled from Kaggle (~5000 images), Roboflow
(~3000) and in-lab capture (~4000), resized to 224 × 224 × 3, sorted into
class folders from `.txt` annotations, and split 70/15/15 stratified per class:

* **14-class** — regulatory, warning and directional signs plus red/green
  traffic-light states.
* **5-class core** — RedT, GreenT, Stop, Adjusted60 (speed limit 60), Other.

| Metric | GoogleNet 5-class | GoogleNet 14-class | Custom CNN 5-class | Custom CNN 14-class |
| --- | --- | --- | --- | --- |
| Test accuracy | 100 % | 96.25 % | 94.33 % | 90.61 % |
| Precision (avg) | 1.00 | 0.95 | 0.95 | 0.97 |
| Recall (avg) | 1.00 | 0.96 | 0.95 | 0.97 |
| F1 (avg) | 1.00 | 0.94 | 0.95 | 0.97 |
| Training time | Lower | Higher | Higher | Higher |

* **Transfer learning (GoogleNet)** — final classification layer replaced;
  learning rate 0.0001, 20 epochs, batch size 24, GPU training.
* **Custom CNN** — 5 convolutional blocks (Conv2D → BatchNorm → ReLU →
  MaxPool) then Flatten → FC → Softmax; Adam, 8 epochs, mini-batch 32, L2
  1e-4, learning rate 0.001.
* **Augmentation** — random rotation, scaling, horizontal flip and random
  translation applied to the GoogleNet 5-class model. Result: 99.37 % test
  accuracy, slightly *below* the non-augmented 100 %.
* **Hyperparameter tuning** — learning rate {0.0001, 0.001, 0.01} × epochs
  {10, 15, 20} × mini-batch {12, 24, 48} swept in MATLAB Experiment Manager.
  Best trial: lr 0.0001, 20 epochs, mini-batch 12 → 99.37 % validation
  accuracy, training loss 5.46e-7.

### Part 4 — Navigation control strategies

* **Fuzzy logic controller** — inputs are obstacle distance (NEAR, NOTFAR,
  FAR), lane detection status (YES, NO) and traffic-light state (RED, GREEN);
  output is motor speed (STOP, SLOWSPEED, FULLSPEED) over 12 rules, simulated
  in MATLAB/Simulink.
* **Real-time control loop** — object detection (RedT/GreenT → stop/go) → lane
  detection (steering) → obstacle avoidance (emergency stop under 40 cm) →
  fuzzy inference setting base speed.
* Validated on the EV3 over USB, with fallback simulation support and a
  Quanser Virtual QCar simulation.

### Part 5 — Mechanical design of a camera mount

A three-part SolidWorks assembly — a LEGO-compatible base, a Logitech C270
holder, and an adjustable Intel RealSense D435 holder using a circular keyhole
and pin.

| Specification | Target / constraint |
| --- | --- |
| Dimensions | ≤ 130 mm (H) × 80 mm (W) × 100 mm (D) |
| Material | PLA (or ABS), FDM printable |
| Weight | ≤ 150 g including camera |
| Camera compatibility | Logitech C270 and Intel RealSense D435 |
| Mounting | Snap-fit / LEGO-compatible, assembly ≤ 2 min, no tools |
| Field of view | No obstruction within ±40° horizontal and vertical |
| Adjustability | ±30° tilt (webcam), up to 3 cm height (D435) |
| Environment | Indoor, 10–25 °C, low humidity, low vibration |

### Part 6 — Individual evaluation

See [`docs/K2441768_Omkar_Anant_Joshi_Individual_Conclusion.docx`](docs/K2441768_Omkar_Anant_Joshi_Individual_Conclusion.docx)
for the capability comparison, model comparison, CV vs deep learning
evaluation, and the assessment of navigation strategies.

---

## Repository layout

```
.
├── .vscode/                     VS Code workspace configuration
│   ├── extensions.json          Recommended extensions
│   ├── launch.json              Debug configurations for the scripts below
│   ├── settings.json            Interpreter, linting, MATLAB and search setup
│   └── tasks.json               Venv creation, dependency install, env check
├── docs/                        Reports and supporting documentation
│   ├── ME7027_..._Group_3_Report.pdf
│   └── K2441768_..._Individual_Conclusion.docx
├── scripts/
│   ├── check_environment.py     Verifies interpreter, packages and Quanser SDK
│   └── qcar/
│       ├── qlabs_virtual_qcar.py  Spawn and drive a QCar in Interactive Labs
│       └── qcar_sensors.py        LiDAR / CSI / RealSense / IMU read loop
├── .gitignore
├── README.md
└── requirements.txt             Python dependencies
```

MATLAB sources, datasets, trained models and result videos are added under
their own directories as the work is committed; large binaries (datasets,
`.mat` checkpoints, recorded `.avi`/`.mp4` results) are excluded by
`.gitignore` and should be shared out of band.

---

## Development environment

Two environments are required to complete the project: **Visual Studio Code**
for editing, running and debugging, and the **Quanser QCar** software stack
for the vehicle work. MATLAB/Simulink remains the primary toolchain for the
coursework itself.

### 1. Visual Studio Code

Install [Visual Studio Code](https://code.visualstudio.com/), then open this
repository as a folder. VS Code reads the checked-in `.vscode/` configuration
and offers to install the recommended extensions on first open.

Extensions (declared in [`.vscode/extensions.json`](.vscode/extensions.json)):

| Extension | Purpose |
| --- | --- |
| `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.debugpy` | Python editing, IntelliSense and debugging |
| `charliermarsh.ruff` | Python linting and formatting |
| `ms-toolsai.jupyter` | Notebooks for sensor-data analysis |
| `MathWorks.language-matlab` | MATLAB editing, running and debugging inside VS Code |
| `mechatroner.rainbow-csv` | Reading logged sensor CSVs |
| `slevesque.vscode-3dviewer` | Previewing the camera-mount STL/OBJ meshes |
| `yzhang.markdown-all-in-one`, `DavidAnson.vscode-markdownlint` | Documentation |
| `eamodio.gitlens`, `streetsidesoftware.code-spell-checker` | General |

Set up the Python environment:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/check_environment.py
```

The same three steps are available from the Command Palette via
**Tasks: Run Task** → *Create virtual environment* / *Install Python
dependencies* / *Check environment*, defined in
[`.vscode/tasks.json`](.vscode/tasks.json).

`.vscode/settings.json` points the interpreter at `.venv`, adds `scripts/` to
the analysis path, and downgrades unresolved-import errors to warnings so the
Quanser imports stay readable on a machine without the QCar software. The
`MathWorks.language-matlab` extension additionally needs `matlab.installPath`
set to your local MATLAB root — it is left unset in the committed settings
because the path is machine-specific:

```jsonc
// Windows
"matlab.installPath": "C:\\Program Files\\MATLAB\\R2023b"
// Linux
"matlab.installPath": "/usr/local/MATLAB/R2023b"
```

Debug entry points are pre-wired in
[`.vscode/launch.json`](.vscode/launch.json): *Check environment*,
*QCar: virtual (QLabs) drive demo*, *QCar: sensor read loop*, and
*Python: current file*.

### 2. Quanser QCar environment

The QCar work needs the Quanser software stack. **None of it is on PyPI** —
it is licensed and distributed by Quanser with the vehicle and with Quanser
Interactive Labs, so `pip install` will not provide it.

| Component | Role |
| --- | --- |
| **Quanser Interactive Labs (QLabs)** | Virtual QCar and simulated environments — the Virtual QCar Simulation in Part 4 |
| **QUARC** | Real-time control, and the Simulink code-generation target for the QCar |
| **Quanser Python SDK** — `quanser` (HIL/communications), `pal` (physical and virtual QCar products), `qvl` (Interactive Labs) | Python access to the vehicle and the simulator |
| **QCar research studio resources** | Reference examples, calibration tools and workspaces |

Setup:

1. Install Quanser Interactive Labs and QUARC from the Quanser distribution
   supplied with the module, and activate your licence.
2. Make the Quanser Python packages importable — either run the scripts with
   the Python interpreter that ships with Quanser, or add the Quanser
   `python` directory to `PYTHONPATH`.
3. Confirm the SDK is visible:

   ```bash
   python scripts/check_environment.py --require-quanser
   ```

   This exits non-zero and prints what is missing if `quanser`, `pal` or
   `qvl` cannot be found.
4. For the physical QCar, connect over the vehicle's Wi-Fi and run the
   scripts on the onboard computer (Jetson TX2 / Intel i7 NUC class).

Reference documentation ships with the installation, and the product page is
at <https://www.quanser.com/products/qcar/>. The QCar hardware manual cited
in the group report is `Qcar_user_manual_system_hardware.pdf`.

### 3. MATLAB / Simulink (primary coursework toolchain)

MATLAB R2022b or later with:

* Image Processing Toolbox
* Computer Vision Toolbox
* Deep Learning Toolbox (plus the GoogleNet pretrained network support package)
* Fuzzy Logic Toolbox
* Simulink
* MATLAB Support Package for LEGO MINDSTORMS EV3 Hardware
* Experiment Manager (for the hyperparameter sweeps in Part 3)
* Parallel Computing Toolbox (for GPU training)

MATLAB files can be edited and run from VS Code through the MathWorks
extension, but Simulink models (`.slx`) and live scripts (`.mlx`) must be
opened in MATLAB itself.

### 4. Other software

* SolidWorks (camera mount CAD)
* An FDM slicer and 3D printer for PLA prototypes

---

## Scripts

| Script | What it does | Runs without the Quanser SDK? |
| --- | --- | --- |
| [`scripts/check_environment.py`](scripts/check_environment.py) | Reports the interpreter, the required packages and the Quanser SDK; `--require-quanser` makes a missing SDK a failure | Yes — stdlib only |
| [`scripts/qcar/qlabs_virtual_qcar.py`](scripts/qcar/qlabs_virtual_qcar.py) | Connects to QLabs, spawns a QCar, drives an open-loop manoeuvre, grabs a front RGB frame | No — exits 2 with setup guidance |
| [`scripts/qcar/qcar_sensors.py`](scripts/qcar/qcar_sensors.py) | Read loop over LiDAR, CSI cameras, RealSense depth and the IMU, printing a running summary | No — exits 2 with setup guidance |

```bash
python scripts/check_environment.py
python scripts/qcar/qlabs_virtual_qcar.py --host localhost --duration 8
python scripts/qcar/qcar_sensors.py --duration 30 --no-realsense
```

Every script supports `--help`.

> **The two `scripts/qcar/` scripts are scaffolds, not verified coursework
> code.** They follow the documented Quanser Python API, but that surface
> changes between SDK releases (`QLabsQCar` vs `QLabsQCar2`, PAL constructor
> arguments and attribute names). They have been syntax- and CLI-checked and
> their missing-SDK path is tested, but they have **not** been run against a
> real QCar or a live QLabs instance. Check the calls against the Quanser
> Python API documentation for your installed version before relying on them.

---

## References

**Platforms and SDK**

* Quanser QCar product page — <https://www.quanser.com/products/qcar/>
* Quanser QCar hardware manual — `Qcar_user_manual_system_hardware.pdf`
  (ships with the QCar)
* Quanser Interactive Labs and QUARC documentation — installed with the
  Quanser distribution
* LEGO MINDSTORMS EV3 hardware poster and sensor pages — cited in full in the
  References section of the group report

**Tooling**

* Visual Studio Code — <https://code.visualstudio.com/>
* MATLAB extension for VS Code — <https://marketplace.visualstudio.com/items?itemName=MathWorks.language-matlab>
* MATLAB Support Package for LEGO MINDSTORMS EV3 Hardware — MathWorks
* MathWorks, *Creating a colour mask for an image in HSV* — MATLAB Central
* MathWorks, *Image Augmentation Using Image Processing Toolbox*

**Datasets**

* Kaggle — traffic-light and road-sign corpus (~5000 images)
* Roboflow — annotated road-sign dataset (~3000 images)
* In-lab capture — ~4000 images under varied angles and lighting

**CAD**

* Logitech C270 webcam model — GrabCAD
* Intel RealSense D435 model — GrabCAD

Full citations with access dates are in the References section of the group
report.

---

## Notes

* Reused or adapted code is cited in the group report; sensor test scripts were
  written or adapted from the LEGO EV3 MATLAB support packages.
* Raw sensor data, plots, CAD models, constrained models and Quanser virtual
  simulation captures are in Appendices 1–4 of the group report.
