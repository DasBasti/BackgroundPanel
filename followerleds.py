# coding=utf-8
import panel
import json
import datetime
import signal
import random
import threading
import time
import queue
import random
from morse import morseTranslator

import paho.mqtt.client as mqtt
import sqlite3
import re

import requests


con = sqlite3.connect('led.db')
cur = con.cursor()

mqtt_message_list = queue.Queue()

effects = {}
state = {}
discomode = 0

disco_colors=[
    panel.Color(0,0,0),
    panel.Color(0,0,0),
    panel.Color(0,0,0),
    panel.Color(50,0,0),
    panel.Color(0,50,0),
    panel.Color(0,0,50),
    panel.Color(30,30,30),
]

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

def morse(username, color):
    if len(state[username])>1:
        state[username] = state[username][1:]
        return color if state[username][0] == "x" else panel.Color(0,0,0)
    else:
        del(effects[username])

def identify(username, color):
    return blink(username, color)

def stop(username, color):
    del effects[username]
    return color

functions = {
    "blink": blink,
    "boom": boom,
    "rainbow": rainbow,
    "fastbow": fastbow,
    "morse": morse,
    "identify": identify,
    "stop": stop
}
functions_state = {
    "blink": lambda  args: random.randint(25,100)*2,
    "boom": lambda  args:10,
    "rainbow": lambda args: random.randint(0,255),
    "fastbow": lambda args: random.randint(0,255),
    "morse": lambda args: morseTranslator(" ".join(args)),
    "identify": lambda args: 4,
    "stop": lambda args: 0,
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

pipeline_free=True
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
    mqtt_message_list.put("@{user} deine LED ist Nr. {num} und befindet sich auf {x}/{y}.".format(user=username, num=num, x=x, y=y))

def blink_info(username, num):
    mqtt_message_list.put("@{user} deine LED blinkt jetzt {num} mal.".format(user=username, num=int(num)))

def send_help(username):
    mqtt_message_list.put("@{user} du kannst folgende Funktionen ausführen:".format(user=username))
    mqtt_message_list.put("!led 1-255 1-255 1-255")
    mqtt_message_list.put("!led off")
    mqtt_message_list.put("!led info|status")
    mqtt_message_list.put("!led run [{commands}]".format(commands="|".join(functions.keys())))

def send_mqtt_list():
    global running
    while(running):
        if not mqtt_message_list.empty():
            payload = mqtt_message_list.get()
            mqtt_client.publish("chat/out", payload=payload)
            time.sleep(1)
        else:
            time.sleep(0.1)


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
        requests.post("https://platinenmacher.tech/pcb/panel/led/"+username ,
                data={
                    'auth': 123,
                    'owner': username,
                    'color': colour
                    })
        cur.execute("UPDATE leds SET lastSeen=DATETIME('now'), color=? WHERE owner=?;", (colour, username))
    else:
        cur.execute("UPDATE leds SET lastSeen=DATETIME('now') WHERE owner=?;", (username,))

    if info:
        cur.execute("SELECT id FROM leds WHERE owner=?;",(username,))
        update_led_number(username, cur.fetchone()[0])

    con.commit()
    #update_panel()

def update_panel():
    global discomode
    panel.clear()
    if discomode == 0:
        con = sqlite3.connect('led.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM leds WHERE owner IS NOT NULL AND lastSeen>DATETIME('now', '-10800 seconds');")
        for led in cur.fetchall():
            if(led[1]):
                curcol = led[2]
                if effects.get(led[1], 0):
                    curcol = effects[led[1]](led[1], curcol)
                panel.panel[led[0]]=curcol
    else:
        for led in range(1024):
            panel.panel[led]=random.choice(disco_colors)
        discomode -=1
        print("Discomode: ", discomode)
    panel.display()

def SignalHandler(signum, frame):
    global running
    con.commit()
    running = False
    print("saved")
    quit()

def on_connect(client, userdata, flags, rc):
    print("connected")

def on_message(client, userdata, msg):
    # message zerlegen
    if not msg.payload:
        return
    m = json.loads(msg.payload)
    try:
        username = m.get("username").lower()
        chat_text = m.get('message').lower()
        if chat_text.startswith('!led'):
            num = regex.findall(chat_text)
            if len(num) == 1:
                col = panel.Color(int(num[0][0]),int(num[0][1]),int(num[0][2]))
                print(int(num[0][0]),int(num[0][1]),int(num[0][2]))
                update_user(username, col)
                return
            if chat_text[5:8] == "off":
                update_user(username, panel.Color(1,1,1))
                return
            if chat_text[5:9] == "info" or chat_text[5:11] == "status":
                update_user(username, info=True)
                return
            if chat_text[5:11] == "random":
                r,g,b = (random.randint(1,255), random.randint(1,255), random.randint(1,255))
                update_user(username, panel.Color(r,g,b))
                mqtt_message_list.put("@{username} deine LED leuchtet jetzt in ({r} {g} {b})RGB".format(username=m.get('username'), r=r, g=g, b=b))
                return

            """ !led run command
                !led run command args
            """ 
            if chat_text[5:8] == "run":
                update_user(username)
                cmd = chat_text[9:].split(" ")
                fun = cmd[0]
                args = cmd[1:]
                print("Run:",fun)
                if fun in functions:
                    print(fun, functions[fun])
                    state[username] = functions_state[fun](args)
                    effects[username] = functions[fun]
                else:
                    mqtt_message_list.put("@{username} !led run [{commands}]".format(username=m.get('username'), commands="|".join(functions.keys())))
                return
            if chat_text[5:9] == "help" or chat_text[5:6] == "?":
                send_help(m.get('username'))
                return
            if chat_text[5:10] == "disco":
                global discomode
                discomode = 10
                return
        else:
            update_user(username)
    except Exception as e:
        print(e)
        pass
    
def update_panel_thread():
    global running
    while(running):
        update_panel()
        if discomode == 0:
            time.sleep(0.1)
        else:
            time.sleep(1)

if __name__ == "__main__":
    global running
    running = True
    signal.signal(signal.SIGINT, SignalHandler)
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    send_queue = threading.Thread(target=send_mqtt_list)
    send_queue.start()

    display_fred = threading.Thread(target=update_panel_thread)

    mqtt_client.connect("192.168.1.21", 1883, 60)
    mqtt_client.subscribe("chat/in")

    panel.init_strip()

    panel.display()

    display_fred.start()
    mqtt_client.loop_forever()
