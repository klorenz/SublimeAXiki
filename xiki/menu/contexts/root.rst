Root
====

This context provides a root menu if pressed ``ctrl+enter`` on an empty line.  Each context can create a method ``root_menuitems`` and lines returned there are used to create
root menu.

This context is triggered, if a path is empty.

::

	class root(XikiContext):

		def root_menuitems(self):
			return None

		def does(self,xiki_path):
			return not ''.join(xiki_path).strip()

		def menu(self):
			from xiki.util import unindent

			result = []
			for ctx in self.contexts():
				c = ctx(self)
				items = c.root_menuitems()
				if items:
					result.append(unindent(items))

			result.sort()

			for s in result:
				for l in s.splitlines(1):
					yield '+ '+l