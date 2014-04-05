Getting Started with aXiki
==========================

Hit ``ctrl+enter`` on an empty line to get started.

For getting started with Xiki you only have to remember following basic
things.

- Hitting ``ctrl+enter`` at a line will expand it.
	- Hitting ``ctrl+enter`` at a line which is expanded, will collapse it.
	  ... and will hide all indented text beneath.
- Collapsed lines are marked with a leading "+"
	- Expanded lines are marked with a leading "-"

- Hit ``ctrl+shift+enter`` on collapsed line, expands + continues, i.e.
  appends a $ line at the end

- Hit ``ctrl+shift+enter`` on expanded line, will use indented lines as
  input for command.

If you make a change at a line and you want to save current context, hit 


Configuring other tools
=======================

:: 
	fogbugz/
		@ settings/
			- username: kay
			- password: some password
			- url: https://fogbugz.moduleworks.com/fogbugz/api.asp

		- .shell: 

		- defaults/
			- project: 

		- q: here the query goes
			- case 12345: here the title


ideas:
	- store on leave line
	- store on collapse
	- store on special store command
	- preview on enter line (also for text files in IDE mode)




