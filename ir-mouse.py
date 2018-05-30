#!/usr/bin/python

# ir-mouse.py
# Use the webcam to track an infrared pointing device, and then
# translate those motions into mouse pointer movement. Although
# I developed this with a head-mounted pointing device, any infrared
# device (even a TV remote) works.
#
# The OpenCV documentation site (https://docs.opencv.org) has
# loads of code examples and tutorials; some of this code is based
# on those examples.
#
# Copyright (c) 2018, Chris Coffey <kpuc@sdf.org>
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted, provided
# that the above copyright notice and this permission notice appear
# in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL 
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA
# OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#

"""Track an infrared pointing device using a webcam and move the mouse pointer"""

import sys
import argparse
import numpy as np
import cv2
from pymouse import PyMouse


def irMouse():
    """Open webcam, track IR movements, and move the mouse pointer accordingly.
    
    Returns:
        0 on success, -1 otherwise
    """
    retval = 0

    # Open up a webcam capture
    capture = cv2.VideoCapture(0)

    # Reduce video size for faster processing
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 600)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 450)

    # Create windows
    cv2.namedWindow('Hue', flags=cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('Saturation', flags=cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('Value', flags=cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('Composite', flags=cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('Tracking', flags=cv2.WINDOW_AUTOSIZE)

    # Spread out the windows a bit so they're not directly on top of each other
    cv2.moveWindow('Tracking', 0, 0)
    cv2.moveWindow('Composite', 400, 0)
    cv2.moveWindow('Value', 0, 340)
    cv2.moveWindow('Hue', 400, 340)
    cv2.moveWindow('Saturation', 800, 340)

    # Add trackbars to make on-the-fly testing easier. After you've found
    # values that work for your own environment, you'll probably want to change
    # the default values here
    cv2.createTrackbar('hmin', 'Hue', 51, 179, lambda *args: None)
    cv2.createTrackbar('hmax', 'Hue', 62, 179, lambda *args: None)
    cv2.createTrackbar('smin', 'Saturation', 12, 255, lambda *args: None)
    cv2.createTrackbar('smax', 'Saturation', 43, 255, lambda *args: None)
    cv2.createTrackbar('vmin', 'Value', 250, 255, lambda *args: None)
    cv2.createTrackbar('vmax', 'Value', 255, 255, lambda *args: None)

    mouse = PyMouse()
    screenSize = mouse.screen_size()

    newLoc = (0, 0)

    print("Running, press Esc to exit...")

    # Loop infinitely reading webcam data until user presses Escape
    while True:

        ret, frame = capture.read()

        if ret == True:

            # Convert capture to hue, saturation, value
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hue, sat, val = cv2.split(hsv)

            # Get threshold values from trackbars
            hmin = cv2.getTrackbarPos('hmin', 'Hue')
            hmax = cv2.getTrackbarPos('hmax', 'Hue')
            smin = cv2.getTrackbarPos('smin', 'Saturation')
            smax = cv2.getTrackbarPos('smax', 'Saturation')
            vmin = cv2.getTrackbarPos('vmin', 'Value')
            vmax = cv2.getTrackbarPos('vmax', 'Value')

            # Apply thresholding values
            hthresh = cv2.inRange(np.array(hue), np.array(hmin), np.array(hmax))
            sthresh = cv2.inRange(np.array(sat), np.array(smin), np.array(smax))
            vthresh = cv2.inRange(np.array(val), np.array(vmin), np.array(vmax))

            # AND value and hue
            composite = cv2.bitwise_and(vthresh,hthresh)

            # Do some morphological transformations to clean up image
            kernel = np.ones((5,5), np.uint8)
            composite = cv2.dilate(composite, kernel, iterations = 1)
            composite = cv2.morphologyEx(composite, cv2.MORPH_CLOSE, kernel)

            # Use big kernel for blurring
            argRad = 55
            composite = cv2.GaussianBlur(composite, (argRad, argRad), 0)

            prevLoc = newLoc

            # Get the maximum location
            (_, _, _, newLoc) = cv2.minMaxLoc(composite)

            # Only proceed if we are NOT at the top left (i.e., default) corner
            if newLoc != (0, 0) and prevLoc != (0, 0):

                # Calculate x-axis and y-axis changes between prevLoc and newLoc
                delta = np.subtract(newLoc, prevLoc)

                # Calculate actual distance between prevLoc and newLoc
                distance = cv2.norm(newLoc, prevLoc)

                # Has the IR pointer moved a "reasonable" distance? If so, move the mouse pointer
                if distance > 3:
                    if args.opt_verbose == True:
                        print("IR pointer moved {0}".format(distance))

                    # Set the scale factor: bigger IR moves == bigger mouse moves
                    if distance > 20:
                        scaleFactor = 1.7
                    elif distance > 9:
                        scaleFactor = 1.4
                    elif distance > 6:
                        scaleFactor = 1.2
                    else:
                        scaleFactor = 1.0

                    # Get the mouse pointer's current location
                    curPtr = mouse.position()

                    if args.opt_verbose == True:
                        print("\tMouse pointer is currently at {0}".format(curPtr))

                    # Calculate the new mouse pointer location
                    newPtrX = int(curPtr[0] - (delta[0] * (distance * scaleFactor)))
                    newPtrY = int(curPtr[1] + (delta[1] * (distance * scaleFactor)))

                    # Sanity check the new pointer location values
                    if newPtrX < 0:
                        newPtrX = 0
                    if newPtrX > screenSize[0]:
                        newPtrX = screenSize[0]
                    if newPtrY < 0:
                        newPtrY = 0
                    if newPtrY > screenSize[1]:
                        newPtrY = screenSize[1]

                    # Move the mouse pointer
                    mouse.move(newPtrX, newPtrY)

                    if args.opt_verbose == True:
                        print("\tMoved mouse pointer to {0}, {1}".format(newPtrX, newPtrY))

            # Draw circle around what we're tracking
            cv2.circle(frame, newLoc, 10, (128, 255, 0), 2)
            
            # Display results in windows
            cv2.imshow('Hue', hthresh)
            cv2.imshow('Saturation', sthresh)
            cv2.imshow('Value', vthresh)
            cv2.imshow('Composite', composite)
            cv2.imshow('Tracking', frame)

            # Esc key pressed?
            if cv2.waitKey(5) & 0xff == 27:
                break

        else:
            print("Webcam capture failed!")
            retval = -1
            break

    # End while loop

    print("Exiting...")
    cv2.destroyAllWindows()
    capture.release()

    return retval


def main():
    """Main routine"""

    global args
    parser = argparse.ArgumentParser(description='Track an infrared pointing device using a webcam, and move the mouse pointer accordingly.')
    parser.add_argument('-v', '--verbose', dest='opt_verbose', action='store_true',
                        help='Display verbose information')
    
    args = parser.parse_args()

    return irMouse()
    
    
if __name__ == '__main__':
    sys.exit(main())

