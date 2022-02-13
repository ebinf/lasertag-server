import time
from random import randrange
import inspect
import traceback
dracula = -1

def replace_assignAll(instance, force):
    try:
        global dracula
        instance["a_teams"][1]["waistcoats"] = set()
        instance["a_teams"][2]["waistcoats"] = set()
        activeWaistcoats = list(instance["a_waistcoats"].keys())
        if (instance["gamestate"] == 1):
            activeWaistcoats += list(instance["i_waistcoats"].keys())
        if (dracula == -1):
            dracula = randrange(0, len(activeWaistcoats))
        instance["client"].publish("game/ammunition", instance["IntToHex"](instance["ammunition"]), 2)
        instance["client"].publish("game/lives", instance["IntToHex"](instance["lives"]), 2)
        instance["py_assignToTeam"](activeWaistcoats[dracula], 1, True)
        del activeWaistcoats[dracula]
        for waistcoat in activeWaistcoats:
            instance["py_assignToTeam"](waistcoat, 2, True)
    except:
        print(traceback.print_exc())

def post_waistcoatOnline(instance, waistcoat):
    try:
        if (instance["gamestate"] == 1):
            if (dracula != -1):
                instance["py_assignToTeam"](waistcoat, 2, True)
            else:
                instance["py_assignAll"]()
    except:
        print(traceback.print_exc())

def post_start(instance, countdown):
    try:
        global dracula
        if len(instance["a_teams"][1]["waistcoats"]) == 0:
            instance["client"].publish("game/color/mode", "5", 2)
            instance["client"].publish("game/ammunition", "0", 2)
            time.sleep(3)
            dracula = -1
            instance["py_assignAll"](True)
            instance["client"].publish("game/color/mode", "0", 2)
    except:
        print(traceback.print_exc())

def post_aclives(instance, waistcoat, lives):
    try:
        global dracula
        if (int(lives) == 0 and instance["a_waistcoats"][waistcoat]["team"] == 2):
            if (len(instance["a_teams"][1]["waistcoats"]) == len(instance["a_waistcoats"]) - 1):
                instance["client"].publish("game/color/mode", "5", 2)
                instance["client"].publish("game/ammunition", "0", 2)
                time.sleep(3)
                dracula = -1
                instance["py_assignAll"](True)
                instance["client"].publish("game/color/mode", "0", 2)
                instance["client"].publish("game/state", "2", 2)
                return
            print("Waistcoat " + waistcoat + " is now a zombie!")
            instance["client"].publish("waistcoat/" + waistcoat + "/lives", instance["lives"], 2)
            instance["eel"].py_changeTeam(waistcoat, 1, True)
            time.sleep(instance["reactivationtime"] - 1)
            instance["js_changeTeam"](waistcoat, 1)
    except:
        print(traceback.print_exc())
