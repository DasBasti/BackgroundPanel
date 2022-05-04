""" Dino Game """

import panel
import json
import random
import paho.mqtt.client as mqtt
import sqlite3
import signal, os
import time

def SignalHandler(signum, frame):
    con.commit()
    print("saved")
    quit()

con = sqlite3.connect('eieiei.db')
cur = con.cursor()
HOST = 'cloud.eieiei.lol'
#HOST = '192.168.1.21'
PORT = 1883

player=[]


playing_field = []
for i in range(1024):
    playing_field.append(dict(player=-1,food=0)) #empty field

def xy2pos(x, y):
    return (x * 32) + y

def move_player(id, x, y):
    # valid
    return True
    #invalid
    return False

def generate_food():
    x = random.randint(0,31)
    y = random.randint(0,31)
    print("food at {x}/{y}".format(x=x,y=y))
    playing_field[xy2pos(x,y)]['food'] += 5
    return True

def render_panel():
    panel.clear()
    food_avail = 0
    
    for index, field in enumerate(playing_field):
        if field.get('food', 0) > 0:
            panel.panel[index] = panel.Color(0,field['food'],0)
            food_avail += field['food']

    five_minutes_ago = int(time.time()) - 300
    cur.execute('SELECT * FROM dino') # WHERE last_update > ?', (five_minutes_ago,))
    for d in cur.fetchall():
        x = d[2]
        y = d[3]
        # move
        if random.randint(1,100) < 25:
           x += 1 
        if random.randint(1,100) < 25:
           x -= 1 
        if random.randint(1,100) < 25:
           y += 1 
        if random.randint(1,100) < 25:
           y -= 1 
        # stop at wall
        if x < 0:
            x = 0
        if x > 31:
            x= 31
        if y < 0:
            y = 0
        if y > 31:
            y= 31

        dino = {}        
        dino['x'] = x
        dino['y'] = y

        cur.execute('SELECT name FROM dino WHERE x=? AND y=?', (x,y))
        res = cur.fetchone()
        if res:
            dino['meet'] = d[0]

        panel.panel[xy2pos(x,y)] = panel.Color(d[5], d[6], d[7])
        #client.publish("dino/{id}".format(id=d[0], payload=json.dumps(dino)))
    
    panel.display()
    """client.publish("dino/game", payload=json.dumps({
        "food_avail": food_avail
    }), qos=0, retain=False)
"""

def on_connect(client, userdata, flags, rc):
    print("Connected to {0} with result code {1}".format(HOST, rc))

def on_message(client, userdata, msg):
    print("Message received on topic {0}: {1}"\
        .format(msg.topic, msg.payload))
    if msg.payload[0] == 123:
        print(msg.payload[0])
        """
    event = json.loads(msg.payload) 
    print(event)
    
    if "feed" in event:
        generate_food()
    
    if "dino" in event:
        # if new player add
        cur.execute('SELECT * FROM dino WHERE id=?', (event['dino'].get('id'),))
        res = cur.fetchone()
        if res:
            print("update player: ", event['dino'].get('name'))
            val = (event['dino'].get('name'), event['dino'].get('r'), event['dino'].get('g'),event['dino'].get('b'),event['dino'].get('id'),int(time.time()))
            cur.execute('UPDATE dino SET name=?,r=?,g=?,b=?,last_update=? WHERE id=?', val)        
        else:
            print("new player joined: ", event['dino'].get('name'))
            val = (event['dino'].get('id'), event['dino'].get('name'),random.randint(0,31),random.randint(0,31),0,event['dino'].get('r'),event['dino'].get('g'),event['dino'].get('b') ,int(time.time()))
            cur.execute('INSERT INTO dino VALUES (?,?,?,?,?,?,?,?,?)', val)
"""
    else:
    
        cur.execute('SELECT * FROM dino WHERE id=?', (msg.payload,))
        res = cur.fetchone()
        if res:
            print("update player: ", msg.payload)
            val = (msg.payload, int(time.time()))
            cur.execute('UPDATE dino SET last_update=? WHERE id=?', val)        
        else:
            print("new player joined: ", msg.payload)
            val = (msg.payload, msg.payload,random.randint(0,31),random.randint(0,31),0,random.randint(30,128),random.randint(30,128),random.randint(30,128),int(time.time()))
            cur.execute('INSERT INTO dino VALUES (?,?,?,?,?,?,?,?,?)', val)
        
    render_panel()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, SignalHandler)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(HOST, PORT, 60)
    client.subscribe("dino/in/#")

    panel.init_strip()

    panel.display()

    client.loop_forever()
