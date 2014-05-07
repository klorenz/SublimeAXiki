Shell Mode
==========

If shell mode enabled, you can work with xiki almost like in a shell.  If you
are at end of your line (starting with a prompt), then you hit return and 
command is executed.  A new prompt will be opened after output of command.

Try it.

<< @>>> print("shell mode enabled: %s" % sublime.active_window().active_view().settings().get('xiki_shell_mode'))

If shell mode is enabled, go to end of next line and hit ``enter``::

    $ echo "hello world"

You can enable shell mode by hitting ``ctrl+shift+enter`` with::

    sublime/settings/view
        xiki_shell_mode: true
