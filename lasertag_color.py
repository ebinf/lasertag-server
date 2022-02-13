#!/usr/bin/python3
import time
import traceback
import paho.mqtt.client as mqtt
import threading
import json
import urllib.request
import eel
import os
import importlib
from random import randrange

##### CONFIGURATION #####
host = "192.168.178.50"
port = 1883
timeouttime = 10
####### DEFAULTS ########
std_teams = 2
std_reactivationtime = 6
std_hits_to_kill = 1
std_lives = -1
std_ammunition = -1
std_gametime = 300
std_pointsforkill = 100
std_pointsfordeath = 0
std_firerate = 0
std_friendlyfire = True
std_friendlykill = 100
std_friendlydeath = 50
std_friendlydeactivate = True
std_friendlysuicide = False
std_friendlycombo = False
std_randomizeteams = False
#########################

waistcoats = set()
a_teams = {}
a_waistcoats = {}
i_waistcoats = {}
referees = {}
gamestate = 0
teams = std_teams
reactivationtime = std_reactivationtime
hits_to_kill = std_hits_to_kill
lives = std_lives
ammunition = std_ammunition
gametime = std_gametime
pointsforkill = std_pointsforkill
pointsfordeath = std_pointsfordeath
firerate = std_firerate
friendlyfire = std_friendlyfire
friendlykill = std_friendlykill
friendlydeath = std_friendlydeath
friendlydeactivate = std_friendlydeactivate
friendlysuicide = std_friendlysuicide
friendlycombo = std_friendlycombo
randomizeteams = std_randomizeteams
client = mqtt.Client("brain")
gamemodes = {}
variations = {}
std_refereemodes = {
    "activate": "0F0",
    "deactivate": "F00",
    "changeteam": "00F",
    "startstopgame": "FF0"
}
refereemodes = std_refereemodes
hooks = False
with open("colors.json", "r") as file:
    colors = json.load(file)
with open("nicknames.json", "r") as file:
    nicknames = json.load(file)
for gamemode in sorted(os.listdir("gamemodes")):
    if (os.path.isdir("gamemodes/" + gamemode) and os.path.isfile("gamemodes/" + gamemode + "/settings.json")):
        with open("gamemodes/" + gamemode + "/settings.json", "r") as file:
            gamemodes[gamemode] = json.load(file)

def hook(name, *args, **kwargs):
    global hooks
    if (hooks and name in dir(hooks)):
        th = threading.Thread(target=getattr(hooks, name), args=(globals(), *args), kwargs={**kwargs}, daemon=False)
        th.start()
        return True
    return False

def IntToHex(inp):
    hexint = str(hex(inp))[2:].upper()
    if (hexint[:1] == "X"):
            return "-" + hexint[1:]
    return hexint

def on_connect(client, userdata, flags, rc):
    client.subscribe("waistcoat/hello")
    client.subscribe("waistcoat/bye")
    client.subscribe("waistcoat/#")
    client.publish("arena/state", "0")
    client.publish("waistcoat/ping", "are u there?", 2)

def on_message(client, userdata, msg):
    try:
        message = msg.payload.decode("utf-8")
        topic = msg.topic
        if (topic[:10] == "waistcoat/"):
            topic = topic[9:]
            hook("pre_message", topic, message)
            if (topic == "/hello"):
                py_waistcoatOnline(message)
            elif (topic == "/bye"):
                py_waistcoatOffline(message)
            elif (topic[5:] == "/hit" and (gamestate == 2 or message in referees)):
                py_hit(topic[1:5], message)
            elif (topic[5:] == "/aclives" and gamestate == 2):
                py_aclives(topic[1:5], message)
            elif (topic[5:] == "/acammunition" and gamestate == 2):
                py_acammunition(topic[1:5], message)
            elif (topic[5:] == "/acpowerups" and gamestate == 2):
                py_acpowerups(topic[1:5], message)
            elif (topic[5:] == "/specialbutton" and (gamestate == 2 or topic[1:5] in referees)):
                py_specialbutton(topic[1:5], int(message))
            elif (topic[5:] == "/membercard" and gamestate == 1):
                py_membercard(topic[1:5], message)
            hook("post_message", topic, message)
    except:
        print(traceback.print_exc())

def timeout():
    global client, gamestate
    running = 0
    initial = False
    while (gamestate == 0):
        running += 1
        if ((not initial and running >= timeouttime) or (initial and running >= 10)):
            initial = True
            client.publish("arena/color/mode", "6")
            running = 0
        time.sleep(1)
    client.publish("arena/color/mode", "0")

def tick():
    global gametime, gamestate
    running = gametime + 1
    while (gamestate == 2):
        running -= 1
        eel.py_gameTime(running)
        hook("tick")
        if (running <= 0):
            print("Game time ran out. Game stopped.")
            py_stop()
            return
        time.sleep(1)

def getNickname(waistcoat):
    global nicknames
    if (waistcoat in nicknames):
        return nicknames[waistcoat]
    return (nicknames["replacement"] % waistcoat)

def py_assignToTeam(waistcoat, team=-1, force=False):
    try:
        global client, gamestate, teams, a_teams, a_waistcoats, i_waistcoats, randomizeteams
        if hook("replace_assignToTeam", waistcoat, team, force):
            return
        hook("pre_assignToTeam", waistcoat, team, force)
        if (gamestate == 1 or force):
            if (team == -1 or team > teams):
                minwc = -1
                team = -1
                rndteams = []
                for i in range(1, teams + 1):
                    if (len(a_teams[i]["waistcoats"]) < minwc or minwc == -1):
                        minwc = len(a_teams[i]["waistcoats"])
                        team = i
                if (randomizeteams):
                    for i in range(1, teams + 1):
                        if (len(a_teams[i]["waistcoats"]) == minwc):
                            rndteams.append(i)
                    team = rndteams[randrange(0, len(rndteams))]
            client.publish("waistcoat/" + waistcoat + "/color/all", a_teams[team]["color"], 2)
            a_teams[team]["waistcoats"].add(waistcoat)
            activated = False
            if (waistcoat in a_waistcoats):
                activated = True
                if (a_waistcoats[waistcoat]["team"] > 0 and a_waistcoats[waistcoat]["team"] <= teams and a_waistcoats[waistcoat]["team"] != team):
                    a_teams[a_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
                a_waistcoats[waistcoat]["team"] = team
            elif (waistcoat in i_waistcoats):
                if (i_waistcoats[waistcoat]["team"] > 0 and i_waistcoats[waistcoat]["team"] <= teams and i_waistcoats[waistcoat]["team"] != team):
                    a_teams[i_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
                i_waistcoats[waistcoat]["team"] = team
            client.publish("waistcoat/" + waistcoat + "/team", IntToHex(team), 2)
            print("Assigned " + waistcoat + " to team " + str(team) + ".")
            eel.py_changeTeam(waistcoat, team, activated)
        hook("post_assignToTeam", waistcoat, team, force)
    except:
        print(traceback.print_exc())

def py_assignAll(force=False):
    try:
        global gamestate, waistcoats, a_waistcoats, i_waistcoats, teams
        if hook("replace_assignAll", force):
            return
        hook("pre_assignAll", force)
        if (gamestate == 1 or force):
            for team in a_teams:
                a_teams[team]["waistcoats"] = set()
            if (gamestate == 1):
                for waistcoat in waistcoats:
                    if (waistcoat in referees):
                        eel.py_changeTeam(waistcoat, 0, True)
                    else:
                        py_assignToTeam(waistcoat)
            else:
                for waistcoat in referees:
                    eel.py_changeTeam(waistcoat, 0, True)
                for waistcoat in a_waistcoats:
                    py_assignToTeam(waistcoat, force=True)
                for waistcoat in i_waistcoats:
                    if ("team" not in i_waistcoats[waistcoat] or i_waistcoats[waistcoat]["team"] <= 0 or i_waistcoats[waistcoat]["team"] > teams):
                        py_assignToTeam(waistcoat, force=True)
                        client.publish("waistcoat/" + waistcoat + "/color/all", "000")
        hook("post_assignAll", force)
    except:
        print(traceback.print_exc())

def py_teamAmount(amount, noreassign=False):
    try:
        global colors, teams, a_teams, a_waistcoats, i_waistcoats
        if (amount <= 0):
            return
        if (amount > 10):
            amount = 10
        hook("pre_teamAmount", amount)
        new_a_teams = {}
        payload = []
        for i in range(1, amount + 1):
            colorid = i - 1
            teamname = "Team " + colors[colorid]["name"]
            if (i <= len(a_teams)):
                if ("colorid" in a_teams[i]):
                    colorid = a_teams[i]["colorid"]
                    teamname = "Team " + colors[colorid]["name"]
                if ("name" in a_teams[i]):
                    teamname = a_teams[i]["name"]
            new_a_teams[i] = {
                "name": teamname,
                "points": 0,
                "waistcoats": set(),
                "color": colors[colorid]["waistcoat"]
            }
            payload.append({
                "name": teamname,
                "color": colors[colorid]["config"]
            })
        teams = amount
        a_teams = new_a_teams
        gamestate = 1
        eel.py_teamAmount(teams, payload)
        if (noreassign):
            for waistcoat in referees:
                eel.py_changeTeam(waistcoat, 0, True)
            for waistcoat in i_waistcoats:
                eel.py_changeTeam(waistcoat, i_waistcoats[waistcoat]["team"], False)
            for waistcoat in a_waistcoats:
                eel.py_changeTeam(waistcoat, a_waistcoats[waistcoat]["team"], True)
        else:
            for waistcoat in a_waistcoats:
                if ("membercard" in a_waistcoats[waistcoat]):
                    del a_waistcoats[waistcoat]["membercard"]
                a_waistcoats[waistcoat]["nickname"] = getNickname(waistcoat)
                i_waistcoats[waistcoat] = a_waistcoats[waistcoat]
            a_waistcoats = {}
            py_assignAll(True)
        hook("post_teamAmount", amount)
    except:
        print(traceback.print_exc())

def py_waistcoatOnline(waistcoat):
    try:
        global waistcoats, a_waistcoats, gamestate, i_waistcoats, referees, refereemodes, a_teams
        hook("pre_waistcoatOnline", waistcoat)
        if (waistcoat not in waistcoats):
            print("Waistcoat " + waistcoat + " connected.")
            waistcoats.add(waistcoat)
            client.publish("waistcoat/" + waistcoat + "/color/all", "000", 2)
            i_waistcoats[waistcoat] = {"team": -1, "nickname": getNickname(waistcoat)}
            if (gamestate == 1):
                py_assignToTeam(waistcoat)
            else:
                client.publish("waistcoat/" + waistcoat + "/color/mode", "0", 2)
            eel.py_waistcoatOnline(waistcoat, i_waistcoats[waistcoat]["nickname"], i_waistcoats[waistcoat]["team"])
        elif (gamestate == 2):
            if (waistcoat in a_waistcoats):
                entry = a_waistcoats[waistcoat]
                print("Waistcoat " + waistcoat + " reconnected.")
                client.publish("waistcoat/" + waistcoat + "/color/all", str(a_teams[entry["team"]]["color"]), 2)
                client.publish("waistcoat/" + waistcoat + "/team", str(entry["team"] + 1), 2)
                client.publish("waistcoat/" + waistcoat + "/state", "1", 2)
                client.publish("waistcoat/" + waistcoat + "/state", "2", 2)
                client.publish("waistcoat/" + waistcoat + "/reactivationtime", IntToHex(reactivationtime), 2)
                client.publish("waistcoat/" + waistcoat + "/hitstokill", IntToHex(hits_to_kill), 2)
                client.publish("waistcoat/" + waistcoat + "/ammunition", IntToHex(entry["ammunition"]), 2)
                client.publish("waistcoat/" + waistcoat + "/lives", IntToHex(entry["lives"]), 2)
                client.publish("waistcoat/" + waistcoat + "/firerate", IntToHex(firerate), 2)
                client.publish("waistcoat/" + waistcoat + "/friendlyfire", int(friendlyfire), 2)
                client.publish("waistcoat/" + waistcoat + "/friendlydeactivate", int(friendlydeactivate), 2)
                eel.py_waistcoatReconnected(waistcoat)
            elif (waistcoat in referees):
                print("Waistcoat " + waistcoat + " reconnected.")
                client.publish("waistcoat/" + waistcoat + "/color/all", "FFF", 2)
                client.publish("waistcoat/" + waistcoat + "/color/3", refereemodes[referees[waistcoat]["mode"]], 2)
                client.publish("waistcoat/" + waistcoat + "/team", 0, 2)
                client.publish("waistcoat/" + waistcoat + "/state", "1", 2)
                client.publish("waistcoat/" + waistcoat + "/state", "2", 2)
                client.publish("waistcoat/" + waistcoat + "/color/mode", "0", 2)
        hook("post_waistcoatOnline", waistcoat)
    except:
        print(traceback.print_exc())

def py_waistcoatOffline(waistcoat):
    try:
        global a_waistcoats, gamestate, waistcoats, a_teams, i_waistcoats
        hook("pre_waistcoatOffline", waistcoat)
        if (waistcoat in waistcoats):
            print("Waistcoat " + waistcoat + " disconnected.")
            if (gamestate == 0 or gamestate == 1):
                waistcoats.remove(waistcoat)
                if (gamestate == 1):
                    if (waistcoat in a_waistcoats):
                        a_teams[a_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
                        del a_waistcoats[waistcoat]
                    elif (waistcoat in referees):
                        del referees[waistcoat]
                    else:
                        a_teams[i_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
                        del i_waistcoats[waistcoat]
                eel.py_waistcoatOffline(waistcoat)
            elif (gamestate == 2):
                eel.py_waistcoatInactive(waistcoat)
        hook("post_waistcoatOffline", waistcoat)
    except:
        print(traceback.print_exc())

def py_membercard(waistcoat, membercard):
    try:
        global a_waistcoats, i_waistcoats
        hook("pre_membercard", waistcoat, membercard)
        if (waistcoat in i_waistcoats):
            for iwaistcoat in a_waistcoats:
                if ("membercard" in a_waistcoats[iwaistcoat] and a_waistcoats[iwaistcoat]["membercard"] == membercard):
                    return
            request = urllib.request.Request('https://lasertag.ebinf.eu/api/membercard.php', headers={'content-type': 'application/json'}, data=json.dumps({'card': membercard}).encode('utf-8'))
            try:
                with urllib.request.urlopen(request) as response:
                    data = json.loads(response.read())
                    if (data["status"] == "found"):
                        client.publish("waistcoat/" + waistcoat + "/state", "1", 2)
                        i_waistcoats[waistcoat]["membercard"] = str(membercard)
                        i_waistcoats[waistcoat]["nickname"] = str(data["nickname"])
                        eel.py_activate(waistcoat, i_waistcoats[waistcoat]["team"], i_waistcoats[waistcoat]["nickname"])
                        a_waistcoats[waistcoat] = i_waistcoats[waistcoat]
                        del i_waistcoats[waistcoat]
                        print("Waistcoat " + waistcoat + " was activated with membercard " + str(membercard) + " aka " + str(data["nickname"])  + ".")
            except urllib.request.HTTPError as e:
                return
        hook("post_membercard", waistcoat, membercard)
    except:
        print(traceback.print_exc())

def py_start(countdown=0):
    try:
        global gamestate, a_waistcoats, ammunition, lives, reactivationtime, hits_to_kill,\
        firerate, friendlyfire, friendlydeactivate, client, i_waistcoats
        hook("pre_start", countdown)
        if (gamestate == 1):
            for waistcoat in a_waistcoats:
                a_waistcoats[waistcoat]["points"] = 0
                a_waistcoats[waistcoat]["combo"] = 0
                a_waistcoats[waistcoat]["ammunition"] = ammunition
                a_waistcoats[waistcoat]["lives"] = lives
                a_waistcoats[waistcoat]["powerups"] = set()
            for waistcoat in i_waistcoats:
                a_teams[i_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
                client.publish("waistcoat/" + waistcoat + "/state", "0", 2)
            for waistcoat in referees:
                if (referees[waistcoat]["mode"] == "startgame"):
                    referees[waistcoat]["mode"] = "stopgame"
                    client.publish("waistcoat/" + waistcoat + "/color/3", "0FF", 2)
            client.publish("game/reactivationtime", IntToHex(reactivationtime), 2)
            client.publish("game/hitstokill", IntToHex(hits_to_kill), 2)
            client.publish("game/ammunition", IntToHex(ammunition), 2)
            client.publish("game/lives", IntToHex(lives), 2)
            client.publish("game/firerate", IntToHex(firerate), 2)
            client.publish("game/friendlyfire", int(friendlyfire), 2)
            client.publish("game/friendlydeactivate", int(friendlydeactivate), 2)
            while (countdown > 0):
                eel.py_gameTime(countdown)
                countdown -= 1
                time.sleep(1)
            gamestate = 2
            client.publish("game/state", "2", 2)
            timer = threading.Thread(target=tick, daemon=True)
            timer.start()
            print("Game started.")
        hook("post_start", countdown)
    except:
        print(traceback.print_exc())

def py_stop():
    try:
        global client, a_teams, colors, waistcoats, a_waistcoats, i_waistcoats, gamestate, hooks, referees
        hook("pre_stop")
        client.publish("arena/state", "0", 2)
        gamestate = 0
        print(a_teams)
        print()
        print(a_waistcoats)
        a_teams = {}
        a_waistcoats = {}
        i_waistcoats = {}
        referees = {}
        teams = 0
        waistcoats = set()
        timerout = threading.Thread(target=timeout, daemon=True)
        timerout.start()
        hook("post_stop")
        eel.py_clear()
        hooks = False
        client.publish("waistcoat/ping", "are you there?", 2)
        eel.py_load(False)
    except:
        print(traceback.print_exc())

def py_hit(waistcoat, by):
    try:
        global a_waistcoats, pointsforkill, pointsfordeath, friendlyfire, friendlykill,\
        friendlydeath, friendlysuicide, friendlycombo, teams
        hook("pre_hit", waistcoat, by)
        print()
        if (by in referees):
            if (referees[by]["mode"] == "deactivate" and waistcoat in a_waistcoats):
                js_deactivate(waistcoat)
                eel.py_changeTeam(waistcoat, i_waistcoats[waistcoat]["team"], False)
            elif (referees[by]["mode"] == "activate" and waistcoat in i_waistcoats):
                js_activate(waistcoat)
                eel.py_changeTeam(waistcoat, a_waistcoats[waistcoat]["team"], True)
            elif (referees[by]["mode"] == "changeteam"):
                if (waistcoat in a_waistcoats):
                    entry = a_waistcoats[waistcoat]
                else:
                    entry = i_waistcoats[waistcoat]
                newteam = entry["team"] + 1
                if (newteam > teams):
                    newteam = 1
                js_changeTeam(waistcoat, newteam)
                eel.py_changeTeam(waistcoat, newteam, (waistcoat in a_waistcoats))
        elif (waistcoat in a_waistcoats and by in a_waistcoats):
            print("%s hits %s." % (by, waistcoat))
            multiply = 1
            if ("2xmultiplier" in a_waistcoats[by]["powerups"]):
                multiply = 2
            if (a_waistcoats[by]["team"] != a_waistcoats[waistcoat]["team"]):
                a_teams[a_waistcoats[by]["team"]]["points"] += pointsforkill * multiply
                a_waistcoats[by]["points"] += pointsforkill * multiply
                a_waistcoats[by]["combo"] += 1
                if ("invulnerability" not in a_waistcoats[waistcoat]["powerups"]):
                    a_waistcoats[waistcoat]["points"] -= pointsfordeath
                    a_teams[a_waistcoats[waistcoat]["team"]]["points"] -= pointsfordeath
                    a_waistcoats[waistcoat]["combo"] = 0
            elif (not friendlyfire):
                if (friendlycombo and not friendlysuicide):
                    a_waistcoats[by]["points"] -= friendlykill
                    a_teams[a_waistcoats[by]["team"]]["points"] -= friendlykill
                    a_waistcoats[by]["combo"] += 1
                else:
                    a_waistcoats[by]["points"] -= friendlykill * multiply
                    a_teams[a_waistcoats[by]["team"]]["points"] -= friendlykill * multiply
                    a_waistcoats[by]["combo"] = 0
                if ("invulnerability" not in a_waistcoats[waistcoat]["powerups"]):
                    a_waistcoats[waistcoat]["points"] -= friendlydeath
                    a_teams[a_waistcoats[waistcoat]["team"]]["points"] -= friendlydeath
                    a_waistcoats[waistcoat]["combo"] = 0
                if (friendlysuicide):
                    client.publish("waistcoat/" + by + "/state", "3", 2)
        hook("post_hit", waistcoat, by)
    except:
        print(traceback.print_exc())

def py_aclives(waistcoat, lives):
    try:
        global a_waistcoats
        hook("pre_aclives", waistcoat, lives)
        if (waistcoat in a_waistcoats):
            a_waistcoats[waistcoat]["lives"] = int(lives)
        hook("post_aclives", waistcoat, lives)
    except:
        print(traceback.print_exc())

def py_acammunition(waistcoat, ammunition):
    try:
        global a_waistcoats
        hook("pre_acammunition", waistcoat, ammunition)
        if (waistcoat in a_waistcoats):
            a_waistcoats[waistcoat]["ammunition"] = int(ammunition)
        hook("post_acammunition", waistcoat, ammunition)
    except:
        print(traceback.print_exc())

def py_acpowerups(waistcoat, powerup):
    try:
        global a_waistcoats
        hook("pre_acpowerups", waistcoat, powerup)
        if (waistcoat in a_waistcoats):
            a_waistcoats[waistcoat]["powerups"].discard(powerup)
            if (powerup == "all"):
                a_waistcoats[waistcoat]["powerups"] = set()
            print("Waistcoat %s lost powerup %s." % (waistcoat, powerup))
        hook("post_acpowerups", waistcoat, powerup)
    except:
        print(traceback.print_exc())

def py_specialbutton(waistcoat, seconds=0):
    try:
        global a_waistcoats, referees, gamestate, refereemodes
        hook("pre_specialbutton", waistcoat)
        if (waistcoat in referees):
            if (seconds < 3):
                newmode = list(refereemodes.keys()).index(referees[waistcoat]["mode"]) + 1
                if (newmode >= len(refereemodes)):
                    newmode = 0
                referees[waistcoat]["mode"] = list(refereemodes.keys())[newmode]
                client.publish("waistcoat/" + waistcoat + "/color/3", refereemodes[referees[waistcoat]["mode"]], 2)
                print("Changed mode of referee %s to %s." % (waistcoat, referees[waistcoat]["mode"]))
            else:
                if (referees[waistcoat]["mode"] == "startstopgame"):
                    if (gamestate == 1):
                        print("Referee %s started the game." % waistcoat)
                        py_start(0)
                        eel.py_gameStart()
                    elif (gamestate == 2):
                        print("Referee %s stopped the game." % waistcoat)
                        py_stop()
                hook("referee_specialbutton", waistcoat)
        elif (waistcoat in a_waistcoats):
            if hook("replace_specialbutton", waistcoat):
                return
            print("Waistcoat %s pressed special button for %i seconds." % (waistcoat, seconds))
        hook("post_specialbutton", waistcoat)
    except:
        print(traceback.print_exc())

def py_applyGamemode(gamemode):
    try:
        global a_teams, gametime, reactivationtime, lives, ammunition, pointsforkill,\
        pointsfordeath, firerate, friendlyfire, friendlykill, friendlydeath, friendlysuicide,\
        friendlydeactivate, friendlycombo, randomizeteams, refereemodes, std_refereemodes
        disableTeamAmount = -1
        disableTeamNames = -1
        if ("teams" in gamemode):
            disableTeamAmount = True
            disableTeamNames = False
            if (isinstance(gamemode["teams"], int)):
                a_teams = {i: {} for i in range(1, gamemode["teams"] + 1)}
            else:
                a_teams = {i: {} for i in range(1, len(gamemode["teams"]) + 1)}
                for team in range(len(gamemode["teams"])):
                    if "name" in gamemode["teams"][team]:
                        disableTeamNames = True
                        a_teams[team + 1]["name"] = gamemode["teams"][team]["name"]
                    if "color" in gamemode["teams"][team]:
                        a_teams[team + 1]["colorid"] = gamemode["teams"][team]["color"]
        if ("gametime" in gamemode):
            gametime = gamemode["gametime"]
        if ("firerate" in gamemode):
            firerate = gamemode["firerate"]
        if ("pointsforkill" in gamemode):
            pointsforkill = gamemode["pointsforkill"]
        if ("pointsfordeath" in gamemode):
            pointsfordeath = gamemode["pointsfordeath"]
        if ("hitstokill" in gamemode):
            hits_to_kill = gamemode["hitstokill"]
        if ("reactivationtime" in gamemode):
            reactivationtime = gamemode["reactivationtime"]
        if ("randomizeteams" in gamemode):
            randomizeteams = gamemode["randomizeteams"]
        if ("lives" in gamemode):
            if (isinstance(gamemode["lives"], bool) and gamemode["lives"] == False):
                lives = -1
            else:
                lives = gamemode["lives"]
        if ("ammunition" in gamemode):
            if (isinstance(gamemode["ammunition"], bool) and gamemode["ammunition"] == False):
                ammunition = -1
            else:
                ammunition = gamemode["ammunition"]
        if ("refereemodes" in gamemode):
            refereemodes = {**std_refereemodes, **gamemode["refereemodes"]}
        if ("friendlyfire" in gamemode):
            if (isinstance(gamemode["friendlyfire"], bool)):
                friendlyfire = gamemode["friendlyfire"]
            else:
                if ("friendlyfire" in gamemode["friendlyfire"]):
                    friendlyfire = gamemode["friendlyfire"]["friendlyfire"]
                if ("friendlydeactivate" in gamemode["friendlyfire"]):
                    friendlydeactivate = gamemode["friendlyfire"]["friendlydeactivate"]
                if ("friendlysuicide" in gamemode["friendlyfire"]):
                    friendlysuicide = gamemode["friendlyfire"]["friendlysuicide"]
                if ("friendlykill" in gamemode["friendlyfire"]):
                    friendlykill = gamemode["friendlyfire"]["friendlykill"]
                if ("friendlydeath" in gamemode["friendlyfire"]):
                    friendlydeath = gamemode["friendlyfire"]["friendlydeath"]
                if ("friendlycombo" in gamemode["friendlyfire"]):
                    friendlycombo = gamemode["friendlyfire"]["friendlycombo"]
        return disableTeamAmount, disableTeamNames
    except:
        print(traceback.print_exc())

@eel.expose
def js_init():
    try:
        global waistcoats, gamemodes
        for waistcoat in waistcoats:
            eel.py_waistcoatOnline(waistcoat, getNickname(waistcoat), -1)
        eel.py_init({gamemode: gamemodes[gamemode]["name"] for gamemode in gamemodes})
        eel.py_load(False)
    except:
        print(traceback.print_exc())

@eel.expose
def js_gameMode(gamemode, variation=False):
    try:
        global gamestate, a_waistcoats, i_waistcoats, a_teams, gametime, reactivationtime, lives,\
        ammunition, pointsforkill, pointsfordeath, firerate, friendlyfire, friendlykill,\
        friendlydeath, friendlysuicide, friendlydeactivate, std_hits_to_kill, std_reactivationtime,\
        std_lives, std_ammunition, std_gametime, std_pointsforkill, std_pointsfordeath,\
        std_firerate, std_friendlyfire, std_friendlykill,std_friendlydeath, std_friendlydeactivate,\
        std_friendlysuicide, friendlycombo, std_friendlycombo, gamemodes, variations, hooks,\
        randomizeteams, std_randomizeteams, referees, refereemodes, std_refereemodes
        if (gamemode in gamemodes):
            eel.py_clear(True)
            client.publish("game/state", "0", True)
            disableTeamNames = False
            disableTeamAmount = False
            variations = {}
            if (os.path.isdir("gamemodes/" + gamemode + "/variations")):
                for ivariation in sorted(os.listdir("gamemodes/" + gamemode + "/variations")):
                    if (os.path.isdir("gamemodes/" + gamemode + "/variations/" + ivariation) and os.path.isfile("gamemodes/" + gamemode + "/variations/" + ivariation + "/settings.json")):
                        with open("gamemodes/" + gamemode + "/variations/" + ivariation + "/settings.json", "r") as file:
                            variations[ivariation] = json.load(file)
            gm = gamemode
            gamemode = gamemodes[gamemode]
            standard = ("no_standard" not in gamemode)
            a_teams = {i: {} for i in range(1, std_teams + 1)}
            reactivationtime = std_reactivationtime
            hits_to_kill = std_hits_to_kill
            lives = std_lives
            ammunition = std_ammunition
            gametime = std_gametime
            pointsforkill = std_pointsforkill
            pointsfordeath = std_pointsfordeath
            firerate = std_firerate
            friendlyfire = std_friendlyfire
            friendlykill = std_friendlykill
            friendlydeath = std_friendlydeath
            friendlydeactivate = std_friendlydeactivate
            friendlysuicide = std_friendlysuicide
            friendlycombo = std_friendlycombo
            randomizeteams = std_randomizeteams
            refereemodes = std_refereemodes
            a_waistcoats = {}
            i_waistcoats = {i: {"nickname": getNickname(i), "team": -1} for i in waistcoats}
            referees = {}
            hooks = False
            if (os.path.isfile("gamemodes/" + gm + "/hooks.py")):
                hooks = importlib.import_module("gamemodes." + gm + ".hooks")
            dta, dtn = py_applyGamemode(gamemode)
            if (dta >= 0):
                disableTeamAmount = dta
            if (dtn >= 0):
                disableTeamNames = dtn
            if (len(variations) > 0):
                dta = -1
                dtn = -1
                if (variation in variations):
                    dta, dtn = py_applyGamemode(variations[variation])
                    if (os.path.isfile("gamemodes/" + gm + "/variations/" + variation + "/hooks.py")):
                        hooks = importlib.import_module("gamemodes." + gm + ".variations." + variation + ".hooks")
                        importlib.reload(hooks)
                elif (isinstance(variation, bool) and variation == False and standard == False):
                    dta, dtn = py_applyGamemode(variations[list(variations)[0]])
                    if (os.path.isfile("gamemodes/" + gm + "/variations/" + list(variations)[0] + "/hooks.py")):
                        hooks = importlib.import_module("gamemodes." + gm + ".variations." + variation + ".hooks")
                        importlib.reload(hooks)
                if (dta >= 0):
                    disableTeamAmount = dta
                if (dtn >= 0):
                    disableTeamNames = dtn
            gamestate = 1
            if (isinstance(variation, bool) and variation == False):
                eel.py_gameMode({ivariation: variations[ivariation]["name"] for ivariation in variations}, standard)
            eel.py_variation(disableTeamAmount, disableTeamNames)
            py_teamAmount(len(a_teams))
            eel.py_gameTime(gametime)
            hook("init")
        else:
            eel.py_clear()
        eel.py_load(False)
    except:
        print(traceback.print_exc())

@eel.expose
def js_teamAmount(amount):
    py_teamAmount(amount)
    print("Changed team amount to " + str(teams))

@eel.expose
def js_teamName(team, name):
    a_teams[team]["name"] = name
    print("Changed team " + str(team) + "'s name to \"" + name + "\".")

@eel.expose
def js_changeTeam(waistcoat, team):
    try:
        global client, a_teams, a_waistcoats, i_waistcoats, referees
        team = int(team)
        client.publish("waistcoat/" + waistcoat + "/team", IntToHex(team), 2)
        if (team == 0):
            client.publish("waistcoat/" + waistcoat + "/color/all", "FFF", 2)
            client.publish("waistcoat/" + waistcoat + "/color/mode", "0", 2)
            client.publish("waistcoat/" + waistcoat + "/state", "1", 2)
            client.publish("waistcoat/" + waistcoat + "/state", "2", 2)
            if (gamestate == 2):
                referees[waistcoat] = {"mode": "deactivate"}
                client.publish("waistcoat/" + waistcoat + "/color/3", "F00", 2)
            else:
                referees[waistcoat] = {"mode": "activate"}
                client.publish("waistcoat/" + waistcoat + "/color/3", "0F0", 2)
        else:
            a_teams[team]["waistcoats"].add(waistcoat)
            client.publish("waistcoat/" + waistcoat + "/color/all", a_teams[team]["color"], 2)
            if (waistcoat in referees):
                a_waistcoats[waistcoat] = {"nickname": referees[waistcoat]["nickname"], "team": team}
                if ("membercard" in referees[waistcoat]):
                    a_waistcoats[waistcoat]["membercard"] = referees[waistcoat]["membercard"]
                if (gamestate == 1):
                    client.publish("waistcoat/" + waistcoat + "/color/mode", "1", 2)
                    client.publish("waistcoat/" + waistcoat + "/state", "1", 2)
                elif (gamestate == 2):
                    client.publish("waistcoat/" + waistcoat + "/state", "2", 2)
                    a_waistcoats[waistcoat]["points"] = 0
                    a_waistcoats[waistcoat]["combo"] = 0
                    a_waistcoats[waistcoat]["ammunition"] = ammunition
                    a_waistcoats[waistcoat]["lives"] = lives
                    a_waistcoats[waistcoat]["powerups"] = set()
                del referees[waistcoat]
        if (waistcoat in a_waistcoats):
            a_teams[a_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
            if (team == 0):
                if ("membercard" in a_waistcoats[waistcoat]):
                    referees[waistcoat]["membercard"] = a_waistcoats[waistcoat]["membercard"]
                referees[waistcoat]["nickname"] = a_waistcoats[waistcoat]["nickname"]
                del a_waistcoats[waistcoat]
            else:
                a_waistcoats[waistcoat]["team"] = team
        else:
            a_teams[i_waistcoats[waistcoat]["team"]]["waistcoats"].discard(waistcoat)
            if (team == 0):
                if ("membercard" in i_waistcoats[waistcoat]):
                    referees[waistcoat]["membercard"] = i_waistcoats[waistcoat]["membercard"]
                referees[waistcoat]["nickname"] = i_waistcoats[waistcoat]["nickname"]
                del i_waistcoats[waistcoat]
            else:
                i_waistcoats[waistcoat]["team"] = team
                if (gamestate == 2):
                    client.publish("waistcoat/" + waistcoat + "/color/all", "000", 2)
        print("Assign of " + waistcoat + " changed to team " + str(team) + ".")
    except:
        print(traceback.print_exc())

@eel.expose
def js_activate(waistcoat):
    try:
        global client, a_waistcoats, i_waistcoats
        if (waistcoat in i_waistcoats):
            a_waistcoats[waistcoat] = i_waistcoats[waistcoat]
            del i_waistcoats[waistcoat]
            client.publish("waistcoat/" + waistcoat + "/team", a_waistcoats[waistcoat]["team"], 2)
            client.publish("waistcoat/" + waistcoat + "/color/all", a_teams[a_waistcoats[waistcoat]["team"]]["color"], 2)
            client.publish("waistcoat/" + waistcoat + "/state", "1", 2)
            if (gamestate == 2):
                client.publish("waistcoat/" + waistcoat + "/state", "2", 2)
                a_waistcoats[waistcoat]["points"] = 0
                a_waistcoats[waistcoat]["combo"] = 0
                a_waistcoats[waistcoat]["ammunition"] = ammunition
                a_waistcoats[waistcoat]["lives"] = lives
                a_waistcoats[waistcoat]["powerups"] = set()
                a_teams[a_waistcoats[waistcoat]["team"]]["waistcoats"].add(waistcoat)
    except:
        print(traceback.print_exc())

@eel.expose
def js_deactivate(waistcoat):
    try:
        global client, a_waistcoats, i_waistcoats
        if (waistcoat in a_waistcoats):
            client.publish("waistcoat/" + waistcoat + "/state", "0", 2)
            if (gamestate == 1):
                client.publish("waistcoat/" + waistcoat + "/team", IntToHex(a_waistcoats[waistcoat]["team"]), 2)
                client.publish("waistcoat/" + waistcoat + "/color/all", a_teams[a_waistcoats[waistcoat]["team"]]["color"], 2)
                client.publish("waistcoat/" + waistcoat + "/color/mode", "0", 2)
                a_waistcoats[waistcoat]["nickname"] = getNickname(waistcoat)
            if ("membercard" in a_waistcoats[waistcoat]):
                del a_waistcoats[waistcoat]["membercard"]
            i_waistcoats[waistcoat] = a_waistcoats[waistcoat]
            del a_waistcoats[waistcoat]
            return i_waistcoats[waistcoat]["nickname"]
    except:
        print(traceback.print_exc())

@eel.expose
def js_start(countdown=0):
    py_start(countdown)

@eel.expose
def js_stop():
    py_stop()

@eel.expose
def js_gameTime(seconds):
    global gametime
    gametime = int(seconds)

@eel.expose
def js_clear():
    try:
        global gamestate, a_teams, a_waistcoats, i_waistcoats, waistcoats, hooks
        client.publish("arena/state", "0", 2)
        gamestate = 0
        a_teams = {}
        a_waistcoats = {}
        i_waistcoats = {}
        waistcoats = set()
        teams = 0
        hooks = False
        eel.py_clear()
        client.publish("waistcoat/ping", "are you there?", 2)
        timerout = threading.Thread(target=timeout, daemon=True)
        timerout.start()
        eel.py_load(False)
        js_init()
    except:
        print(traceback.print_exc())

client.on_connect = on_connect
client.on_message = on_message
client.connect(host, port, 60)

client.loop_start()

timerout = threading.Thread(target=timeout, daemon=True)
timerout.start()

eel.init("web")
eel.start("index.html")
