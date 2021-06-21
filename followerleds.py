import panel
import json
import datetime
import signal
import random

import paho.mqtt.client as mqtt
import sqlite3
import re

con = sqlite3.connect('led.db')
cur = con.cursor()

effects = {}
state = {}

def blink(username, color):
    ret = color
    if state.get(username, 0):
        if state[username] % 2:
            ret = panel.Color(1,1,1)
        state[username] = state[username] - 1
    else:
        del(effects[username])
    return ret


boomcolors = [
    panel.Color(1,1,1),
    panel.Color(10,10,10),
    panel.Color(20,20,20),
    panel.Color(40,40,40),
    panel.Color(70,70,70),
    panel.Color(130,130,130),
    panel.Color(190,190,190),
    panel.Color(255,255,255),
    panel.Color(255,255,255),
    panel.Color(255,255,255),
]
def boom(username, color):
    ret = color
    if state.get(username, 0):
        ret = boomcolors[state[username] - 1]
        print("boom: ", ret)
        state[username] = state[username] - 1
    else:
        del(effects[username])
    return ret

def rainbow(username, color):
    pos = state[username]
    if state[username] < 255:
        state[username] = state[username] + 1
    else:
        state[username] = 0
    brightness=1
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return panel.Color(int(g/brightness), int(r/brightness), int(b/brightness))

def fastbow(username, color):
    pos = state[username]
    if state[username] < 255:
        state[username] = state[username] + 10
    else:
        state[username] = 0
    brightness=1
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return panel.Color(int(g/brightness), int(r/brightness), int(b/brightness))

def identify(username, color):
    return blink(username, color)

functions = {
    "blink": blink,
    "boom": boom,
    "rainbow": rainbow,
    "fastbow": fastbow,
    "identify": identify,
}
functions_state = {
    "blink": lambda : random.randint(25,100)*2,
    "boom": lambda :10,
    "rainbow": lambda: random.randint(0,255),
    "fastbow": lambda: random.randint(0,255),
    "identify": lambda:4,
}

table_sql = """CREATE TABLE if not exists "leds" (
	"id"	INTEGER NOT NULL UNIQUE,
	"owner"	TEXT UNIQUE,
	"color"	INTEGER,
	"lastSeen"	TEXT,
	PRIMARY KEY("id")
);"""
cur.execute(table_sql)
### fill db
for id in range(1024):
    cur.execute("INSERT OR IGNORE INTO leds VALUES(?,NULL,?,?)",(id,"",""))
con.commit()

regex = re.compile("^\!led ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]) ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]) ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])$")


def xy2pos(x, y):
    return (x * 32) + y

def pos2xy(pos):
    return (int(pos/32)+1, (pos%32)+1)

def gen_whisper(username, msg):
    j = json.dumps({"username":username, "message":msg, "channel":"platinenmacher"})
    print(j)
    return j

def say_led_number(username, num):
    pass
    #client.publish("chat/whisper", payload=gen_whisper(username, "Willkommen {user} Nummer ist {num}".format(user=username, num=num)))

def update_led_number(username, num):
    x,y = pos2xy(num)
    mqtt_client.publish("chat/out", payload="@{user} deine LED ist Nr. {num} und befindet sich auf {x}/{y}.".format(user=username, num=num, x=x, y=y))

def blink_info(username, num):
    mqtt_client.publish("chat/out", payload="@{user} deine LED blinkt jetzt {num} mal.".format(user=username, num=int(num)))

def send_help(username):
    #print("@{user} du kannst folgende Funktionen ausführen:\n!led 1-255 1-255 1-255\n!led off\n!led info\n!led run[{commands}]".format(user=username, commands="|".join(functions.keys())))
    mqtt_client.publish("chat/out", payload="@{user} du kannst folgende Funktionen ausführen:\n!led 1-255 1-255 1-255\n!led off\n!led info\n!led run[{commands}]".format(user=username, commands="|".join(functions.keys())))

def update_user(username, colour=None, info=False):
    ### random ID
    cur.execute("SELECT * FROM leds WHERE owner IS NULL ORDER BY RANDOM();")
    res = cur.fetchone()
    try:
        cur.execute("UPDATE leds SET owner=? WHERE id=?",(username, res[0]))
        #say_led_number(username, res[0])
    except:
        pass

    if(colour):
        cur.execute("UPDATE leds SET lastSeen=DATETIME('now'), color=? WHERE owner=?;", (colour, username))
    else:
        cur.execute("UPDATE leds SET lastSeen=DATETIME('now') WHERE owner=?;", (username,))

    if info:
        cur.execute("SELECT id FROM leds WHERE owner=?;",(username,))
        update_led_number(username, cur.fetchone()[0])

    con.commit()
    #update_panel()

def update_panel():
    panel.clear()
    cur.execute("SELECT * FROM leds WHERE owner IS NOT NULL AND lastSeen>DATETIME('now', '-10800 seconds');")
    for led in cur.fetchall():
        if(led[1]):
            curcol = led[2]
            if effects.get(led[1], 0):
                curcol = effects[led[1]](led[1], curcol)
            panel.panel[led[0]]=curcol

    panel.display()

def SignalHandler(signum, frame):
    con.commit()
    print("saved")
    quit()

def on_connect(client, userdata, flags, rc):
    print("connected")

def on_message(client, userdata, msg):
    # message zerlegen
    if not msg.payload:
        update_panel()
        return
    m = json.loads(msg.payload)
    try:
        chat_text = m.get('message').lower()
        if chat_text.startswith('!led'):
            num = regex.findall(chat_text)
            if len(num) == 1:
                col = panel.Color(int(num[0][0]),int(num[0][1]),int(num[0][2]))
                update_user(m.get('username'), col)
                return
            if chat_text[5:8] == "off":
                update_user(m.get('username'), panel.Color(1,1,1))
                return
            if chat_text[5:9] == "info" or chat_text[5:11] == "status":
                update_user(m.get('username'), info=True)
                return
            if chat_text[5:8] == "run":
                update_user(m.get('username'))
                fun = chat_text[9:]
                if fun in functions:
                    print(fun, functions[fun])
                    state[m.get('username')] = functions_state[fun]()
                    effects[m.get('username')] = functions[fun]
                return
            if chat_text[5:9] == "help":
                send_help(m.get('username'))
                return
    except:
        pass
    
    #update_user(m.get('username'))
    


if __name__ == "__main__":
    #signal.signal(signal.SIGINT, SignalHandler)
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect("192.168.1.21", 1883, 60)
    mqtt_client.subscribe("chat/in")

    panel.init_strip()

    panel.display()

    mqtt_client.loop_forever()
