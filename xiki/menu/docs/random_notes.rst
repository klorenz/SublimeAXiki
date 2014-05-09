Random Notes
============

This document contains sketches, ideas and other fragments — random notes!

[ ] output in rst mode. This means if indentation increases, there must be
    inserted an empty line in output tree, such that it is rendered right.

[ ] Add a "snippet" tag in menus ::

        - contacts
          * add
            - first name: $1
            - last name : $2
            - aliases:
              - ${$1.$2@some.domain}
              - all@some.domain

    The star means two things:  Insert in snippet mode and insert expanded 
    tree instead of collapsing in this example aliases item.

    So hitting ``ctrl+enter`` on add line in ::

        + contacts/add


    Will result in::

        - contacts/add
          - first name: $1
          - last name : $2
          - aliases:
            - ${$1.$2@some.domain}
            - all@some.domain

    For handling this form there will be something like::

    class Contacts(XikiMenu):

      def add(self, input):
          dict = self.parse(input)


    If you define a class in camel case it will correspond to a lowercase line
    in menu.

      - my contacts

    will call ``my_contacts`` which may be created by a class named MyContacts.

    So:

    1. Either you create my_contacts function in your module, or you create
       a class MyContacts derived from XikiMenu, which is automatically 
       instantiated as my_contacts.




- ctrl+a,ctrl+m => "as menu" to turn::
	  foo/
	    - bar/
	    - glork/

- ctrl+o,ctrl+m => "open menu", ctrl+return

  into a menu

~/






./

<< 

Normal Wiki with WikiWords or @external_page or @"External Page".

+ foo
- bar
  :key: value
  :key2: value

Is it possible to do a WikiAnywhere?

- within RST:

  `foo`_ or foo_ are wikiwords.



A line starting with

@~/

We need a search mechanism:

- foo bar :: query or filter here

> section
| text or file content

+ collapsed menu
- expanded menu
$ external command

on a word: open file with that name relative to current one with same extension.

in a comment: remove comment char specified by TM_COMMENT


Xiki Settings
=============

xiki/
	- menu-path
		- ~/menu
		- .
		- $(sublime.project_path)/menu


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


TODO:
	In a file browser:

	if filename ends with /, then file is opened locally in xiki tree.

	if a file is xmind, then xmind opener gets active and opens 


add reminder tool:

remind/
  - list of current reminders
  - me
    + in 1h
    - in half an hour
      of: ${1:something}
      [submit]
    - in 2h
    - today
      at: 12:00
    - tomorrow
      at: 13:00

    - tomorrow at 09:00
    - tomorrow at 12:00


  - 2014-04-13/some note
    you will be reminded at



		- 
	- 1400
	- 

For sublime, I need following things:

folders/
	- migration/
		- file1
		- folder1/

How to:
	- rename a file
	- duplicate a file
	- copy a file
	- move a file

special action:
	rename /foo/bar/glork /x/y/z (move)
	duplicate /foo/bar/glork /x/y/z (copy)

Maybe create some special workflow:
	- "Mark" lines and then select an action for them
	- or better create a selection -> turn it into a Mark
	  and then do an action on selected items


$ gnome-terminal -e "sudo apt-get install libreoffice"

For windows we need something like download and execute for installing packages

