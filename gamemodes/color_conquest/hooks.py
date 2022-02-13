import time
import traceback

def shuffleAll(instance):
    try:
        if (instance["gamestate"] == 2):
            instance["client"].publish("game/color/mode", "5", 2)
            instance["client"].publish("game/ammunition", "0", 2)
            time.sleep(3)
        old_waistcoats = instance["a_waistcoats"].copy()
        choicelen = len(instance["a_waistcoats"])
        if (instance["gamestate"] == 1):
            choicelen = len(instance["i_waistcoats"]) + len(instance["a_waistcoats"])
        if (choicelen >= 7):
            choicelen = 7
        if (choicelen != instance["teams"]):
            instance["py_teamAmount"](choicelen, True)
        instance["a_waistcoats"] = old_waistcoats
        instance["py_assignAll"](True)
        if (instance["gamestate"] == 2):
            instance["client"].publish("game/lives", instance["IntToHex"](instance["lives"]), 2)
            instance["client"].publish("game/ammunition", instance["IntToHex"](instance["ammunition"]), 2)
            instance["client"].publish("game/color/mode", "0", 2)
            instance["client"].publish("game/state", "2", 2)
    except:
        print(traceback.print_exc())

def post_start(instance, countdown):
    try:
        shuffleAll(instance)
    except:
        print(traceback.print_exc())

def referee_specialbutton(instance, waistcoat):
    try:
        if (instance["referees"][waistcoat]["mode"] == "shuffle"):
            shuffleAll(instance)
    except:
        print(traceback.print_exc())

def post_hit(instance, waistcoat, by):
    try:
        if (by in instance["referees"]):
            return
        if (instance["a_waistcoats"][waistcoat]["lives"] == 1):
            if (len(instance["a_teams"][instance["a_waistcoats"][by]["team"]]["waistcoats"]) == len(instance["a_waistcoats"]) - 1):
                shuffleAll(instance)
                return
            instance["client"].publish("waistcoat/" + waistcoat + "/lives", instance["lives"], 2)
            instance["eel"].py_changeTeam(waistcoat, instance["a_waistcoats"][by]["team"], True)
            time.sleep(instance["reactivationtime"])
            instance["js_changeTeam"](waistcoat, instance["a_waistcoats"][by]["team"])
    except:
        print(traceback.print_exc())

def init(instance):
    try:
        if (len(instance["i_waistcoats"]) < 7):
            instance["py_teamAmount"](len(instance["i_waistcoats"]), True)
        else:
            instance["py_teamAmount"](7, True)
        instance["py_assignAll"](True)
    except:
        print(traceback.print_exc())

def post_waistcoatOnline(instance, waistcoat):
    try:
        if (len(instance["i_waistcoats"]) + len(instance["a_waistcoats"]) < 7):
            instance["py_teamAmount"](len(instance["i_waistcoats"]) + len(instance["a_waistcoats"]), True)
        else:
            instance["py_teamAmount"](7, True)
        instance["py_assignAll"](True)
    except:
        print(traceback.print_exc())
