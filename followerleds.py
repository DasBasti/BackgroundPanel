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
import webcolors
import levenshtein

import paho.mqtt.client as mqtt
import sqlite3
import re

import requests

"""
Global sqlite connections and cursor
"""
con = sqlite3.connect('led.db')
cur = con.cursor()

# Queue of MQTT messages to be sent to chat
mqtt_message_list = queue.Queue()

# Empty effects and state dicts. Usernames can be registerd to overwrite LED color on drawing
effects = {}
state = {}

# DISCOMODE!!!
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

"""
Blinks the LED of the user
"""
def blink(username, color):
    ret = color
    # 1. if state vale for the effect is odd blank color
    if state.get(username, 0):
        if state[username] % 2:
            ret = panel.Color(1,1,1)
        # 2. reduce state value
        state[username] = state[username] - 1
    else:
        # 3. remove effect if state reaches 0
        del(effects[username])
    return ret

"""
This function runs an animation that "explodes the LED"
"""
def boom(username, color):
    # Colors of the boom animation in reverse order
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
    ret = color
    # 1. State is bigger than 0
    if state.get(username, 0):
        # 2. Get color matching state value
        ret = boomcolors[state[username] - 1]
        print("boom: ", ret)
        # 3. reduce state value by 1
        state[username] = state[username] - 1
    else:
        # 4. if state reaches 0 remove from effects
        del(effects[username])
    return ret

def rainbow_table(pos, brightness):
    # 1. Input a value 0 to 255 to get a color value.
    #    The colours are a transition r - g - b - back to r.
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


"""
Shows a rainbow table effect
"""
def rainbow(username, color):
    # 1. Get the position on the rainbow table from state value
    pos = state[username]
    # 2. Do not increase state over 255
    if state[username] < 255:
        state[username] = state[username] + 1
    else:
        state[username] = 0
    return rainbow_table(state[username], 1)


"""
Same function as rainbow but 10x faster
"""
def fastbow(username, color):
    pos = state[username]
    if state[username] < 255:
        state[username] = state[username] + 10
    else:
        state[username] = 0
    return rainbow_table(state[username], 1)

"""
This effect prints out morse code. 
The code is generated at the effect initialisation
"""
def morse(username, color):
    # 1. If the state still contains data
    if len(state[username])>1:
        # 2. delete first in character in morse data
        state[username] = state[username][1:]
        # 3. Turn on LED in user color if state character is 'x' else turn LED off
        return color if state[username][0] == "x" else panel.Color(0,0,0)
    else:
        # 4. If all morse characters are displayed remove effect from username
        del(effects[username])

"""
This function is the same rendering as the blink function.
But it does come with a different initial state.
"""
def identify(username, color):
    return blink(username, color)

"""
Remove effect from username
"""
def stop(username, color):
    del effects[username]
    return color

# Dict of available functions to be called by !led command
functions = {
    "blink": blink,
    "boom": boom,
    "rainbow": rainbow,
    "fastbow": fastbow,
    "morse": morse,
    "identify": identify,
    "stop": stop
}
# Dict of initial states for the effect
functions_state = {
    "blink": lambda  args: random.randint(25,100)*2,
    "boom": lambda  args:10,
    "rainbow": lambda args: random.randint(0,255),
    "fastbow": lambda args: random.randint(0,255),
    "morse": lambda args: morseTranslator(" ".join(args)),
    "identify": lambda args: 4,
    "stop": lambda args: 0,
}

# Table generation string
table_sql = """CREATE TABLE if not exists "leds" (
	"id"	INTEGER NOT NULL UNIQUE,
	"owner"	TEXT UNIQUE,
	"color"	INTEGER,
	"lastSeen"	TEXT,
	PRIMARY KEY("id")
);"""
cur.execute(table_sql)
# fill db with LEDs
for id in range(1024):
    cur.execute("INSERT OR IGNORE INTO leds VALUES(?,NULL,?,?)",(id,"",""))
con.commit()

# precompiled regex for finding three integers range 0-255
regex = re.compile("^\!led ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]) ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]) ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])$")

# ???
pipeline_free=True

"""
Helper function to calculate linear array position for x,y coordinates
"""
def xy2pos(x, y, grid=32):
    return (x * grid) + y

"""
Helper function to calculate x,y position for linear array coordinates
"""
def pos2xy(pos, grid=32):
    return (int(pos/grid)+1, (pos%grid)+1)


"""
Decativated function
"""
def say_led_number(username, num):
    pass
    #client.publish("chat/whisper", payload=gen_whisper(username, "Willkommen {user} Nummer ist {num}".format(user=username, num=num)))

"""
This function sends the LED position for the username
"""
def update_led_number(username, num):
    x,y = pos2xy(num)
    mqtt_message_list.put("@{user} deine LED ist Nr. {num} und befindet sich auf {x}/{y}.".format(user=username, num=num, x=x, y=y))

"""
This function send a message @ the username
"""
def show_message(username, message):
    mqtt_message_list.put("@{user} {message}".format(user=username, message=message))


"""
This function sends help text about the fuctionality of this program
"""
def send_help(username):
    mqtt_message_list.put("@{user} du findest die LED Funktionen im Beschreibungstext.".format(user=username))
    return
    mqtt_message_list.put("!led 1-255 1-255 1-255")
    mqtt_message_list.put("!led CSS3 Name (https://www.cssportal.com/css3-color-names)")
    mqtt_message_list.put("!led #Hexwert")
    mqtt_message_list.put("!led off")
    mqtt_message_list.put("!led info|status")
    mqtt_message_list.put("!led [{commands}]".format(commands="|".join(functions.keys())))

"""
This is the MQTT sending thread

Send a message every second. If the queue is empty look again in 100ms
"""
def send_mqtt_list():
    global running
    while(running):
        if not mqtt_message_list.empty():
            payload = mqtt_message_list.get()
            mqtt_client.publish("chat/out", payload=payload)
            time.sleep(1)
        else:
            time.sleep(0.1)

"""
This function updates the LED row in the database
"""
def update_user(username, color=None, info=False):
    # 1. We get a random unassigned LED from the database.
    cur.execute("SELECT * FROM leds WHERE owner IS NULL ORDER BY RANDOM();")
    
    # 2. We try to assign the LED to the user in username. The username column is unique and if the user
    #    already has a LED assigned this will throw. We ignore the exception.
    res = cur.fetchone()
    try:
        cur.execute("UPDATE leds SET owner=? WHERE id=?",(username, res[0]))
        # User is now assigned to the LED
    except:
        # User is already assigned to a different LED
        pass


    # 3. Post the LED color and update last_seen on remote database
    data = {
        'auth': 123,
        'owner': username,
    }
    if color: 
        data.color = color
    requests.post("https://platinenmacher.tech/pcb/panel/led/"+username ,
            data=data)
    
    # 4. If a color is given (should be changed) we update the row with the color
    if(color):
        cur.execute("UPDATE leds SET lastSeen=DATETIME('now'), color=? WHERE owner=?;", (color, username))
    else:
        cur.execute("UPDATE leds SET lastSeen=DATETIME('now') WHERE owner=?;", (username,))

    # 5. If the LED info is requested we queue a message with the coordinates
    if info:
        cur.execute("SELECT id FROM leds WHERE owner=?;",(username,))
        update_led_number(username, cur.fetchone()[0])

    # 6. save database
    con.commit()
"""
This function deletes a user from the database
"""
def delete_user(username):
    # 1. Update the LED that is assigned to the user in username and remove the username
    cur.execute("UPDATE leds SET owner=NULL where owner=?;",(username,))
    con.commit()
    # 2. Send message to the user
    show_message(username, "dein Name wurde aus der LED Tabelle entfernt")


"""
This function updates the array of LED colors to be displayed on the panel
"""
def update_panel():
    global discomode
    
    # 1. clear the last frame from memory
    panel.clear()
    
    # 2. If we are in normal mode, i.e. not disco mode
    if discomode == 0:
        # open the database ???
        con = sqlite3.connect('led.db')
        cur = con.cursor()
        
        # 3. Get all LEDs that have a lastSeen from the last 4 hours
        cur.execute("SELECT * FROM leds WHERE owner IS NOT NULL AND lastSeen>DATETIME('now', '-10800 seconds');")
        for led in cur.fetchall():
            # 3.1. If the LED has a username assigned
            if(led[1]):
                # 3.2. Set the panel LED to the color in the database
                curcol = led[2]
                # 3.3. If an effect is registered for the username we execute the effect function 
                #      and update the color with the return value of the function
                if effects.get(led[1], 0):
                    curcol = effects[led[1]](led[1], curcol)
                # 3.4. Set the LED color by number
                panel.panel[led[0]]=curcol
    
    else: 
        # 4. disco mode enabled: set random color from disco_colors list to each LED
        for led in range(1024):
            panel.panel[led]=random.choice(disco_colors)
        # 4.1 reduce discomode counter so we stop the disco at 0
        discomode -=1
    
    # 5. Push the panel array data to the physical LED panel.
    panel.display()

"""
Signal handler for saving the database on closing
"""
def SignalHandler(signum, frame):
    global running
    # 1. save database
    con.commit()
    # 2. stop all threads
    running = False
    print("saved")
    # 3. bye bye
    quit()

"""
Callback on MQTT connection
"""
def on_connect(client, userdata, flags, rc):
    print("connected")

"""
Callback on MQTT message
"""
def on_message(client, userdata, msg):
    # 1. Do we have a payload?
    if not msg.payload:
        return
    # 2. Convert payload to object
    m = json.loads(msg.payload)
    try:
        # 3. Get username and message text from message object as lower case text!
        username = m.get("username").lower()
        chat_text = m.get('message').lower()
        # 4. Do we have a !led command?
        if chat_text.startswith('!led'):
            # 5. Try to find RGB numbers in message
            num = regex.findall(chat_text)
            # 6.1. update LED color of the user with colors from message
            if len(num) == 1:
                col = random.choice(disco_colors)
                print(col)
                update_user(username, col)
                return
            # 6.2. "Off" command sets color to black
            if chat_text[5:8] == "off":
                update_user(username, panel.Color(1,1,1))
                return
            # 6.3. "Info" or "Status" command prints the LED coordinates
            if chat_text[5:9] == "info" or chat_text[5:11] == "status":
                update_user(username, info=True)
                return
            # 6.4. "Random" command sets the LED to random color
            if chat_text[5:11] == "random":
                r,g,b = (random.randint(1,255), random.randint(1,255), random.randint(1,255))
                update_user(username, panel.Color(r,g,b))
                mqtt_message_list.put("@{username} deine LED leuchtet jetzt in ({r} {g} {b})RGB".format(username=m.get('username'), r=r, g=g, b=b))
                return
            # 6.5. "DSGVO" removes username assignment from LED
            if chat_text[5:10] == "dsgvo":
                delete_user(username)
                return

            # 7. Execute LED fuction
            #    !led command
            #    !led command args
            
            # 7.1. split chat_text after !led by space character
            cmd = chat_text[5:].split(" ")
            if cmd[0] in functions:
                # 7.2. update the user entry for this LED
                update_user(username)
                # 7.3. extract fuction and arguments from list
                fun = cmd[0]
                args = cmd[1:]
                print(fun, functions[fun])
                # 7.4. set initial state for the function
                state[username] = functions_state[fun](args)
                
                # 7.5. register function for username
                effects[username] = functions[fun]
                return
            
            # 7.6. Try to match the command to a CSS3 color
            try:
                col = webcolors.name_to_rgb(cmd[0])
            except:
                col = 0
            if col:
                update_user(username, panel.Color(col.red,col.green,col.blue))
                return

            # 7.7. Try to match the command to a hex color
            if chat_text[5] == "#":
                try:
                    col = webcolors.hex_to_rgb(cmd[0])
                except Exception as e:
                    show_message(username, e)
                    col = 0
                if col:
                    update_user(username, panel.Color(col.red,col.green,col.blue))
                    return

            # 8. DISCOMODE!!! for 10 runs
            if chat_text[5:10] == "disco":
                global discomode
                discomode = 10
                return

            # 9. Print help 
            if len(chat_text) == 4 or chat_text[5:9] == "help" or chat_text[5:6] == "?":
                send_help(m.get('username'))
                return

            # 10: Calculate Levenshtein distance for color if nothing matched so far
            distance = 0
            for css3_color in levenshtein.css3_colors:
                lsdist = levenshtein.levenshtein_ratio_and_distance(css3_color.lower(), cmd[0], True)
                if lsdist > distance:
                    distance = lsdist
                    col_named = css3_color
            if distance > 0.6:
                show_message(m.get('username'), "Ich habe für dich die Frabe {c} ausgesucht.".format(c=col_named))
                col = webcolors.name_to_rgb(col_named)
                update_user(username, panel.Color(col.red,col.green,col.blue))
                return
            send_help(m.get('username'))
        else:
            # 10. update user timestamp even if no !led command was issued
            update_user(username)
    except Exception as e:
        print(e)
        pass
    
"""
This function runs the panel updating
"""
def update_panel_thread():
    global running
    while(running):
        update_panel()
        if discomode == 0:
            time.sleep(0.1)
        else:
            time.sleep(1)


""" 
Main entry point of the program
"""
if __name__ == "__main__":
    # 1. Global running state for threads
    global running
    running = True
    
    # 2. Hook into SIGINT to save on closing
    signal.signal(signal.SIGINT, SignalHandler)
    
    # 3. Initialize MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # 4. Init and start MQTT sending thread
    send_queue = threading.Thread(target=send_mqtt_list)
    send_queue.start()

    # 5. Init display updating thread
    display_fred = threading.Thread(target=update_panel_thread)

    # 6. connect to MQTT broker
    mqtt_client.connect("192.168.0.11", 1883, 60)
    mqtt_client.subscribe("chat/in")

    # 7. Create LED array and initialize WS2812 LEDs
    panel.init_strip()

    # 8. Show empty panel
    panel.display()

    # 9. Start display thread
    display_fred.start()
    
    #10. process MQTT messagges
    mqtt_client.loop_forever()
