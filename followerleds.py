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

blinky = {}

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
            if blinky.get(led[1], 0):
                if blinky[led[1]] % 2:
                    curcol = panel.Color(1,1,1)
                blinky[led[1]] = blinky[led[1]]-1
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
            if chat_text[5:9] == "info":
                update_user(m.get('username'), info=True)
                return
            if chat_text[5:10] == "blink":
                blinky[m.get('username')] = random.randint(5,20) * 2
                update_user(m.get('username'))
                blink_info(m.get('username'), blinky[m.get('username')]/2)
                return
    except:
        pass
    
    #update_user(m.get('username'))
    


if __name__ == "__main__":
    signal.signal(signal.SIGINT, SignalHandler)
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect("192.168.1.21", 1883, 60)
    mqtt_client.subscribe("chat/in")

    panel.init_strip()

    panel.display()

    mqtt_client.loop_forever()
