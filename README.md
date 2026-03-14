# Enterprise AI Paint (Writing in the Air)

Real-time air drawing with a webcam using hand tracking and gesture recognition. Draw on a virtual canvas, switch tools, and export artwork without touching the keyboard.

## Features
- Gesture-driven drawing, erase, clear, undo, and redo actions
- Pinch-to-click toolbar controls for brush selection and size changes
- Multiple brush types: round, square, spray, plus eraser
- Layered canvas with undo/redo support
- Export to PNG, JPEG, or PDF
- Live UI overlay with brush preview and FPS

## Tech Stack
- Python 3.8+
- OpenCV (camera capture and rendering)
- MediaPipe Tasks (hand tracking and gesture recognition)

## Requirements
- Webcam
- Python 3.8+ (3.10+ recommended)
- Dependencies in `requirements.txt`

## Clone
```bash
git clone https://github.com/godgodgodsd/Writing-in-the-air.git
cd Writing-in-the-air
```

## Install
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python main.py
```
Press `Esc` to exit the app.

## Controls
### Drawing gestures (default mapping)
Configured in `config/gesture_profile.json`:
- `Pointing_Up` -> DRAW
- `Victory` -> ERASE
- `Closed_Fist` -> STOP
- `Open_Palm` -> CLEAR
- `Thumb_Up` -> UNDO
- `Thumb_Down` -> REDO

### Toolbar (pinch to click)
- Brush toggle: cycles round -> square -> spray
- Eraser
- Undo / Redo
- Size - / Size +
- Export: choose PNG, JPEG, or PDF

## Output
- Exports are saved to the `exports/` directory with timestamped filenames.

## Project Structure
```
ai/         Gesture recognition, custom gestures, profiles
core/       App controller, session/export/performance managers
engine/     Stroke engine, layers, brush logic
ui/         Toolbar and UI overlay rendering
models/     MediaPipe task models
exports/    Generated artwork exports
main.py     Application entry point
```

## Configuration
- Gesture mapping: `config/gesture_profile.json`
- Model files: `models/gesture_recognizer.task` and `models/hand_landmarker.task`

## Troubleshooting
- Camera not detected: ensure no other app is using the webcam.
- App opens but no drawing: make sure gesture model files exist under `models/`.
- Low gesture accuracy: improve lighting and keep hand fully visible.
- Export not saving: check write permissions for `exports/`.
- PDF export errors: confirm Pillow is installed (`pip install pillow`).

## Contributing
Issues and pull requests are welcome. Keep changes focused and include a short description of the behavior change.