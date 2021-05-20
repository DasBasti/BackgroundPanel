import panel
import json
import datetime
import signal

import paho.mqtt.client as mqtt
import sqlite3
import re

con = sqlite3.connect('led.db')
cur = con.cursor()

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
    client.publish("chat/out", payload="@{user} deine LED  ist Nr. {num} und befindet sich auf {x}/{y}.".format(user=username, num=num, x=x, y=y))

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
    update_panel()

def update_panel():
    panel.clear()
    cur.execute("SELECT * FROM leds WHERE owner IS NOT NULL AND lastSeen>DATETIME('now', '-10800 seconds');")
    for led in cur.fetchall():
        #print(led)
        if(led[1]):
            panel.panel[led[0]]=led[2]

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
        if m.get('message').startswith('!led'):
            num = regex.findall(m.get('message'))
            if len(num) == 1:
                col = panel.Color(int(num[0][0]),int(num[0][1]),int(num[0][2]))
                update_user(m.get('username'), col)
                return
            if m.get('message')[5:8] == "off":
                update_user(m.get('username'), panel.Color(1,1,1))
                return
            if m.get('message')[5:9] == "info":
                update_user(m.get('username'), info=True)
                return
    except:
        pass
    
    update_user(m.get('username'))
    


if __name__ == "__main__":
    signal.signal(signal.SIGINT, SignalHandler)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("192.168.1.21", 1883, 60)
    client.subscribe("chat/in")

    panel.init_strip()

    panel.display()

    client.loop_forever()
