🖋️ Writing in the Air
Enterprise-grade AI-powered air drawing and painting experience — interact with your webcam to write and paint in mid-air using hand gestures and AI gesture recognition.
Powered by computer vision and gesture analysis, this project lets users draw, erase, undo, redo, export artwork, and switch brushes without touching a single key — all using natural hand movements.
🚀 Features
✨ AI Gesture Recognition
Recognizes gestures in real time from webcam video to control actions like drawing, erasing, clearing, undo/redo, and exporting.
🖌️ Natural Air Drawing
Paint on an overlay canvas just by moving your index finger — visually composited with webcam feed.
🎨 Customizable Painting Tools
Multiple brushes (round, square, spray) with adjustable sizes.
📦 Layered Canvas Management
Supports layering, undo/redo functionality, and clean clearing.
🗂️ Export Artwork
Save your artwork in multiple export formats (e.g., PNG, JPEG).
💡 Real-time UI Overlay
Visual toolbar and instant feedback of gestures and brush previews.
📸 Preview
Add screenshots here to showcase live webcam drawing, gesture feedback, toolbar, and exported artwork.
🧠 How It Works
Capture Camera Feed
The app grabs frames from your webcam (cv2.VideoCapture(0)).
Gesture & Hand Tracking
AI modules (HandTracker, GestureController) analyze each frame to identify hand positions and gestures.
Drawing Engine
Stroke data is processed and rendered on layered canvases managed by the core engine.
User Interaction
Pinch gestures are used to interact with the UI toolbar — change brush, erase, clear, adjust sizes, and export.
Export and Save
Completed creations can be saved through the export system.
This interaction model enables a fluid, touch-free drawing experience — perfect for demos, HCI research, creative art projects, and AI-driven interfaces.
🛠️ Installation
⚙️ Requirements
Python 3.8+
Webcam
Dependencies listed in requirements.txt
Clone the repository:
git clone https://github.com/godgodgodsd/Writing-in-the-air.git
cd Writing-in-the-air
Install dependencies:
pip install -r requirements.txt
Run the application:
python main.py
🎮 Controls & Interaction
Action	Gesture / Interaction
Draw	Pinch & move index finger
Erase	Select Eraser in toolbar with pinch
Brush switch	Cycle through brushes with toolbar
Adjust brush size	+Size / -Size buttons
Undo/Redo	Corresponding toolbar buttons
Clear Canvas	Clear button
Export Artwork	Export options in toolbar
Visual feedback is shown on-screen for active gesture and FPS.
🧩 Architecture Overview
📦 Writing-in-the-air
├── core/                  # App controller and session management
├── ai/                    # Hand tracking & gesture logic
├── engine/                # Drawing & stroke management
├── ui/                    # Toolbar & UI rendering
├── exports/               # Export and file saving subsystem
├── main.py                # Entry point application loop
├── requirements.txt       # Python dependencies
📁 Project Structure
Folder	Purpose
core/	Main controller & performance handling
ai/	Gesture recognition and hand tracking modules
engine/	Paint engine, layer managers, stroke logic
ui/	Toolbar and UI overlay rendering
exports/	Image export utilities
📌 Best Practices
Keep your webcam well-lit for consistent gesture detection.
Use a plain background to improve tracking performance.
Adjust brush size using size buttons — no keyboard input needed.
🧪 Troubleshooting
✔️ Camera not detected
Make sure no other application is using the webcam.
✔️ Low gesture accuracy
Enhance lighting and ensure your hand is fully visible in frame.
✔️ Export errors
Check write permissions for the output directory.
✨ Contributing
Thank you for your interest! Contributions are welcome:
⭐ Star the repo
🐛 Report issues
🛠️ Open pull requests
📄 Improve docs and examples
