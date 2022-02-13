def post_hit(instance, waistcoat, by):
    if (by not in instance["referees"]):
        if (instance["a_waistcoats"][by]["combo"] == 10):
            instance["client"].publish("waistcoat/" + by + "/powerups/invisibility", 2)
            instance["a_waistcoats"][by]["powerups"].add("invisibility")
        elif (instance["a_waistcoats"][by]["combo"] == 7):
            instance["client"].publish("waistcoat/" + by + "/powerups/invulnerability", 2)
            instance["a_waistcoats"][by]["powerups"].add("invulnerability")
        elif (instance["a_waistcoats"][by]["combo"] == 5):
            instance["client"].publish("waistcoat/" + by + "/powerups/rapidfire", 2)
            instance["a_waistcoats"][by]["powerups"].add("rapidfire")
