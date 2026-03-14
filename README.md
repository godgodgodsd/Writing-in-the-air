# Enterprise AI Paint

Enterprise AI Paint is a real-time, camera-driven drawing app that uses hand tracking and gesture recognition to control a painting canvas. It combines MediaPipe Tasks, OpenCV rendering, and a modular drawing engine with gesture-to-action mapping, custom gestures, and export workflows.

## Features
- Real-time hand tracking with MediaPipe Tasks.
- Gesture recognition with configurable gesture-to-action mapping.
- Pinch-based toolbar clicks and continuous size adjustment.
- Brush system with round, square, spray, eraser, and optional ABR stamp brushes.
- Layered canvas with undo/redo per layer.
- Export to PNG, JPEG, and PDF.
- Gesture management UI for custom gestures and actions.
- Custom actions that chain multiple toolbar clicks.

## Requirements
- Python 3.10+ (project venv uses 3.10)
- A webcam
- Windows tested (OpenCV + MediaPipe)

## Libraries Used
Core runtime libraries from `requirements.txt`:
- `mediapipe`: hand tracking and gesture recognition (Tasks API).
- `opencv-python` / `opencv-contrib-python`: camera capture, rendering, UI overlays, and image export.
- `numpy`: image buffers and mask math.
- `pillow`: PDF export support.
- `reportlab`: PDF backend dependency (via Pillow).
- `matplotlib` and related dependencies: required by the current environment (not used directly in runtime paths).
- `sounddevice`, `cffi`: installed but not used in the current runtime paths.
- `absl-py`, `flatbuffers`, `protobuf`-related dependencies: required by MediaPipe.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure model files exist:
- `models/hand_landmarker.task`
- `models/gesture_recognizer.task`

## Run
Start the main canvas:

```bash
python main.py
```

Start with the gesture management panel:

```bash
python run_gesture_ui.py
```

## Controls
### Default Gesture Mapping
Configured in `config/gesture_profile.json`:
- `Pointing_Up` -> `DRAW`
- `Victory` -> `ERASE`
- `Closed_Fist` -> `STOP`
- `Open_Palm` -> `CLEAR`
- `Thumb_Up` -> `UNDO`
- `Thumb_Down` -> `REDO`
- `Pinch` -> `None` (used for toolbar click detection)

### Toolbar (Pinch to Click)
- Brush cycle, Eraser, Undo, Redo, Size +/-
- Export dropdown: PNG, JPEG, PDF

### Keyboard Shortcuts
- `c`: create a custom gesture from the current hand pose
- `b`: reload ABR brushes from the `brushes/` folder

## Custom Gestures and Actions
- Custom gestures are stored in `config/custom_gestures.json`.
- Custom actions (button click sequences) are stored in `config/custom_actions.json`.
- Use the Gesture UI to create, map, and delete gestures and actions.

## Project Structure
- `main.py`: entry point
- `run_gesture_ui.py`: launches gesture management UI
- `ai/`: hand tracking, gesture recognition, profiles, and custom gestures
- `engine/`: brush, stroke, layer, smoothing, and ABR loading
- `ui/`: toolbar, status UI, and gesture management panel
- `core/`: app controller, performance, export, logging, sessions
- `config/`: gesture mappings and runtime settings
- `exports/`: saved images
- `models/`: MediaPipe Tasks models

## ABR Brush Import
Place `.abr` files in the `brushes/` folder. The loader attempts to use optional parsers (such as `abr_parser` or `abr`). If no compatible backend is available, ABR import will be skipped with a message.

## How It Works (Detailed)
### Frame Processing Loop
1. `main.py` opens the webcam stream and creates an `AppController`.
2. Each frame is flipped horizontally to behave like a mirror.
3. The frame is passed into `AppController.process_frame()` for AI inference, drawing, and UI updates.

### AI Pipeline
1. `PerformanceManager` downsizes frames (default 256x192) and runs AI on a background thread.
2. `HandTracker` uses MediaPipe Tasks to extract hand landmarks.
3. `GestureController` uses the MediaPipe GestureRecognizer to detect known gestures.
4. `CustomGestureDetector` runs custom detection in parallel, including pinch detection (thumb/index distance with smoothing and cooldown) and custom finger extension masks for user-defined gestures.

### Gesture-to-Action Mapping
1. Mappings are loaded from `config/gesture_profile.json`.
2. Actions include drawing, erasing, undo/redo, clearing, and toolbar actions.
3. The Gesture UI can cycle or set mappings at runtime.
4. Custom actions are stored in `config/custom_actions.json` and can map to sequences of toolbar clicks.

### Drawing Engine
1. `StrokeEngine` manages stroke lifecycle and uses `StrokeSmoother` to reduce jitter.
2. `BrushEngine` renders to the active layer using round, square, spray, eraser, or ABR stamp brushes.
3. `LayerManager` composites layers into a single canvas and tracks bounding boxes for efficient blending.

### UI and Interaction
1. The toolbar is drawn as an overlay each frame.
2. Pinch gestures are translated into toolbar clicks by hit-testing the toolbar bounds.
3. The Gesture Management UI is rendered in a second window when enabled.

### Export
1. When the user clicks Export, `ExportManager` writes the canvas to `exports/`.
2. Supported formats: PNG, JPEG, and PDF.

## Troubleshooting
- If the camera does not open, ensure no other app is using it.
- If gestures feel laggy, reduce AI resolution or increase `skip_rate` in `core/performance_manager.py`.
- If export to PDF fails, confirm `pillow` is installed.
