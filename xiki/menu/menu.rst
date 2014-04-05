Adding Menus
============

You have multiple opportunities to add menus.

Open Menu File
--------------

Add name of Menu file like this: 
|
| - docs/my-doc.py — This will open my-doc.py
| - docs/Getting Started — This will find existing Getting Started rst file
| - docs/
|    - Getting Started
|
Go to a line and hit ctrl+enter to open file.

Create Menu Inline
------------------

Add a new menu by either creating a submenu here like in this example:
| - plants/fruits
|   - apple
|   - peach
|   - plum
Then go to `fruits` line and hit ``ctrl+shit+enter``.  This will create a file named plants/fruits.xiki with content
| - apple
| - peach
| - plum

If you have a project directory `project` and you want to create a menu there, you can do it with following code:
| ~project/
|    @menu
|       - plants/fruits
|         ...

::