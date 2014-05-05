aXiki is a Xiki clone
=====================

Why a clone?
------------

- Original Xiki works only under Unix based OS, and not on Windows.  Although
  there are requests which are years old, there is still done no effort to make
  it run on Windows.

- I tried Xiki and it is really great, but I often got tracebacks while trying 
  out features.  Apart from some (impressive!) screencasts documentation is 
  rather poor, at least for me it was hard to find my way through it.  I wanted 
  to have some notes about general syntax, but found nothing.

- My Ruby knowledge is too poor to get Xiki running on Windows quickly, and I 
  loved to have more Xiki features in SublimeText.

- I started with extending SublimeXiki_, but soon there were only little utility
  functions left from original code, so I started an own Package.

- I wanted to use Xiki everywhere.  Especially in Documentations.  So I extended
  Xiki Language a bit to get it easier embedded into Markdown and reStructured
  Text.


aXiki Concept
-------------

If you are reading this document in SublimeText, it is time to start Xikiing.

You have to remember only two keyboard shortcuts to get started:

- ``ctrl+enter`` — Open a node

- ``ctrl+shift+enter`` — Re-Open a node and pass nested text as input to 
  corresponding handler.


Knowing this, you are ready to hit ``ctrl+return`` on next line:

- help/concept — hit ``ctrl+enter`` here to read more about the concept

- `docs/

Random Notes
============

TODO
----

[ ] output in rst mode. This means if indentation increases, there must be
    inserted an empty line in output tree, such that it is rendered right.

[ ] Add a "snippet" tag in menus
    ::

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

