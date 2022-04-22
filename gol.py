import random
import panel
import time
import math

field = []
aging = 10
inherit = 1.5

def getColor(c):
    """Convert the provided 24-bit color value to color white, red, green, blue
    Each color component is a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    return ((c >> 24) & 0xff, (c >> 16) & 0xff, (c >> 8) & 0xff, (c) & 0xff) 

def addColor(c1, c2):
    cm1 = getColor(c1)
    cm2 = getColor(c2)
    return panel.Color(
        min(255,math.floor((cm1[1]+cm2[1])/inherit)),
        min(255,math.floor((cm1[2]+cm2[2])/inherit)),
        min(255,math.floor((cm1[3]+cm2[3])/inherit)))

def init():
    global field
    for cell in range(1024):
        field.append(panel.panel[cell])

def run():
    global field
    new_field = [0]*1024
    for x in range(32):
        for y in range(32):
            neighbours = 0
            alive = field[x*32 + y]
            new_cell = 0
            # Neighbours
            if(x-1 >= 0 and field[(x-1)*32 + y]):
                neighbours +=1
                new_cell = addColor(new_cell, field[(x-1)*32 + y])
            if(x-1 >= 0 and y-1 >=0 and field[(x-1)*32 + y-1]):
                neighbours +=1
                new_cell = addColor(new_cell, field[(x-1)*32 + y-1])
            if(x-1 >= 0 and y+1 <32 and field[(x-1)*32 + y+1]):
                neighbours +=1
                new_cell = addColor(new_cell, field[(x-1)*32 + y+1])

            if(x+1 < 32 and field[(x+1)*32 + y]):
                neighbours +=1
                new_cell = addColor(new_cell, field[(x-1)*32 + y])
            if(y-1 >= 0 and field[x*32 + y-1]):
                neighbours +=1
                new_cell = addColor(new_cell, field[x*32 + y-1])
            
            if(y+1 < 32 and field[x*32 + y+1]):
                neighbours +=1
                new_cell = addColor(new_cell, field[x*32 + y+1])
            if(x+1 < 32 and y-1 >=0 and field[(x+1)*32 + y-1]):
                neighbours +=1
                new_cell = addColor(new_cell, field[(x+1)*32 + y-1])
            if(x+1 < 32 and y+1 <32 and field[(x+1)*32 + y+1]):
                neighbours +=1
                new_cell = addColor(new_cell, field[(x+1)*32 + y+1])
                
            # Eine lebendige Zelle stirbt, wenn sie weniger als zwei lebendige Nachbarzellen hat.
            if alive and neighbours < 2:
                new_field[x*32 + y] = 0
            # Eine lebendige Zelle mit zwei oder drei lebendigen Nachbarn lebt weiter.
            elif alive and neighbours <= 3:
                color = getColor(field[x*32 + y])
                new_color = panel.Color(max(0,color[1]-aging),max(0,color[2]-aging),max(0,color[3]-aging))
                new_field[x*32 + y] = new_color
            # Eine lebendige Zelle mit mehr als drei lebenden Nachbarzellen stirbt im nächsten Zeitschritt.
            elif alive and neighbours > 3:
                new_field[x*32 + y] = 0
            # Eine tote Zelle wird wiederbelebt, wenn sie genau drei lebende Nachbarzellen hat.
            if not alive and neighbours == 3:
                new_color = getColor(new_cell)
                new_field[x*32 + y] = panel.Color(new_color[1],new_color[2],new_color[3])
                            
    field = new_field.copy()      
    if not any(new_field):    
        global running
        running = False

def display():
    global field
    panel.clear()
    panel.panel = field.copy()
    panel.display()

running = True

if __name__ == "__main__":
    panel.init_strip()
    for c in range(1024):
        
        if random.randint(0,10) > 4:
            panel.panel[c] = panel.Color(random.randint(0,200),random.randint(0,200),random.randint(0,200))

    init()
    while(running):
        run()
        display()
        time.sleep(0.1)
