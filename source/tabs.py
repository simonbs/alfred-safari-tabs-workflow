import json
from subprocess import Popen, PIPE
from Feedback import Feedback

# Returns tabs as feedback for Alfred
def show_tabs(query = ""):
  feedback = Feedback()
  wins_tabs = all_tabs()
  windows = wins_tabs["windows"]
  for window in windows:
    tabs = window["tabs"]
    for tab in tabs:
      if query is None or query is "" or query in tab["name"] or query in tab["url"]:
        feedback.add_item(tab["name"], "", json_args({ "window_index": window["index"],
                                                       "window_title": window["title"],
                                                       "tab_index": tab["index"],
                                                       "tab_name": tab["name"],
                                                       "tab_url": tab["url"] }))
  return feedback
  
# Retrieves the open windows and tabs
def all_tabs():
  script = """
  on findAndReplace(tofind, toreplace, TheString)
  	set ditd to text item delimiters
  	set text item delimiters to tofind
  	set textItems to text items of TheString
  	set text item delimiters to toreplace
  	if (class of TheString is string) then
  		set res to textItems as string
  	else -- if (class of TheString is Unicode text) then
  		set res to textItems as Unicode text
  	end if
  	set text item delimiters to ditd
  	return res
  end findAndReplace

  tell application "Safari"
  	set json to "{\\"windows\\":["
  	set winlist to every window
  	set winscount to count of winlist
  	set i to 0
  	repeat with win in winlist
  		set winindex to index of win
  		tell me to set wintitle to findAndReplace("\\"", "\\\\\\"", (name of win))
  		set json to json & "{\\"index\\":" & winindex & ",\\"title\\":\\"" & wintitle & "\\",\\"tabs\\":["
  		set tabscount to count of every tab of win
  		set n to 0
  		repeat with t in every tab of win
  			set tabindex to index of t
  			tell me to set tabname to findAndReplace("\\"", "\\\\\\"", (name of t))
  			set taburl to URL of t
  			set json to json & "{\\"index\\":" & tabindex & ",\\"name\\":\\"" & tabname & "\\",\\"url\\":\\"" & taburl & "\\"}"
  			set n to n + 1
  			if n is less than tabscount then
  				set json to json & ","
  			end if
  		end repeat
  		set json to json & "]}"
  		set i to i + 1
  		if i is less than winscount then
  			set json to json & ","
  		end if
  	end repeat
  	set json to json & "]}"
  	return json
  end tell"""
  return json.loads(run_applescript(script))

# Bring a tab to focus
def focus_tab(query):
  args = to_args(query)
  window_index = args["window_index"]
  window_title = args["window_title"]
  tab_index = args["tab_index"]
  script = """
  tell application "Safari"
    tell window %s to set current tab to tab %s
    activate
  end tell
  tell application "System Events" to tell process "Safari"
    perform action "AXRaise" of window %s
  end tell
  """ % (window_index, tab_index, window_index)
  run_applescript(script)

# E-mails a tab
def email_tab(query):
  args = to_args(query)
  tab_name = args["tab_name"]
  tab_url = args["tab_url"]
  script = """
  tell application "Mail"
  	set newmail to make new outgoing message with properties {subject: "%s", content: "%s", visible: true}
  	activate
  end tell
  """ % (tab_name, tab_url)
  run_applescript(script)

# Closes all windows and tabs but the selected
def close_all_tabs_but_selected(query):
  args = to_args(query)
  window_index = args["window_index"]
  tab_name = args["tab_name"]
  script = """
  tell application "Safari"
  	close (every window whose index is not %s)
  	tell window %s to close (every tab whose name is not "%s")
  end tell
  """ % (window_index, window_index, tab_name)
  run_applescript(script)
  
# Closes the specified tabs
def close_tab(query):
  args = to_args(query)
  window_index = args["window_index"]
  tab_index = args["tab_index"]
  script = """
  tell application "Safari"
  	tell window %s to close tab %s
  end tell
  """ % (window_index, tab_index)
  run_applescript(script)

# Executes an AppleScript.
def run_applescript(script):
  p = Popen(["osascript", "-"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
  stdout, stderr = p.communicate(script)
  return stdout
  
# Creates single quoted JSON arguments from a list.
# Single quotes are used instead of double quotes because for some reason
# it doesn't work with double quotes through Alfred.
def json_args(args):
  new_args = {}
  keys = args.keys()
  for key in keys:
    value = args[key]
    if type(value) is str or type(value) is unicode:
      value = value.replace("\"", "\\\"")
    new_args[key] = value
  return json.dumps(new_args).replace("\"", "'")
  
# Creates arguments from a query created with json_args()
def to_args(query):
  return json.loads(query.replace("'", "\""))