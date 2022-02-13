var teamamount = 0;

function js_waistcoat_moved(waistcoat, sender, target) {
  if (sender.substr(0, 9) == "inactive_") {
    oldteam = sender.substr(9)
  } else {
    oldteam = sender.substr(7)
  }
  if (target.substr(0, 9) == "inactive_") {
    newteam = target.substr(9)
  } else {
    newteam = target.substr(7)
  }
  if (newteam != oldteam) {
    eel.js_changeTeam(waistcoat, parseInt(newteam))
  }

  if (sender.substr(0, 7) == "active_" && target.substr(0, 9) == "inactive_") {
    js_deactivate(waistcoat, target.substr(9));
  } else if (sender.substr(0, 9) == "inactive_" && target.substr(0, 7) == "active_") {
    js_activate(waistcoat, target.substr(7));
  }
}

function js_activate(waistcoat, team) {
  eel.js_activate(waistcoat);
  if ($("#stop").prop("disabled")) {
    $("#start_0").prop("disabled", false);
    $("#start_10").prop("disabled", false);
    $("#start_30").prop("disabled", false);
  }
  console.log("JS: Waistcoat " + waistcoat + " was activated in team " + team);
}

function js_deactivate(waistcoat, team) {
  eel.js_deactivate(waistcoat)(function (nickname) {
    $("#" + waistcoat).text(nickname);
  });
  console.log("JS: Waistcoat " + waistcoat + " was deactivated to team " + team);
}

function js_teamAmount(amount) {
  console.log("JS: Changing team amount to " + amount)
  eel.js_teamAmount(amount);
}

function js_teamName(team, name) {
  if (!disablenames) {
    $($($("#inactive").children()[team - 1]).children()[0]).text(name);
    $($($("#active").children()[team - 1]).children()[0]).text(name);
    eel.js_teamName(parseInt(team), name);
    console.log("JS: Team " + team + "'s name changed to " + name);
  }
}

function js_start(countdown=0) {
  eel.js_start(countdown)(function() {
    $("#stop").prop("disabled", false);
    $("#start_10>span").hide();
    $("#start_30>span").hide();
    $(".clock").removeClass("text-info");
  });
  if (countdown == 10) {
    $(".clock").addClass("text-info");
    $("#start_10>span").show();
  } else if (countdown == 30) {
    $(".clock").addClass("text-info");
    $("#start_30>span").show();
  }
  $("#ctrl_teams").prop("disabled", true);
  $("#gamemode").prop("disabled", true);
  $("#variations").prop("disabled", true);
  $("#start_0").prop("disabled", true);
  $("#start_10").prop("disabled", true);
  $("#start_30").prop("disabled", true);
  $("#minutes").prop("disabled", true);
  $("#seconds").prop("disabled", true);
  if (countdown > 0) {
    console.log("JS: Countdown started with " + countdown + " seconds")
  } else {
    console.log("JS: Game started")
  }
}

function js_stop() {
  eel.js_stop();
  py_load(false);
  console.log("JS: Game stopped");
}

function js_gameTime(minutes, seconds) {
  $("#minutes").val(String(minutes).padStart(2, '0'));
  $("#seconds").val(String(seconds).padStart(2, '0'));
  eel.js_gameTime(parseInt(minutes) * 60 + parseInt(seconds))
  console.log("JS: Set gametime to " + minutes + ":" + seconds);
}

function js_gameMode(gamemode, variation=false) {
  py_load(true);
  if (gamemode == -1) {
    eel.js_clear();
    return;
  }
  $("#minutes").prop("disabled", false);
  $("#seconds").prop("disabled", false);
  if (variation === false) {
    $("#variations>option").remove();
    $("#variations").prop("disabled", false);
    $("#variations").append("<option value='-1' selected>Standard</option>");
    eel.js_gameMode(gamemode);
  } else {
    eel.js_gameMode(gamemode, variation);
  }
}

eel.expose(py_load);
function py_load(show=false) {
  if (show) {
    $("#spinner").addClass("d-flex");
    $("#spinner").removeClass("d-none");
  } else {
    $("#spinner").addClass("d-none");
    $("#spinner").removeClass("d-flex");
  }
}

eel.expose(py_init);
function py_init(payload) {
  $("#gamemode>option:gt(0)").remove();
  for (gamemode in payload) {
    $("#gamemode").append('<option value="' + gamemode + '">' + payload[gamemode] +  '</option>');
  }
}

eel.expose(py_gameMode);
function py_gameMode(variations, standard) {
  $("#variations>option").remove();
  if (standard) {
    $("#variations").append("<option value='-1' selected>Standard</option>");
  }
  for (variation in variations) {
    $("#variations").append('<option value="' + variation + '">' + variations[variation] +  '</option>');
  }
  $("#minutes").prop("disabled", false);
  $("#seconds").prop("disabled", false);
}

eel.expose(py_variation);
function py_variation(disableTeamAmount, disableTeamNames) {
  $("#ctrl_teams").prop("disabled", disableTeamAmount);
  $("#teams>div>div>input").prop("disabled", disableTeamNames);
  $("#teams_panel").toggle(!disableTeamNames);
}

eel.expose(py_waistcoatOnline);
function py_waistcoatOnline(waistcoat, nickname, team) {
  if ($("#" + waistcoat).length == 0) {
    if (team == -1) {
      teami = "#unused"
    } else {
      teami = "#inactive_" + team
    }
    $(teami).append("<li class=\"list-group-item\" id=\"" + waistcoat + "\">" + nickname + "</li>");
    console.log("PY: Waistcoat " + waistcoat + " went online in team " + team);
  }
}

eel.expose(py_waistcoatOffline);
function py_waistcoatOffline(waistcoat) {
  $("#" + waistcoat).remove();
  console.log("PY: Waistcoat " + waistcoat + " went offline")
}

eel.expose(py_waistcoatInactive);
function py_waistcoatInactive(waistcoat) {
  $("#" + waistcoat).addClass("text-muted");
  $("#" + waistcoat).css("text-decoration", "line-through");
  console.log("PY: Waistcoat " + waistcoat + " disconnected during game")
}

eel.expose(py_waistcoatReconnected);
function py_waistcoatReconnected(waistcoat) {
  $("#" + waistcoat).removeClass("text-muted");
  $("#" + waistcoat).css("text-decoration", "");
  console.log("PY: Waistcoat " + waistcoat + " reconnected")
}

eel.expose(py_changeTeam);
function py_changeTeam(waistcoat, team, activated=false) {
  $((activated ? "#active_" : "#inactive_") + team).append($("#" + waistcoat));
  console.log("PY: Waistcoat " + waistcoat + " was moved to team " + team);
}

eel.expose(py_activate);
function py_activate(waistcoat, team, nickname=false) {
  if (nickname !== false) {
    $("#" + waistcoat).text(nickname);
  }
  $("#active_" + team).append($("#" + waistcoat));
  $("#start_0").prop("disabled", false);
  $("#start_10").prop("disabled", false);
  $("#start_30").prop("disabled", false);
  console.log("PY: Waistcoat " + waistcoat + " was activated in team " + team);
}

eel.expose(py_teamAmount);
function py_teamAmount(amount, teams=[]) {
  $("#unused").append($("#active>div>ul>li"));
  $("#unused").append($("#inactive>div>ul>li"));
  $("#inactive>div").remove();
  $("#active>div").remove();
  $("#teams>div").remove();
  for (i = 0; i < amount; i++) {
    $("#inactive").append("<div class=\"card m-0 mb-3\" style=\"border-color: #" + teams[i]["color"] + ";\">\
      <div class=\"card-header\" style=\"background-color: #" + teams[i]["color"] + ";\">" + teams[i]["name"] + "</div>\
      <ul class=\"list-group list-group-flush waistcoatsSelection\" id=\"inactive_" + (i + 1) + "\">\
      </ul></div>");
    $("#active").append("<div class=\"card m-0 mb-3\" style=\"border-color: #" + teams[i]["color"] + ";\">\
      <div class=\"card-header\" style=\"background-color: #" + teams[i]["color"] + ";\">" + teams[i]["name"] + "</div>\
      <ul class=\"list-group list-group-flush waistcoatsSelection\" id=\"active_" + (i + 1) + "\">\
      </ul></div>");
    $("#teams").append("<div class=\"form-group\">\
      <label>Team " + (i + 1) + "</label>\
      <div class=\"input-group\">\
        <div class=\"input-group-prepend\">\
          <span class=\"input-group-text\" style=\"background-color: #" + teams[i]["color"] + "\"></span>\
        </div>\
        <input type=\"text\" class=\"form-control\" value=\"" + teams[i]["name"] + "\" id=\"name_" + (i + 1) + "\">\
      </div></div>");
    $("#name_" + i).change(function () { js_teamName($(this)[0].id.substr(5), $(this).val()); });
  }
  teamamount = amount;
  $("#active").append("<div class=\"card m-0 mb-3 border-light\">\
    <div class=\"card-header text-dark bg-light\">Neutral/Referees</div>\
    <ul class=\"list-group list-group-flush waistcoatsSelection\" id=\"active_0\">\
    </ul></div>");
  $(".waistcoatsSelection").sortable({
    connectWith: ".waistcoatsSelection",
    placeholder: "list-group-item list-group-item-success",
    cursor: "move",
    scroll: false,
    revert: true,
    tolerance: "pointer",
    receive: function (event, ui) {
      js_waistcoat_moved(ui.item[0].id, ui.sender[0].id, event.target.id);
    }
  }).disableSelection();
  $("#ctrl_teams").val(amount);
  console.log("PY: Changed team amount to " + amount);
}

eel.expose(py_clear);
function py_clear(keepGamemode=false) {
  py_load(true);
  if (!keepGamemode) {
    $("#gamemode").val(-1);
    $("#variations").prop("disabled", true);
    $("#variations").html("<option selected disabled>– Select a gamemode –</option>");
    $("#minutes").prop("disabled", true);
    $("#minutes").val("00");
    $("#seconds").prop("disabled", true);
    $("#seconds").val("00");
  } else {
    $("#unused").append($("#active>div>ul>li"));
    $("#unused").append($("#inactive>div>ul>li"));
  }
  $("#start_0").prop("disabled", true);
  $("#start_10").prop("disabled", true);
  $("#start_30").prop("disabled", true);
  $("#stop").prop("disabled", true);
  $("#teams_panel").show();
  $("#ctrl_teams").prop("disabled", true);
  $("#gamemode").prop("disabled", false);
  $("#inactive>div").remove();
  $("#active>div").remove();
  $("#teams>div").remove();
  $("#ctrl_teams").val(0);
}

eel.expose(py_gameTime);
function py_gameTime(seconds) {
  $("#minutes").val(String((seconds - (seconds % 60)) / 60).padStart(2, '0'));
  $("#seconds").val(String(seconds % 60).padStart(2, '0'));
}

eel.expose(py_gameStart);
function py_gameStart() {
  $("#stop").prop("disabled", false);
  $("#ctrl_teams").prop("disabled", true);
  $("#gamemode").prop("disabled", true);
  $("#variations").prop("disabled", true);
  $("#start_0").prop("disabled", true);
  $("#start_10").prop("disabled", true);
  $("#start_30").prop("disabled", true);
  $("#minutes").prop("disabled", true);
  $("#seconds").prop("disabled", true);
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip();
  $("#ctrl_teams").change(function () {
    js_teamAmount(parseInt($("#ctrl_teams").val()));
  });
  $("#start_0").click(function () { js_start(0); });
  $("#start_10").click(function () { js_start(10); });
  $("#start_30").click(function () { js_start(30); });
  $("#stop").click(function () { js_stop(); });
  $("#minutes, #seconds").change(function () { js_gameTime($("#minutes").val(), $("#seconds").val()); });
  $("#gamemode").change(function () { js_gameMode($(this).val()); });
  $("#variations").change(function () { js_gameMode($("#gamemode").val(), $(this).val()); });
  eel.js_init();
});
