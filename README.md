ir-mouse
========
This is a Python program that works in tandem with an infrared pointing device ([read the complete backstory here](https://ccoff.github.io/a-modest-mouse)). It uses the webcam to track an infrared pointing device, and then translates those motions into mouse pointer movement.

Although I originally designed this with a head-mounted pointing device in mind, any infrared pointing device (such a TV remote) works.

I have only tested this on Linux, though Windows and Mac should work with minimal tweaking. You will probably want to change the default value and hue thresholds based on your own environment.

Usage
-----
Type `python ir-mouse.py` at the command line. Alternatively, type `chmod 755 ir-mouse.py` to enable starting the program directly (i.e., `./ir-mouse.py`). The following command-line options are available:

**-v**: Display verbose information.

