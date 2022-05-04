import panel
import time
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import pcb_string

def getColorsRGB(c):
    """Convert the provided 24-bit color value to color red, green, blue.
    Each color component is a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    return ((c >> 16) & 0xff, (c >> 8) & 0xff, (c) & 0xff) 



offset=25
def draw_username_on_panel(username, f, color):
    global offset
    panel.clear()
    img = Image.new(mode="RGB", size=(32, 32))
    i1 = ImageDraw.Draw(img)
    i1.text((offset,10), username, font=f, fill=getColorsRGB(color))
    offset -=1
    panel.panel = [panel.Color(p[0],p[1],p[2]) for p in img.convert('RGB').getdata()]

def reset():
    global offset
    offset=25

f = ImageFont.truetype("osifont.ttf",14)

if __name__ == "__main__":
    panel.init_strip()

    while(True):
        draw_username_on_panel("Platinenmacher", f, panel.Color(70,00,00))

        if not any(panel.panel):
            panel.display()
            break

        pcb_string.draw_pcb_string(pcb_string.code)
        panel.display()
        time.sleep(0.1)