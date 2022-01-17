#!/usr/bin/env python3
# rpi_ws281x library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
from rpi_ws281x import *
import argparse
from PIL import Image, ImageFont, ImageDraw  

# LED strip configuration:
LED_COUNT      = 1024      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Erzeuge panel array mit schwarz
panel = []
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)


def display():
    for x in range(32):
        for y in range(32):
            if y < 8:
                if (x%2==0):
                    p = x*8+y
                else:
                    p = x*8+7-y
            elif y < 16:
                if (x%2==0): # x ist gerade
                    p = (31-x)*8+(y-7)
                else:
                    p = (31-x)*8+(16-y)
                p+=255
            elif y < 24:
                if (x%2==0):
                    p = x*8+y-16
                else:
                    p = x*8+7+(16-y)
                p+=(256*2)
            else:
                if (x%2==0):
                    p = (31-x)*8+(y-23)
                else:
                    p = (31-x)*8+32-y
                p+=(256*3-1)
            #c = panel[x +(y*32)]
            #c = reduceBrightnes(c)
            if panel[x +(y*32)]:
                strip.setPixelColor(p, panel[x +(y*32)])
    strip.show()

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def reduceBrightnes(c):
    white = int(translate((c >> 24) & 0xff, 0, 255, 0, LED_BRIGHTNESS))
    red = int(translate((c >> 16) & 0xff, 0, 255, 0, LED_BRIGHTNESS))
    green = int(translate((c >> 8) & 0xff, 0, 255, 0, LED_BRIGHTNESS))
    blue = int(translate(c & 0xff, 0, 255, 0, LED_BRIGHTNESS))
    
    return (white << 24) | (red << 16) | (green << 8) | blue

def render_cat(panel):
    cat = Image.open("cat.png")
    print(cat)
    panel = [Color(p[0],p[1],p[2]) for p in cat.convert('RGB').getdata()]
    return panel

def render_chip(panel):
    chip = Image.open("chip.png")
    panel = [Color(p[0],p[1],p[2]) for p in chip.convert('RGB').getdata()]
    return panel

def init_strip():

    for x in range(32*32):
            panel.append(0)

    # Create NeoPixel object with appropriate configuration.
    
    # Intialize the library (must be called once before other functions).
    strip.begin()

    return strip


def clear():
    for x in range(32*32):
            strip.setPixelColor(x, 0)
            panel[x] = 0


# Main program logic follows:
if __name__ == '__main__':
    
    strip = init_strip()

    print ('Press Ctrl-C to quit.')

    while True:
        panel = render_chip(panel)
        display(panel)
        time.sleep(10)
        panel = render_cat(panel)
        panel[0] = Color(20,20,20)
        display(panel)
        time.sleep(10)
