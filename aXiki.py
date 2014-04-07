import sys, os, time

import sublime, sublime_plugin

from imp import reload

from .xiki import util, core, core, path
from . import xiki as xiki_package
reload(util)
reload(path)
reload(core)
reload(xiki_package)

# make xiki global
for x in list(sys.modules):
	if x.startswith('aXiki.xiki'):
		sys.modules[x[6:]] = sys.modules[x]

import sys
import os
import logging
import re

import logging
log = logging.getLogger('xiki.sublime-connector')
log.setLevel(logging.DEBUG)

INDENTATION  = '  '
backspace_re = re.compile('.\b')

from .xiki.core import BaseXiki, ProxyXiki, XikiPath, INDENT, Snippet
from .xiki.util import INDENT_RE, unindent
from .edit import xiki_apply_edit, Edit

def replace_line(view, edit, point, text):
	text = text.rstrip()
	line = view.full_line(point)

	edit.insert(line.b, text + '\n')
	edit.erase(line)

def is_xiki_buffer(view):
	return view is not None and view.settings().get('xiki')

def get_indent(view, region):
	v = view
	return INDENT_RE.match(v.substr(v.line(region))).group(0)

def get_main_group(window):
	'''return widest view ... what if there are two wide views?'''

	result = []
	for i in range(window.num_groups()):
		result.append( (window.active_view_in_group(i).viewport_extent()[0], i) )
	group = max(result)[1]
	log.debug("groups: %s, group: %s", result, group)
	return group

def show_panel(view, options, done, highlighted=None):
	sublime.set_timeout_async(lambda: view.window().show_quick_panel(options, done, 0, -1, highlighted), 10)

def ask_user_yes_no(view, condition, yes_text="Engage!", 
	no_text="I Panic!"):

	if isinstance(yes_text, str):
		yes_text = [yes_text]
	if isinstance(no_text, str):
		no_text = [no_text]
	options = [ ['Yes']+yes_text, ['No']+no_text ]

	result = []

	def done(index):
		if index == -1:
			result.append("esc")
			return
		if index == 1:
			result.append("yes")
			return
		if index == 2:
			result.append("no")
			return

	show_panel(view, options, done)

	while not result:
		time.sleep(0.1)

	return result[0]

# helpers

def dirname(path, tree, tag):
	path_re = r'^(.+)/%s$' % re.escape(tag)
	match = re.match(path_re, tree)
	if match:
		return os.path.join(path, match.group(1))
	else:
		return path

def completions(base, partial, executable=False):
	if os.path.isdir(base):
		ret = []
		partial = partial.lower()

		for name in os.listdir(base):
			path = os.path.join(base, name)
			if name.lower().startswith(partial):
				if not executable or os.access(path, os.X_OK):
					ret.append(name)

		return ret

def apply_xiki_settings(view):
	return

	settings = view.settings()
	settings.set('tab_size', 2)
	settings.set('translate_tabs_to_spaces', True)
	settings.set('syntax', 'Packages/SublimeXiki/Xiki.tmLanguage')

started = time.time()

class SublimeXiki(BaseXiki):
	def __init__(self):
		BaseXiki.__init__(self)
		self.plugin_root  = "Packages"
		self.user_root    = "Packages/User/aXiki"

	def is_packages(self, path):
		return path == "Packages" or path.startswith('Packages/')

	def walk(self, path):
		log.debug("walk path %s", path)
		if self.is_packages(path):
			slashed_p = path
			if not slashed_p.endswith('/'):
				slashed_p += "/"

			for r in sublime.find_resources('*'):
				if r.startswith(slashed_p):
					yield r
		else:
			BaseXiki.walk(self, path)

	def getmtime(self, path):
		if path.startswith('Packages/aXiki'):
			_path = sublime.packages_path()
			path = os.path.join(_path, path[9:])
			if os.path.exists(path):
				return os.path.getmtime(path)
			return started
		if path.startswith('Packages/'):
			return started

	def path_exists(self, path):
		if self.is_packages(path):
			slashed_p = path
			if not slashed_p.endswith('/'):
				slashed_p += "/"

			for r in sublime.find_resources('*'):
				if path == r: return True
				if r.startswith(slashed_p): return True

			return False
		return BaseXiki.path_exists(self, path)

	def read_file(self, path):
		log.debug("reading %s", path)
		if self.is_packages(path):
			return sublime.load_resource(path)
		return BaseXiki.read_file(self, path)

	def open_file(self, path, opener=None, text_opener=None, bin_opener=None):
		if path.startswith('Packages/'):
			path = '${packages}/'+path[9:]

		BaseXiki.open_file(path, opener=opener, text_opener=text_opener, 
			bin_opener=bin_opener)

	def __call__(self, view, action="default", cont=False, handle_input=False):
		'''Interface to Sublime Text.
		'''

		if not is_xiki_buffer(view): return

		for sel in list(view.sel()):
			# get line region

			line_region = view.full_line(sel.end())
			line        = view.substr(line_region).rstrip()

			# get tree for current node
			lr = line_region
			indent = get_indent(view, lr.begin())
			if line.strip():
				while lr.begin()-1 > 0 and indent:
					lr = view.line(lr.begin()-1)
					_indent = get_indent(view, lr)
					_line   = view.substr(lr).strip()
					if not _line:
						continue
					if len(_indent) == 0:
						break

			path_region = sublime.Region(lr.begin(), line_region.end())
			tree        = view.substr(path_region)

			# find input
			next_char = sublime.Region(line_region.end(), line_region.end()+1)

			# collapse if needed
			indent = get_indent(view, line_region)
			next_indent = get_indent(view, next_char)

			xiki = SublimeRequestXiki(self, view, line_region, tree, cont=cont, sel=sel)

			if next_indent.startswith(indent) and len(next_indent) > len(indent):
				r = view.indented_region(next_char.begin())

				if handle_input:
					xiki.open(input=unindent(view.substr(r)))
				else:
					xiki.close()

			elif line.strip().startswith('-'):
				if handle_input:
					xiki.open(input="")
				else:
					xiki.close(tree)

			else:
				if handle_input:
					xiki.open(input="")
				else:
					xiki.open()


class SublimeRequestXiki(SublimeXiki, ProxyXiki):
	def __init__(self, xiki, view=None, line_region=None, tree=None, cont=False,sel=None):
		ProxyXiki.__init__(self, xiki)
		self.view        = view
		self.window      = view.window()
		self.line_region = line_region
		self.tree        = tree
		self.cont        = cont
		self.sel         = sel

	def getcwd(self):
		fn = self.view.file_name()
		if fn:
			return os.path.dirname(fn)

	def get_project_dirs(self):
		return [os.path.basename(x) for x in self.view.window().folders()]

	def get_system_dirs(self):
		return ['sublime']

	def expand_dir(self, name):
		if name == 'sublime':
			return os.path.abspath('.')

		for f in self.view.window().folders():
			if os.path.basename(f) == name:
				return f

		return None

	def open(self, input=None, cont=False):
		try:
			context = XikiPath(self.tree).context(self)
			handler = context.open
		except:
			log.error("open", exc_info=1)
			context = None
			handler = None

		args    = tuple()
		kwargs  = dict(input=input, cont=cont)

		t = XikiHandlerThread(self.view, self.line_region,
			xiki    = self, 
			handler = handler, args=args, kwargs=kwargs,
			context  = context,
			bullet   = '-',
			)
		t.start()

	def close(self, input=None):
		handler = XikiPath(self.tree).close
		args    = (self,)
		kwargs  = dict(input=input)

		t = XikiHandlerThread(self.view, self.line_region,
			xiki    = self, 
			handler = handler, args=args, kwargs=kwargs,
			bullet  = '+',
			)
		t.start()


MULTISLASHES_RE = re.compile(r'//+')

import threading
class XikiHandlerThread(threading.Thread):
	def __init__(self, view, region, xiki=None, handler=None, args=[], kwargs={},
		context=None, bullet=None):
		threading.Thread.__init__(self)
		if hasattr(handler, '__name__'):
			name = handler.__name__
		else:
			name = handler.__class__.__name__

		self.region_name = "xiki %s %s" % (name, self.name)

		self.xiki    = xiki
		self.handler = handler
		self.args    = args
		self.kwargs  = kwargs
		self.view    = view
		self.region  = region
		self.context = context
		self.bullet  = bullet

		self.indent = get_indent(view, region)


	def _append_output(self):
		view = self.view
		regions = view.get_regions(self.region_name)
		if not regions: return

		output = ''.join(self.buffer)
		if output.endswith('\n'):
			self.buffer[:] = []
		elif "\n" in output:
			self.buffer[:-1] = []
			output, buf      = output.rsplit("\n", 1)
			self.buffer[-1]  = buf
			output          += "\n"
		else:
			return

		#pos = view.line(regions[0].end()-1)
		pos = view.line(regions[0].end()-1)

		restore_sel = []
		for sel in list(view.sel()):
			if pos.end() in (sel.begin(), sel.end()):
				restore_sel.append(sel)
				view.sel().subtract(sel)

		indent = self.indent+INDENT

		# if on empty line, we do not indent
		if not self.indent:
			if not self.view.substr(self.region).strip():
				indent = ""

		with Edit(view) as edit:
			try:
				p = view.full_line(pos)
				edit.insert(p.end()-1, "\n"+''.join([indent+l for l in output.splitlines(1)])[:-1])
				#insert(view, edit, pos, output, indent=self.indent)
			except:
				log.error('error writing output', exc_info=1)
			finally:
				def restore_selections():
					for sel in restore_sel:
						view.sel().add(sel)

				edit.callback(restore_selections)

	def run(self):
		if self.xiki.cont:
			log.debug("Normal Enter")
			normal_enter = False

			if not self.context:
				normal_enter = True
			elif not self.context.prompt():
				normal_enter = True
			elif self.context:
				prompt = self.context.prompt().lstrip()
				log.debug("prompt: %s", repr(prompt))
				line = self.view.substr(self.view.line(self.xiki.sel))
				log.debug("line: %s", repr(line))
				if not line.lstrip().startswith(prompt):
					normal_enter = True

			log.debug("Normal Enter: %s", normal_enter)
			if normal_enter:
				b = self.xiki.sel.begin()
				e = self.xiki.sel.end()
				log.debug("sel: %s, %s", b, e)

				self.view.sel().subtract(self.xiki.sel)

				# restore_sel = []
				# for sel in list(self.view.sel()):
				# 	if e in (sel.begin(), sel.end()):
				# 		restore_sel.append(sel)
				# 		view.sel().subtract(sel)

				with Edit(self.view) as edit:
					edit.replace(self.xiki.sel, "\n")

					def _restore_sel():
						if b != e:
							log.debug("add: %s, %s", b, b+1)
							self.view.sel().add(sublime.Region(b, b+1))
						else:
							log.debug("add: %s", b+1)
							self.view.sel().add(sublime.Region(b+1))

					edit.callback(_restore_sel)

				return

		self.view.add_regions(self.region_name, [self.region], 'keyword', '', 
			sublime.DRAW_OUTLINED)

		try:

			log.debug("handler: %s, args: %s, kwargs: %s", self.handler, self.args, self.kwargs)
			output = self.handler(*self.args, **self.kwargs)

		except Exception as e:
			if self.view.settings().get('xiki_traceback'):
				import traceback
				output = traceback.format_exc()
				output = ''.join(['! '+l for l in output.splitlines(1)])
			else:
				output = "! %s" % e

		try:
			self._print_output(output)
		except Exception as e:
			if self.view.settings().get('xiki_traceback'):
				import traceback
				output = traceback.format_exc()
				output = ''.join(['! '+l for l in output.splitlines(1)])
			else:
				output = "! %s" % e

			log.error("exception while printing", exc_info=1)

			try:
				self._print_output(output)
			except:
				log.error("exception while printing exception", exc_info=1)

	def _insert_snippet(self, contents):
		view   = self.view
		indent = self.indent
		line_region = self.view.get_regions(self.region_name)[0]
		pos    = line_region.end()

		view.sel().clear()
		view.sel().add(sublime.Region(pos, pos))
		view.run_command('insert_snippet', {'contents': contents})

	def _print_output(self, output):
		line = self.view.substr(self.region)
		line_to_replace = self.xiki.change_bullet(line, self.bullet)

		if isinstance(output, tuple):
			# got first line + output
			line_to_replace = output[0].strip()
			output = output[1]

		if isinstance(output, str):
			output = [ output ]

		if not output:
			output = []

		# remove indented part if present
		line_region = self.region
		indent      = self.indent
		view        = self.view
		next_char   = sublime.Region(line_region.end(), line_region.end()+1)
		next_indent = get_indent(view, next_char)

		if next_indent.startswith(indent) and len(next_indent) > len(indent):
			r = view.indented_region(next_char.begin())
			with Edit(view) as edit:
				edit.erase(r)

		if isinstance(output, Snippet):
			self._insert_snippet(str(output))
		else:
			self.buffer = buf = []
			last        = time.time()

			for o in output:
				if not o: continue

				if isinstance(o, bytes):
					o = o.decode('utf-8')

				if not isinstance(o, str):
					o = str(o)

				buf.append(o)

				since = time.time() - last
				if since > 0.05:
					last = time.time()
					self._append_output()

			if buf:
				log.debug("buf: %s", buf)
				if not buf[-1].endswith("\n"):
					buf.append("\n")
				self._append_output()

		if self.xiki.cont:
			if self.view.settings().get('xiki_shell_mode', True):
				if self.context:
					prompt = self.context.prompt()
					if prompt:
						self._insert_snippet(self.indent+str(prompt).replace('$', '\\$')+"$0\n")

		# if self.cont:
		# 	if isinstance(self.cont, Snippet):
		# 		log.debug("add prompt: %s", self.cont)
		# 		self._insert_snippet(line_region, str(self.cont))
		# 	else:
		# 		raise NotImplementedError("cont must be snippet")

		if line_to_replace:
			region = self.view.get_regions(self.region_name)[0]
			pos    = region.begin() + 1
			if pos >= region.end():
				pos = region.begin()

			with Edit(self.view) as edit:
				replace_line(self.view, edit, pos, self.indent+line_to_replace)

		self.view.erase_regions(self.region_name)

xiki = SublimeXiki()

# sublime event classes

class XikiListener(sublime_plugin.EventListener):

	def on_query_completions(self, view, prefix, locations):

		return []

		if is_xiki_buffer(view):
			sel = view.sel()
			if len(sel) == 1:
				row, _ = view.rowcol(sel[0].b)
				indent, sign, path, tag, tree = find_tree(view, row)

				if sign == '$':
					# command completion
					pass
				elif path:
					# directory/file completion
					target, partial = os.path.split(dirname(path, tree, tag))
					return completions(target, partial)

	def on_query_context(self, view, key, operator, operand, match_all):

		if key == 'xiki' and is_xiki_buffer(view):
			return True

	def on_load(self, view):

		# handle new user preferences file
		if view.file_name() and os.path.split(view.file_name())[1] == 'SublimeXiki.sublime-settings':
			if view.size() == 0:
				with Edit(view) as edit:
					template = {
						"double_click": False
					}
					edit.insert(0, json.dumps(template, indent=4))
		elif is_xiki_buffer(view):
			apply_xiki_settings(view)
			pass

	def on_pre_save(self, view):
		if view.file_name():
			if 'aXiki' in view.file_name():
				return

		view.set_scratch(True)

	def on_post_save(self, view):
		if view.file_name():
			if 'aXiki' in view.file_name():
				return
		view.set_scratch(False)


	def on_close(self, view):
		pass
		#
		# TODO: terminate active commands
		#
		#
		# vid = view.id()
		# for process in list(commands[vid].values()):
		# 	try:
		# 		process.terminate()
		# 	except OSError:
		# 		pass

		# del commands[vid]

class XikiCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		xiki(self.view)

	def is_enabled(self):
		if is_xiki_buffer(self.view):
			return True
		return False

class XikiContinue(XikiCommand):
	def run(self, edit):
		xiki(self.view, cont=True)

class XikiInput(XikiCommand):
	def run(self, edit):
		xiki(self.view, handle_input=True)

class NewXiki(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.new_file()
		apply_xiki_settings(view)

class XikiClick(sublime_plugin.WindowCommand):
	def is_enabled(self):
		view = self.window.active_view()
		if view is None: return False
		return is_xiki_buffer(view) and view.settings().get('xiki_double_click')

	def run(self):
		if not self.is_enabled(): return

		view = self.window.active_view()

		sel = view.sel()
		s = sel[0]

		text = view.substr(s)
		is_word = r'^(\w+|[^\w]+)$'
		if not re.match(is_word, text.strip('\n')):
			return

		sel.clear()
		sel.add(sublime.Region(s.b, s.a))
		xiki(view)

class XikiIde(sublime_plugin.WindowCommand):
	def run(self):
		active_group = self.window.active_group()

		self.window.set_layout({'rows': [0.0, 0.33, 1.0], 
			'cells': [[0, 0, 1, 1], [1, 0, 2, 2], [0, 1, 1, 2]], 
			'cols': [0.0, 0.33, 1.0]})

		self.window.focus_group(min(active_group), 3)

def plugin_loaded():
	setattr(sys.modules['__main__'], 'xiki', xiki)
	log.debug("make sure extensions are loaded")
	# make sure extensions are up-to-date
	xiki.register_plugin('aXiki/xiki')
	xiki.register_plugin('aXiki')
	xiki.extensions()

def plugin_unloaded():
	if hasattr(sys.modules['__main__'], 'xiki'):
		delattr(sys.modules['__main__'], 'xiki')
