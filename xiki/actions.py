if __name__ == '__main__':
	import test

from .core import XikiContext
import re, os, logging, sys, os

from .util import *

log = logging.getLogger('xiki.actions')
log.setLevel(logging.DEBUG)

KEY_VALUE = re.compile(r'^(?P<key>\w+\s*:(?:\s(?P<val>.*))?)')

EMPTY_LINES = re.compile(r'\n([\x20\t]*\n)+')


class XikiNodeHandler(XikiAction):
	LINE = re.compile(r'^\s*[\+\-]\s(.*)')

	def collapse(self, s):
		output = self.context.collapse(self.input, s)

		if not output:
			line = '+ %s' % s
		else:
			line = '- %s' % s

		return (line, "")

	def expand(self, s):
		output = self.context.expand(s)

		return ('- %s' % s, output)


	from .util import is_text_file

class XikiFileOpener(XikiAction):
	LINE = re.compile(r'^(?P<path>\./|~/|(?:[A-Z]:)?/)$')

	def expand(self, path):
		log.debug("open path: %s", path)

		if path.startswith('~/'):
			path = os.path.expanduser(path)

		elif path.startswith('~'):
			path = self.context.working_dir

		elif path.startswith('./'):
			path = self.context.working_dir + path[1:]

		elif not os.path.isabs(path):
			path = os.path.join(self.context.working_dir, path)

		if not os.path.exists(path):
			return "!path does not exist: %s\n" % path

		log.debug("open path: %s", path)

		if os.path.isdir(path):
			result = []
			for node in sorted(os.listdir(path)):
				fn = os.path.join(path, node)
				if os.path.isdir(fn):
					result.append("+ %s/\n" % node)
				else:
					result.append("+ %s\n" % node)
#					result.append("- %s\n" % node)

			return ''.join(result)

		else:
			self.xiki.open_file(path)


			g = self.settings.get('xiki_target_group')
			max_lines = self.settings.get('xiki_max_display_lines')

			if not g:
				# TODO define opener
				if not is_text_file(path):
					os_open(path, opener=self.settings.get('xiki_opener'))
				else:
					# inline opener
					if 0:
						with open(path, 'r') as f:
							lines = f.readlines()
							return ''.join([ "| "+line for line in lines ])
					else:
						import sublime
						v = self.window.open_file(path, sublime.ENCODED_POSITION)
						self.window.set_view_index(v, get_main_group(self.window), 0)

			else:
				w = self.view.window()
				v = w.find_open_file(path)
				if v is None:
					v = w.open_file(path)
					i = len(w.views_in_group(g))

#					get_view_index


class GotoFileOfTraceback(XikiAction):
	LINE = re.compile(r'''(?x)
		^\s*!\s*File\s"(?P<file>.*)",\s+line\s+(?P<line>\d+)
		''')

	def expand(self, file, line):
		self.window.open_file("%s:%s:0" % (file, line), sublime.ENCODED_POSITION)


#class CodeTree(XikiContext):
