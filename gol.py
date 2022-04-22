import random
import panel
import time

field = []

def init():
    global field
    for cell in range(1024):
        n=0
        if(panel.panel[cell]):
            n=1
        field.append(n)

def run():
    global field
    new_field = [0]*1024
    for x in range(32):
        for y in range(32):
            neighbours = 0
            ## Game of life rules
            
            #      xy-1 y-1
            #      x-1  c   x+1
            #           y+1
             
            if(x-1 >= 0 and field[(x-1)*32 + y]):
                neighbours +=1
            if(x-1 >= 0 and y-1 >=0 and field[(x-1)*32 + y-1]):
                neighbours +=1
            if(x-1 >= 0 and y+1 <32 and field[(x-1)*32 + y+1]):
                neighbours +=1

            if(x+1 < 32 and field[(x+1)*32 + y]):
                neighbours +=1
            if(y-1 >= 0 and field[x*32 + y-1]):
                neighbours +=1
            
            if(y+1 < 32 and field[x*32 + y+1]):
                neighbours +=1
            if(x+1 < 32 and y-1 >=0 and field[(x+1)*32 + y-1]):
                neighbours +=1
            if(x+1 < 32 and y+1 <32 and field[(x+1)*32 + y+1]):
                neighbours +=1
                
            # Eine lebendige Zelle stirbt, wenn sie weniger als zwei lebendige Nachbarzellen hat.
            if field[x*32 + y] and neighbours < 2:
                new_field[x*32 + y] = 0
            # Eine lebendige Zelle mit zwei oder drei lebendigen Nachbarn lebt weiter.
            elif field[x*32 + y] and neighbours <= 3:
                new_field[x*32 + y] = 1
            # Eine lebendige Zelle mit mehr als drei lebenden Nachbarzellen stirbt im nächsten Zeitschritt.
            elif field[x*32 + y] and neighbours > 3:
                new_field[x*32 + y] = 0
            # Eine tote Zelle wird wiederbelebt, wenn sie genau drei lebende Nachbarzellen hat.
            if field[x*32 + y] == 0 and neighbours == 3:
                new_field[x*32 + y] = 1
                            
    field = new_field.copy()      
    pass

def display():
    global field
    panel.clear()
    for c in range(1024):
        if(field[c]):
            panel.panel[c] = panel.Color(100,100,100)
    panel.display()

if __name__ == "__main__":
    panel.init_strip()
    for c in range(1024):
        
        if random.randint(0,10) > 4:
            panel.panel[c] = panel.Color(100,100,100)

    init()
    while(True):
        run()
        display()
        time.sleep(0.1)
