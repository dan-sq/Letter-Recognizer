# Description
This program polls a T265 RealSense camera for its pose and renders it on the screen via a Tkinter canvas.
Then, using an implementation of the $N Multistroke Recognizer, compares the drawing against selected templates
and returns the template that matches the candidate gesture.

# Dependencies
pyrealsense2 2.53.1.4623
python 3.10.11
T265 RealSense Tracking Camera

# Usage
 - Windows Example:
 - Create virtual environment: py -3.10 -m venv .venv
 - Activate virtual environment: .\.venv\Scripts\Activate
 - Install dependency: pip install -r requirements.txt
 - Run program: python main.py

# References

# $N Multistroke Recognizer
 - https://depts.washington.edu/acelab/proj/dollar/ndollar.html