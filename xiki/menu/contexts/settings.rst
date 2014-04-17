Settings
========

Handle Settings.  You may set settings on three different layers:

::

	class settings(XikiContext):

		def does(self, xiki_path):
			if self.context.isroot():
				return False

			if xiki_path[0].lower() == 'settings':
				return True

			return False

		def menu(self):
			output = ""
			from xiki.util import indent

			for i,(k,v) in enumerate(self.context.settings().items()):
				output += ":%s:" % k

				if "\n" in v:
					output += "\n$%s%s" % (i, indent(v, "    "))
				else:
					output += " ${%s:%s}" % v

			return output

