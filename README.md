# RoboticMusicianship_CV_Project

Makes use of mediapipe. Using webcam input, recognizes which section corresponding to an arm is pointed at to start/stop play and change speeds.

Note: must be run on local device with webcam access or an attached webcam. 

## Installation

Activate a Python virtual environment.

```bash
python3 -m venv mp_env && source mp_env/bin/activate
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install mediapipe.
```bash
pip install mediapipe
```

## Usage

In terminal of computer connected to arms, run:
```python
python main_event_threading.py
```

In terminal of client computer with webcam, run:
```python
python hands_separate.py
```
