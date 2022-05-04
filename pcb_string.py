import panel

pcb_lut = [
    285,
    315,
    345,
    375,
    405,
    435,
    465,
    495,
    251,
    281,
    311,
    341,
    371,
    401,
    431,
    461,
    217,
    247,
    277,
    307,
    337,
    367,
    397,
    427,
    183,
    213,
    243,
    273,
    303,
    333,
    363,
    393,
    149,
    179,
    209,
    239,
    269,
    299,
    329,
    359,
    115,
    145,
    175,
    205,
    235,
    265,
    295,
    325,
    81,
    111,
    141,
    171,
    201,
    231,
    261,
    291,
    47,
    77,
    107,
    137,
    167,
    197,
    227,
    257,
]

code = "sswwwwwssswyyowsswwyoywswswoyywswswyyowswwwoyywssswssswsssssssss"

def draw_pcb_string(code):
    i=0
    for p in code:
        if p == ' ':
            continue
        elif p == 'w':
            panel.panel[pcb_lut[i]]=panel.Color(150,150,150)
        elif p == 'k':
            panel.panel[pcb_lut[i]]=panel.Color(0,0,0)
        elif p == 'b':
            panel.panel[pcb_lut[i]]=panel.Color(0,0,200)
        elif p == 'r':
            panel.panel[pcb_lut[i]]=panel.Color(200,0,0)
        elif p == 'g':
            panel.panel[pcb_lut[i]]=panel.Color(0,200,0)
        elif p == 'y':
            panel.panel[pcb_lut[i]]=panel.Color(127,127,0)
        elif p == 'o':
            panel.panel[pcb_lut[i]]=panel.Color(127,70,0)
        elif p == 'c':
            panel.panel[pcb_lut[i]]=panel.Color(0,127,127)
        elif p == 'm':
            panel.panel[pcb_lut[i]]=panel.Color(127,0,127)
        i+=1
        if i >= 64:
            break

