Go to File of Python Traceback
==============================

This module lets you jump to a line of a file, displayed in a python traceback::

	class GotoFileOfPythonTraceback(XikiContext):
		PATTERN = re.compile(r'''(?x)
			^\s*(?:!\s*)?File\s"(?P<file>.*)",\s+line\s+(?P<line>\d+)
			''')

		def open(self, input=None, cont=None):
			import sublime
			g = self.mob.groupdict()
			self.window.open_file("%(file)s:%(line)s:0" % g, sublime.ENCODED_POSITION)
