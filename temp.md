Thanks for taking this on. Here's your technical exercise. It's designed to be built end-to-end, fully offline, and packaged for review.
What to build (48 hours):
•	Cross-platform desktop app: Linux first, plus Windows.
•	Model switcher: user can choose MediaPipe (for hands/gesture or holistic) or MoveNet (Lightning/Thunder).
•	Two modes:
1.	Freestyle: live pose with joint-angle overlays + basic gait metrics.
2.	Guided: app shows a target activity; compute joint angles, segment reps, score accuracy, and report symmetry.
•	Exports: raw keypoints, angles, gait, and session summary to CSV/JSON. Runs entirely offline.
Packaging (must):
•	Linux: one AppImage that runs on Fedora and Ubuntu without extra installs.
•	Windows: standalone .exe installer or portable .exe.


Code quality & docs (expected):
•	Clear structure, clean naming, and comments.
•	Standards:
o	Python: PEP8/PEP257, black, isort, flake8, mypy.
o	C++: Google Style, clang-format/clang-tidy.
o	TS/Electron: strict TS + ESLint + Prettier.
•	Docs: README (build/run/package), ARCHITECTURE.md, ALGORITHMS.md, API docs, VALIDATION_NOTES.md.
•	Tests: unit tests for angle math, rep segmentation, symmetry, and a deterministic CLI check on a sample video.
Checklist (we'll verify):
•	Fully offline; model files bundled.
•	AppImage works on Fedora and Ubuntu; Windows .exe works on a stock machine.
•	Model switching at runtime.
•	Real-time joint-angle overlays; guided scoring; symmetry index.
•	Gait cadence within ±10% of a manual count.
•	≥20 FPS at 720p on a mid-range CPU.
•	CSV/JSON exports match the spec.
References:
•	Use standard goniometry conventions (Norkin & White; Clarkson; Winter). Targets and angle definitions should be documented in ALGORITHMS.md.



## Objective
Build a **cross‑platform desktop application** (Linux first; Windows/macOS acceptable) that runs **fully offline** and supports **pose estimation** with **two selectable backends**:

1) **MediaPipe** (Hands, Holistic) for hand/gesture and full‑body; 2) **MoveNet** (Lightning/Thunder) for high‑FPS whole‑body.

The app must:
- Capture live video from a local webcam.
- Detect and track body keypoints.
- Compute **joint angles** in real time using the rules below.
- Support two modes:
  - **Mode A – Freestyle:** User moves (jumping, squats, arm raises, etc.). Display live joint angles and **gait parameters** overlay.
  - **Mode B – Guided task:** App shows a target pose/activity. User performs it. App computes joint angles and outputs a **score** per trial.
- Save raw detections, angles, gait metrics, and session summary to **CSV and JSON**.

> Hard constraints: Works offline; deterministic results on repeated runs; stable FPS ≥ 20 on a mid‑range laptop without dGPU.

---

## Tech Stack (pick one and commit)
- **Python** + **React.js** UI + **OpenCV** + **MediaPipe** Python or **TensorFlow Lite** (MoveNet via tflite_runtime). Package via **PyInstaller**.

## Model Selection Rules
- If **hand/gesture** classification is required in a trial, select **MediaPipe Hands/Holistic**.
- Otherwise default to **MoveNet** (Thunder if ≥ 30 FPS achievable; else Lightning).
- User can override backend in a * → Model** dropdown.

---

## Keypoint Map (standardized)
Normalize all model outputs to this canonical 2D list (x, y, visibility) with names:
- **Head/Trunk:** nose, left_eye, right_eye, left_ear, right_ear, neck (derived), left_shoulder, right_shoulder, left_hip, right_hip, mid_hip (derived)
- **Arms:** left_elbow, right_elbow, left_wrist, right_wrist
- **Hands (if MediaPipe Hands active):** left/right: wrist, thumb_cmc, thumb_mcp, thumb_ip, thumb_tip, index_mcp, index_pip, index_dip, index_tip, middle_mcp, middle_pip, middle_dip, middle_tip, ring_mcp, ring_pip, ring_dip, ring_tip, pinky_mcp, pinky_pip, pinky_dip, pinky_tip
- **Legs:** left_knee, right_knee, left_ankle, right_ankle, left_heel, right_heel, left_toe, right_toe
- **Spine (derived):** shoulder_center, hip_center, torso_axis

Compute **neck** as midpoint of both shoulders and nose projection. Compute **shoulder_center** = mid(L/R shoulder); **hip_center** = mid(L/R hip).

---

## Joint Angle Computation (2D, camera plane)
Use vector math with robust handling:

**Angle at joint J formed by segments (A→J) and (B→J):**

- v1 = A − J, v2 = B − J
- angle_rad = arccos( clamp( dot(v1, v2) / (||v1||·||v2||), −1, 1) )
- angle_deg = angle_rad · 180/π

**Numerical safeguards:**
- If either segment norm < ε (ε = 1e−6 in normalized image coords), mark angle as **NaN** and carry forward last valid value (exponential smoothing α = 0.25).
- Apply a **1‑Euro filter** or EMA per angle to suppress jitter.
- For occluded keypoints (visibility < 0.5), linearly interpolate up to 500 ms using last velocity; beyond that, mark **missing**.

**Angles to compute (bilateral):**
- **Neck flex/ext:** angle between torso_axis and vector neck→nose.
- **Shoulder abduction:** ∠(elbow, shoulder, hip_center).
- **Shoulder flexion:** ∠(elbow, shoulder, shoulder→hip_center rotated 90° forward). Approx via ∠ with vertical if camera is sagittal.
- **Elbow flexion:** ∠(wrist, elbow, shoulder).
- **Hip flexion:** ∠(knee, hip, shoulder_center).
- **Knee flexion:** ∠(ankle, knee, hip).
- **Ankle dorsiflexion/plantarflexion:** ∠(toe, ankle, knee) relative to shank. If toes absent use heel/ankle.
- **Trunk lateral tilt:** angle between torso_axis and image vertical.

> If 3D is available (MediaPipe with z), compute in 3D first and project to anatomical plane if camera pose is known. Otherwise stay in 2D with camera‑plane assumption.

---

## Activity Library (minimum set)
1. **Squat** (5 reps): primary angles knees, hips, ankles; depth criterion knee flexion peak.
2. **Arm abduction** (5 reps each side): shoulder abduction peak 90° and 120° targets.
3. **Forward flexion** (5 reps): shoulder flexion to 90°.
4. **Calf raises** (10 reps): ankle plantarflexion.
5. **Jumping jacks** (10 reps): symmetric arm abduction + hip abduction rhythm.

App must allow selecting an activity, show a GIF/PNG guide, countdown, record, and auto‑segment reps by zero‑crossings in angle velocity.

---

## Scoring Logic (per activity)
- **Target bands** per joint:
  - Green: |measured − target| ≤ 5°
  - Amber: ≤ 10°
  - Red: > 10° or missing
- **Repetition score:** mean of joint band scores [Green=1, Amber=0.5, Red=0].
- **Form stability:** std‑dev of target joint angle within the top 20% of ROM window; lower is better. Map to [0..1] with min‑max caps.
- **Final trial score:** 0.7·repetition_mean + 0.3·form_stability.

Include **left–right symmetry index:** SI = 100·|L − R|/(0.5·(L + R) + 1e−6). Penalize SI > 15.

---

## Gait Parameters (single‑camera approximation)
During Mode A when the user walks/runs across the frame:
- **Cadence (steps/min):** count heel‑strike surrogates via local minima in vertical ankle trajectory; convert by timebase.
- **Step time / stance–swing ratio:** time between successive ankle events; stance ≈ period where foot vertical velocity ~ 0 with ankle < 5 px variance.
- **Step length (relative):** pixel distance between successive heel‑strike ankle x at mid‑hip y band. Convert to **relative units** by dividing by **hip width** in pixels as person scale.
- **Stride symmetry:** compare left vs right step time and relative length.
- **Vertical excursion:** amplitude of mid‑hip y in pixels normalized by hip width.

Export these with timestamps. Document that monocular estimate gives **relative** gait metrics unless a scale object or known user height is provided.

---

## UI/UX Requirements
- **Toolbar:** Camera selector • Start/Stop • Mode (Freestyle/Guided) • Model (MediaPipe/MoveNet) • Settings • Export.
- **Overlays:**
  - Skeleton lines; joint markers.
  - Live **angle readouts** for key joints (top overlay list), color‑coded Green/Amber/Red vs targets when in Guided.
  - **Gait strip** at bottom: cadence, step time L/R, SI.
- **Panels:**
  - Left: activity selection and targets; thumbnails/GIFs.
  - Right: live charts (last 10 seconds) for selected angles; scoring after each rep.
- **Session Summary dialog:** trial list, per‑rep scores, symmetry, CSV/JSON export.

Keyboard shortcuts: S=start/stop, G=switch mode, M=switch model, E=export, 1..5=activity quick select.

---

## Data & File Outputs
- **/sessions/{ISO8601}/raw_keypoints.json** – per frame keypoints with visibility and model name.
- **/sessions/{ISO8601}/angles.csv** – t, joint_name, side, angle_deg.
- **/sessions/{ISO8601}/gait.csv** – cadence, step_time_L, step_time_R, rel_step_len_L, rel_step_len_R, SI, timestamps.
- **/sessions/{ISO8601}/summary.json** – activities attempted, scores, system info (OS, CPU, model).

---

## Performance & Quality Gates
- Cold start < 5 s; **FPS ≥ 20** at 720p on i5/Ryzen 5‑class CPU.
- Angle latency < 120 ms end‑to‑end.
- Missing‑data handling without UI flicker.
- Deterministic exports given same input video file.

---

## Testing Checklist (must pass before submission)
1. **Offline mode:** Disconnect internet; app still runs; models are locally bundled.
2. **Cross‑distro Linux test:** AppImage validated on **Fedora (preferred)** and **Ubuntu** VMs/hosts; no missing library errors; no external installs.
3. **Cross‑platform build:** Provide Linux AppImage and Windows .exe; macOS .dmg optional. Build scripts reproducible.
4. **Camera enumeration:** Supports ≥ 2 webcams; handles hot‑unplug; graceful errors.
5. **Model switch:** Toggle MediaPipe/MoveNet at runtime; state preserved.
6. **Hand activity:** With MediaPipe, show wrist/finger angles (if enabled) and stable wrist flexion.
7. **Guided squat:** Correctly segment 5 reps; knee peak > 80° flagged green.
8. **Symmetry index:** Reports SI for arm abduction both sides; penalization visible.
9. **Gait run:** Walk across frame for 10 s; cadence within ±10% of manual count.
10. **Recovery:** Handle occlusion without crash; NaN when needed.
11. **Exports:** CSV/JSON created; schema matches spec; timestamps monotonic.
12. **Performance:** FPS ≥ 20 at 720p on i5/Ryzen‑5 CPU on both Fedora and Ubuntu tests.
13. **Reproducibility:** Same prerecorded video → identical `summary.json` on two runs.
14. **Wayland/X11:** Document and verify Wayland run; provide `QT_QPA_PLATFORM=xcb` fallback if using Qt.
## Code Quality & Documentation Standards
- **Coding standards:**
  - **Python:** PEP 8 + PEP 257 docstrings (numpydoc style). Use `black` (line length 88), `isort`, `flake8`, and `mypy --strict` via **pre-commit** hooks.
  - **C++ (if chosen):** Google C++ Style Guide, `clang-format`, `clang-tidy`, `cpplint`. Prefer RAII, `std::unique_ptr`/`std::shared_ptr`, no raw new/delete in app code.
  - **Electron/TS (if chosen):** TypeScript strict mode, ESLint (Airbnb config), Prettier, `tsc --noImplicitAny`, `vite`/`webpack` production build.
- **Project structure:** `src/`, `app/`, `models/`, `assets/`, `tests/`, `docs/`, `scripts/`, `licenses/`, `sessions/`.
- **Documentation:**
  - `README.md` with quickstart, build, run, packaging, troubleshooting.
  - `ARCHITECTURE.md` (modules, data flow, key classes/functions, error handling, threading model).
  - `ALGORITHMS.md` explaining angle math, filters, gait logic, rep segmentation, scoring.
  - API doc: **Sphinx** (Python) or **Doxygen** (C++), or **TypeDoc** (TS). Output to `docs/site/`.
  - Inline docstrings for all public functions/classes; examples where helpful.
- **Testing:**
  - Unit tests for angle engine (synthetic triangles), rep segmentation, SI computation, gait cadence events.
  - CLI test that processes a sample video and asserts deterministic `summary.json`.
  - Code coverage target ≥ **70%** for logic modules (angles, scoring, segmentation).
- **Static analysis & CI:** Provide a local script `scripts/ci_local.sh` that runs lint, type‑check, tests, and packaging steps in sequence.

---

## Repository & Submission Policy (Private)
- **Private submission only. Do not publish publicly.**
- Deliver a **single ZIP archive of the Git repository** (include the `.git/` folder and history) named `poseapp_<yourname>_<timestamp>.zip`.
- Inside the ZIP: full repo, docs, pre‑built binaries, `third_party_licenses.txt`.
- We will ingest this ZIP into internal **GitLab** for review. No public GitHub links.
- Include a `COMPLIANCE.md` noting third‑party licenses and model sources (MoveNet, MediaPipe) and redistribution terms.

---

## Packaging & Runtime Artifacts
- **Mandatory binaries:**
  - **Linux (required):** deliver a **single self‑contained AppImage** (`PoseApp-x86_64.AppImage`) that runs on **Fedora** (preferred validation), **Ubuntu/Debian**, and other mainstream RPM/DEB distros without extra installs. The AppImage must not rely on distro package managers at runtime.
    - **Target ABI:** x86_64, **glibc ≥ 2.31** (or lower if you can); bundle all non‑system libs. Avoid linking against host‑specific `libstdc++`/Qt plugins.
    - **Bundle list:** Qt/PySide, OpenCV core/videoio/highgui plugins, TFLite runtime, MediaPipe graphs/tasks, FFmpeg loader if used, and any codec/backends required by OpenCV.
    - **Do not** depend on NVIDIA/CUDA. CPU path must work. If you optionally support GPU, auto‑fallback to CPU.
  - **Windows (required):** standalone **.exe** installer or portable `.exe`.
- **Optional (nice‑to‑have):** **macOS .dmg/.app** (x86_64 or universal). Provide unsigned run instructions if not notarized.
- **Offline assets bundling:**
  - All models/graphs reside in `/models` and are packaged inside the binaries. **Zero network calls** at runtime.
  - Provide `models/manifest.json` with filenames, SHA256, source, license. Include `scripts/fetch_models.sh` to refresh models for rebuilds.
- **Local installation & run instructions:**
  - **Linux:** `chmod +x PoseApp-x86_64.AppImage && ./PoseApp-x86_64.AppImage`
    - If Wayland issues occur, document `QT_QPA_PLATFORM=xcb` fallback.
  - **Windows:** run installer; data under `%LOCALAPPDATA%/PoseApp/sessions`.
  - **macOS (if provided):** drag to Applications; right‑click → Open on first run if unsigned.


## Build & Packaging Guidance
- Vendor all model files (**.tflite**, MediaPipe graphs/tasks) into the repo under /models with license notices.
- For Python: pin versions in **pyproject.toml** or **requirements.txt**; use **PyInstaller** one‑file build; include OpenCV plugins.

## References – Goniometry & ROM Norms
Use these to define target angles and measurement conventions in code comments and README:
1. **Norkin CC, White DJ.** *Measurement of Joint Motion: A Guide to Goniometry.* 5th ed. F.A. Davis. Standard text for anatomical landmarks and ROM norms.
2. **Clarkson HM.** *Musculoskeletal Assessment: Joint Range of Motion and Manual Muscle Strength.* 3rd ed. Lippincott Williams & Wilkins.
3. **Cuthbert & Goodheart.** On reliability of goniometric measurements across joints; useful for repeatability notes.
4. **Winter DA.** *Biomechanics and Motor Control of Human Movement.* For gait temporal‑spatial definitions and kinematic conventions.
5. **Kadaba et al.** (1990) on repeatability of kinematics in gait; use for cadence/step event logic justification.

> If in doubt, follow Norkin & White for anatomical axis definitions. Document any deviations.

---

## Angle Logic – Implementation Notes
- Keep everything in **radians internally**; expose degrees in UI/exports.
- Define a **JointSpec** table mapping each angle to its parent keypoints and anatomical plane assumption.
- Centralize math in `angles.py` (or equivalent). Unit‑test with synthetic triangles.
- Smoothing only on display; **persist raw** angles to CSV with an additional column for smoothed.

**Example spec row:**
```
name: knee_flexion_left
points: (ankle_L, knee_L, hip_L)
plane: sagittal (camera-left view assumed)
valid_range_deg: 0..150
thresholds_deg: green<=|target-actual|<=5, amber<=10
```

---

## Risk Notes & Assumptions
- Single front‑facing camera; no camera calibration. Angles approximate anatomical planes; acceptable for prototype.
- Hand angles are illustrative; full hand kinematics not required beyond finger MCP/PIP flexion approximation if time allows.
- Gait metrics are **relative** without scale.

## Acceptance Criteria (pass/fail)
- Runs offline with bundled models.
- Real‑time joint angle overlays and exports as specified.
- Guided scoring with banded thresholds and symmetry penalty.
- Gait CSV present with cadence and step metrics.
- Linux binary delivered; repo builds cleanly; videos demonstrate features.

---

## Nice‑to‑Haves (not required for pass)
- 3D pose fusion when MediaPipe provides z; depth‑aware angles.
- Calibration step to estimate pixel→cm using user height.
- Simple gesture mappings (hand open/closed, pinch) to control UI without mouse.

---

## License & Attribution
- Confirm licenses for MediaPipe and MoveNet before redistribution. Include third‑party notices in **/licenses**
