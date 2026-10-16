# Gesture-Control-Media-Player

**Developed by:** Hrishikesh Sharma  
**GitHub:** [@RaavanHrishi07](https://github.com/RaavanHrishi07)

Control your media playback using hand gestures captured through your webcam. This project uses **MediaPipe Hand Landmarker** to track hand landmarks and recognise finger-count gestures, with OpenCV for camera input and PyAutoGUI for media-key commands.

## Features

- Real-time webcam hand tracking
- Hand landmark visualisation
- Finger-count-based gesture recognition
- Stable gesture confirmation to reduce accidental commands
- Media controls using keyboard media keys
- Camera cleanup when the application exits

## Gesture Controls

| Fingers Detected | Action |
|---|---|
| 1 finger | Volume Up |
| 2 fingers | Volume Down |
| 3 fingers | Mute |
| 4 fingers | Play / Pause |
| 5 fingers | Stop |
| No hand / fist | No action |

**Tip:** After triggering a gesture, change the gesture or remove your hand before showing it again. The program requires a stable gesture before sending a media command.

## Requirements

- Python 3.11
- A working webcam
- Windows (the current configuration uses the DirectShow camera backend)
- A media player that responds to standard media keys

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/RaavanHrishi07/Gesture-Control-Media-Player.git
cd Gesture-Control-Media-Player
```

### 2. Install dependencies

```powershell
python -m pip install opencv-python mediapipe pyautogui
```

### 3. Check the model file

Make sure the following model file exists:

```text
models/hand_landmarker.task
```

The application uses this file for MediaPipe hand tracking.

### 4. Run the application

```powershell
python vlc-Gesture-Control.py
```

Place your hand in front of the webcam and show one to five fingers. The application displays the detected hand landmarks and sends the corresponding media-key command.

Press **Q** to close the application.

## Configuration

The following settings can be adjusted near the top of `vlc-Gesture-Control.py`:

- `CAMERA_INDEX`: webcam device index; currently set to `1`
- `HISTORY_SIZE`: number of recent finger-count results retained
- `CONFIRMATION_FRAMES`: consecutive confirmations required before a command
- `COMMAND_COOLDOWN`: minimum delay between commands

If the webcam does not open, close other camera applications and check the camera index and Windows camera permissions.

## How It Works

1. OpenCV captures frames from the webcam.
2. MediaPipe Hand Landmarker identifies hand landmarks.
3. The application estimates the number of extended fingers.
4. Recent results are checked for a stable finger count.
5. PyAutoGUI sends the corresponding media-key command.

## Limitations

- Finger counting can be affected by hand orientation, lighting, and camera angle.
- Media controls depend on the active operating system and media player.
- The configured camera index may need to be changed on other computers.

## Project Structure

```text
Gesture-Control-Media-Player/
├── models/
│   └── hand_landmarker.task
├── vlc-Gesture-Control.py
├── README.md
├── LICENSE
└── .gitignore
```

## License

See the `LICENSE` file for the project's licensing information.