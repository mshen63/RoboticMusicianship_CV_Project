# RoboticMusicianship_CV_Project

Makes use of mediapipe. Using webcam input, recognizes which section corresponding to a robot is pointed at to start/stop play. 

Note: must be run on local device with webcam access. 

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

In terminal, run:
```python
python hands.py
```