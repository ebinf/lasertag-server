import time

def post_aclives(instance, waistcoat, lives):
    try:
        if (int(lives) == 0 and instance["a_waistcoats"][waistcoat]["team"] == 2):
            if (len(instance["a_teams"][1]["waistcoats"]) == len(instance["a_waistcoats"]) - 1):
                instance["a_teams"][1]["waistcoats"] = set()
                instance["a_teams"][2]["waistcoats"] = set()
                instance["client"].publish("game/color/mode", "5", 2)
                instance["client"].publish("game/ammunition", "0", 2)
                time.sleep(3)
                instance["py_assignAll"](True)
                instance["client"].publish("game/lives", instance["IntToHex"](instance["lives"]), 2)
                instance["client"].publish("game/ammunition", instance["IntToHex"](instance["ammunition"]), 2)
                instance["client"].publish("game/color/mode", "0", 2)
                instance["client"].publish("game/state", "2", 2)
                return
            print("Waistcoat " + waistcoat + " is now a zombie!")
            instance["eel"].py_changeTeam(waistcoat, 1, True)
            instance["client"].publish("waistcoat/" + waistcoat + "/lives", instance["IntToHex"](instance["lives"]), 2)
            instance["client"].publish("waistcoat/" + waistcoat + "/ammunition", instance["IntToHex"](instance["ammunition"]), 2)
            time.sleep(instance["reactivationtime"] - 1)
            instance["js_changeTeam"](waistcoat, 1)
    except:
        print(traceback.print_exc())

def post_start(instance, countdown):
    try:
        if len(instance["a_teams"][1]["waistcoats"]) == 0:
            instance["client"].publish("game/color/mode", "5", 2)
            instance["client"].publish("game/ammunition", "0", 2)
            time.sleep(3)
            instance["py_assignAll"](True)
            instance["client"].publish("game/lives", instance["IntToHex"](instance["lives"]), 2)
            instance["client"].publish("game/ammunition", instance["IntToHex"](instance["ammunition"]), 2)
            instance["client"].publish("game/color/mode", "0", 2)
    except:
        print(traceback.print_exc())
