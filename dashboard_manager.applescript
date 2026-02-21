-- Horse Racing Dashboard Manager
-- Checks status of port 8000 and 3000 to determine if app is running.

try
	set backendStatus to do shell script "lsof -i :8000 -t"
on error
	set backendStatus to ""
end try

if backendStatus is not "" then
	-- App is running
	display dialog "The Horse Racing Dashboard is currently RUNNING." buttons {"Cancel", "Stop Dashboard"} default button "Stop Dashboard" with icon note
	if button returned of result is "Stop Dashboard" then
		try
			do shell script "lsof -ti:8000,3000 | xargs kill -9"
			display notification "Dashboard has been stopped." with title "Horse Racing Dashboard"
		on error
			display alert "Error stopping dashboard" message "Could not kill processes."
		end try
	end if
else
	-- App is not running
	display dialog "The Horse Racing Dashboard is currently STOPPED." buttons {"Cancel", "Start Dashboard"} default button "Start Dashboard" with icon note
	if button returned of result is "Start Dashboard" then
		-- Path to the start script
		set scriptPath to "/Users/ron/Documents/Antigravity/horse-racing-dashboard/start_dashboard.command"
		
		-- Execute it using verify it exists
		tell application "System Events"
			if not (exists file scriptPath) then
				display alert "Script not found" message "Could not find: " & scriptPath
				return
			end if
		end tell
		
		-- Run the command file (which opens terminals)
		do shell script "open " & quoted form of scriptPath
		display notification "Dashboard is starting..." with title "Horse Racing Dashboard"
	end if
end if
