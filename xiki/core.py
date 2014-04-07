# vim: fileencoding=utf8

if __name__ == '__main__':
	import test

import logging, re, os, time, subprocess, platform, threading, sys
log = logging.getLogger('xiki.core')

from .util import *
from .path import XikiPath, BULLET_RE

# from six.py
def add_metaclass(metaclass):
	"""Class decorator for creating a class with a metaclass."""
	def wrapper(cls):
		orig_vars = cls.__dict__.copy()
		orig_vars.pop('__dict__', None)
		orig_vars.pop('__weakref__', None)
		for slots_var in orig_vars.get('__slots__', ()):
			orig_vars.pop(slots_var)
		return metaclass(cls.__name__, cls.__bases__, orig_vars)
	return wrapper

os_path_exists = os.path.exists
os_path_join   = os.path.join
os_walk        = os.walk

INDENT = "  "

class XikiSettings:
	def __init__(self, xiki):
		self.xiki = xiki
		self.settings = {}

	def __getitem__(self, name):
		return self.settings[name]

	def __setitem__(self, name, value):
		self.settings[name] = value

	def get(self, name, default=None):
		try:
			return self[name]
		except KeyError:
			return default

	def set(self, name, value):
		self[name] = value

	def append(self, name, value):
		if not name in self.settings:
			self.settings[name] = []
		self.settings[name].append(value)

class Snippet:
	def __init__(self, thing):
		if isinstance(thing, str):
			self.snippet = [ unindent(thing) ]

	def __str__(self):
		return ''.join([x for x in self.snippet])

	def __iter__(self):
		yield str(self)

class XikiError(Exception):
	pass

class XikiFileAlreadyExists(XikiError):
	pass

class XikiLookupError(XikiError):
	pass


PY3 = sys.version_info[0] >= 3


def exec_code(code, globals=None, locals=None):
	if PY3:
		import builtins
		getattr(builtins, 'exec')(code, globals, locals)
		exec(code, globals, locals)
	else:
		#frame = sys._getframe()
		exec(code, globals, locals)
		#eval("exec code in globals, locals", frame.f_globals, frame.f_locals)

class XikiExtensions:

	def __init__(self, xiki):
		self.nodes = {}
		self.dirs  = set()
		self.path = set()
		self.xiki = xiki
		self.titles = {}

	def __getitem__(self, name):
		#import spdb ; spdb.start()

		if name in self.nodes:
			return self.nodes[name]

		if name in self.titles:
			return self.titles[name]

		slashed_name = name + "/"
		result = set()
		log.debug("keys nodes: %s" % self.nodes.keys())
		for d in self.titles:
			if d.startswith(slashed_name):
				result.add("+ "+d.split('/', 2)[1]+"\n")
		return ''.join(result)

	def get_title(self, docstring):
		line = 1
		title, doc = docstring.split("\n", 1)
		if doc:
			if doc[0].isalnum():
				title = name
				doc = docstring
				line = 0


		# elif doc[0] != "\n" and not doc[0].isalnum():
		# 	doc = doc.split("\n", 1)[1]
		# 	line = 2

		# i = 0
		# while doc[i].isspace():
		# 	if doc[i] == "\n":
		# 		line += 1
		# 	i += 1
		# if i:
		# 	doc = doc[i:]

		log.debug("get_title: %s, %s, %s", title, doc, line)
		return title, doc, line

	def add_files_from_path(self, root):
		if root in self.path:
			return

		root_len = len(root)+1
		import imp

		mod_base = 'xiki.%s' % self.xiki.name

		if mod_base not in sys.modules:
			sys.modules[mod_base] = imp.new_module(mod_base)

		mod_base = 'xiki.%s.ext' % self.xiki.name

		if mod_base not in sys.modules:
			sys.modules[mod_base] = imp.new_module(mod_base)

		for path_name in self.xiki.walk(root):
			node_name = path_name[root_len:]
			name, ext = os.path.splitext(os.path.basename(path_name))
			node_name = os.path.splitext(node_name)[0]
			dir_name  = os.path.dirname(node_name)

			if node_name in self.nodes:
				m = self.nodes[node_name]
				if self.xiki.getmtime(path_name) < m.time_created:
					continue
				else:
					if hasattr(m, 'unload'):
						m.unload()

			d = os.path.dirname(node_name)
			parts = d.split('/')
			for i,p in enumerate(parts, start=1):
				_dir = '/'.join(parts[:i])
				if not _dir: continue
				self.dirs.add(_dir)

			mod_name = '%s.%s' % (mod_base, '.'.join(parts))

			m = imp.new_module(mod_name)
			m.__file__ = path_name
			m.xiki = self.xiki
			m.XikiContext = XikiContext
			m.XikiPath = XikiPath
			m.log = logging.getLogger(mod_name)
			m.os  = os
			m.sys = sys
			m.re  = re
			m.time_created = time.time()

#			import spdb ; spdb.start()

			if ext == '.py':
				title = name

				source = self.xiki.read_file(path_name)
				code = compile(source, node_name, 'exec')

				exec_code(code, m.__dict__)

				sys.modules[mod_name] = m

				if not hasattr(m,'menu'):

					if hasattr(m, 'Menu'):
						m.menu = m.Menu()
						if not callable(m.menu):
							m.menu.__call__ = lambda: m.Menu.__doc__

					if m.__doc__:

						title, doc, line_offset = self.get_title(m.__doc__)
						m.menu = lambda: doc

					else:
						def _sym_menu(mod):
							def menu(ctx):
								import types
								result = []
								for a in dir(mod):
									if isinstance(a, types.ClassType):
										if issubclass(a, XikiContext):
											result.append("+ %s\n" % a)
										elif callable(a):
											result.append("+ %s\n" % a)
									elif callable(a):
										result.append("+ %s\n" % a)
								return ''.join(result)
							return menu
						m.menu = _sym_menu(m)


			else:
				source = self.xiki.read_file(path_name)

				title, doc, line_offset = self.get_title(source)
				m.menu = lambda: doc

				menu   = []
				pycode = []
				is_python = False
				
				for i,line in enumerate(doc.splitlines(1)):
					if is_python:
						if not line.strip():
							pycode.append(line)
						else:
							indent = get_indent(line)

							if len(indent) <= len(pycode_indent):

								code = compile("\n"*line_offset+unindent(''.join(pycode)), filename=path_name, mode='exec')
								exec_code(code, m.__dict__)
								is_python = False
								menu.append(line)
								pycode = []
								continue

							pycode.append(line)

						continue

					try:
						stripped = line.strip()

						if stripped.startswith('class ') or stripped.startswith('def '):
							pycode_indent = get_indent(line)
							pycode.append(line)
							is_python = True
							line_offset = i

							# pop indicating line in restructured text
							if len(menu) > 2:
								if menu[-2].endswith('::\n') and not menu[-1].strip():
									menu.pop()
									menu.pop()
									# and remove empty lines before
									while not menu[-1].strip():
										menu.pop()

						else:
							menu.append(line)

					except (OverflowError, SyntaxError, ValueError):
						menu.append(line)
						continue

				if is_python:
#					import spdb ; spdb.start()
					code = compile("\n"*line_offset+unindent(''.join(pycode)), filename=path_name, mode='exec')
					exec_code(code, m.__dict__)

				if menu:
					def _menu(menu):
						return lambda: ''.join(menu)
					m.menu = _menu(menu)

			m.title = lambda: title
			self.titles["%s/%s" % (dir_name, title)] = m

			self.nodes[node_name] = m
			for k,v in self.nodes.items():
				log.debug("%s: %s" %(k,v.__file__))

		self.path.add(root)

	def __contains__(self, name):
		return name in self.nodes or name in self.dirs or name in self.titles

	def __iter__(self):
		log.debug("dirs: %s", self.dirs)
		log.debug("node_keys: %s", self.nodes.keys())
		for n in self.dirs.union(set(self.titles.keys())):
			yield n

	def update(self, extdir):
		log.debug("updating from %s", extdir)
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		for menu_dir in self.xiki.get_search_path(extdir):
			log.debug("menu: updating from %s", menu_dir)
			self.add_files_from_path(menu_dir)



class BaseXiki:
	def __init__(self, name=None):
		if name is None:
			name = self.__class__.__name__
		self.name = name

		import tempfile
		self.plugins      = {}
		self.search_paths = {}
		self.cache_dir    = tempfile
		self.storage      = {}

		self.last_exit_code = {}

		if platform.system() == 'Windows':
			if "great" == self.exec_output("bash", "echo", "great").strip():
				self.shell = ['bash', '-c']
			else:
				self.shell = ['cmd', '/c']

			self.storage['home'] = os.path.expanduser('~/AppData/Roaming/axiki')
		else:
			self.shell = ['bash', '-c']
			self.storage['home'] = os.path.expanduser('~/.config/axiki')

		op = os.path
		xiki_dir = op.abspath(op.join(op.dirname(__file__), '..'))

		if os.path.exists(xiki_dir):
			self.register_plugin('xiki', xiki_dir)

		self.static_vars       = {}
		self.default_storage   = 'home'
		self.default_extension = '.xiki'
		self.extension_dir = 'menu'
		self._extensions = XikiExtensions(self)

	def exec_code(self, code, globals=None, locals=None):
		return exec_code(code, globals, locals)

	def extensions(self):
		self._extensions.update(self.extension_dir)
		return self._extensions

	def contexts(self):
		default = None
		for ctx in list(XikiContext):
			if ctx.__name__ == "XikiDefaultContext":
				default = ctx
				continue
			if ctx.__module__.startswith('xiki.contexts'):
				yield ctx
			if ctx.__module__.endswith('.xiki.contexts'):
				yield ctx
			if ctx.__module__.startswith('xiki.%s' % self.name):
				yield ctx

		yield default

	def parse_data(self, string):
		from .parser import parse
		return parse(string)

	def getmtime(self, path):
		return os.path.getmtime(path)

	def isroot(self):
		if isinstance(self, BaseXiki):
			return True
		return False

	def store(self, xiki_path, content, storage=None):
		if storage is None:
			storage = self.default_storage

		path = self.expand_dir(storage)

		menu_dir = os.path.join(path, 'menu')
		if not self.exists(menu_dir):
			self.makedirs(menu_dir)

		filepath = os.path.join(menu_dir, xiki_path + self.default_extension)

		if self.exists(filepath):
			raise XikiFileAlreadyExists("File already exists: %s" % filepath)

		self.write_file(filepath, content)

	def write_file(self, filepath, content):
		with open(filepath, 'w') as f:
			f.write(content)

	def change_bullet(self, line, bullet):
		'''exchanges the bullet from line, if it is a bullet'''
		line = line.strip()
		b = BULLET_RE.match(line)
		if b:
			return bullet+line[1:]
		return None

	def prompt(self):
		if hasattr(self, 'PS1'):
			return self.PS1
		return None

	def snippet(self, s):
		return Snippet(s)

	def get_xiki(self):
		return self

	def cached_file(self,filename):
		content = self.read_file(filename)

	def read_file(self, filename, count=None):
		'''read first count bytes/chars from filename. If you pass no 
		count, entire content of file is returned'''

		with open(filename, 'r') as f:
			if count is None:
				return f.read()
			else:
				return f.read(count)

	def get_static(self, name, default=None, namespace=None):
		if namespace not in self.static_vars:
			return default

		return self.static_vars[namespace].get(name, default)

	def set_static(self, name, value, namespace=None):
		if namespace not in self.static_vars:
			self.static_vars[namespace] = {}
		self.static_vars[namespace][name] = value

	def clear_static(self, namespace=None):
		if not namespace:
			self.static_vars = {}
		else:
			self.static_vars[namespace] = {}

	def open_file(self, filename, opener=None, text_opener=None, bin_opener=None):
		'''open a file in current environment.  Usually you would here
		hook in your editor'''

		from .util import os_open, is_text_file

		if is_text_file(filename, self.read_file(filename, 512)):

			if text_file_opener:
				r = text_file_opener(filename)
				if r is not None:
					return r
			if opener:
				r = opener(filename)
				if r is not None:
					return r

			def _reader():
				with open(filename, 'r') as f:
					for line in f:
						yield line
			return _reader()

		else:
			if bin_opener:
				r = bin_opener(filename)
				if r is not None:
					return r

			if opener:
				r = opener(filename)
				if r is not None:
					return r

			if platform.system() == 'Linux':
				os_open(filename, 'xdg-open')

			elif platform.system() == 'Windows':
				os_open(filename, 'start')

			elif platform.system() == 'OSX':
				os_open(filename, 'open')

			else:
				raise NotImplementedError("Unhandled system: %s" % platform.system())

			return None

	def getcwd(self):
		return os.getcwd()

	def makedirs(self, *path):
		'''make all directories in given path'''

		path = os.path.join(*path)
		if not os.path.isabs(path):
			path = os.path.join(self.getcwd(), path)
		return os.makedirs(path)

	def get_project_dirs(self):
		'''return root project directories. these are only the names, which
		will be expanded by expand_dir'''

		return []

	def get_system_dirs(self):
		'''return system directories, these are only the names, wich will be
		expanded by expand_dir'''

		return []

	def expand_dir(self, path):
		'''expand project and system directory names here'''
		if path in self.storage:
			return self.storage[path]
		raise XikiLookupError("Storage %s not found" % path)

	def shell_expand(self, path):
		'''expands ~ and shellvars in current environment'''
		return os.path.expandvars(os.path.expanduser(path))

	def isdir(self, path):
		return os.path.isdir(path)

	def listdir(self, dir):
		'''list directory content without '.' and '..' '''
		for x in os.listdir(dir):
			if os.path.isdir(os.path.join(dir, x)):
				yield x+"/"
			else:
				yield x

	def exists(self, filepath):
		return os_path_exists(filepath)

	def walk(self, root):
		for dir, dirs, files in os_walk(root):
			if '.git' in dirs: dirs.remove('.git')
			if '.hg'  in dirs: dirs.remove('.hg')
			if '.svn' in dirs: dirs.remove('.svn')
			for fn in files:
				fn = os_path_join(dir, fn).replace('\\', '/')
				yield fn

	def register_plugin(self, name, root=None):

		if root is None:
			root = self.plugin_root

		if isinstance(root, list):
			for r in root:
				self.register_plugin(name, r)
			return

		log.info("register plugin %s -> %s", name, root)

		res_location = "%s/%s/" % (root, name)
		loclen = len(res_location)

		if name not in self.plugins:
			self.plugins[name] = {'files': set(), 'root': res_location[:-1] }

		for r in self.walk(root):
			if r.startswith(res_location):
				self.plugins[name]['files'].add(r[loclen:])

	def get_search_path(self, name):
		log.debug("search_paths: %s", self.search_paths)
		if name in self.search_paths:
			if self.search_paths[name]:
				return self.search_paths[name]

		slashed_name = name
		if not slashed_name.endswith('/'):
			slashed_name += '/'

		search_path = []
		for p in self.plugins:
			plugin_files = self.plugins[p]['files']
			root = self.plugins[p]['root']
			for f in plugin_files:
				if f.startswith(slashed_name):
					search_path.append('%s/%s' % (root, name))
					break

		self.search_paths[name] = search_path

		log.debug("search_path: %s", search_path)
		return search_path

	def open(self, path, input=None, cont=False):
		self.extensions()
		return XikiPath(path).open(self, input=input, cont=cont)

	def close(self, path, input=None):
		self.extensions()
		return XikiPath(path).close(self, input=input)

	def execute(self, *args, **kargs):
		log.debug("execute args: %s", args)
		log.info("Executing: %s", cmd_string(args))
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		if 'cwd' not in kargs:
			kargs['cwd'] = self.getcwd()

		stdin = None
		if 'input' in kargs:
			if kargs['input'] is not None:
				stdin = kargs['input']
				kargs['stdin'] = subprocess.PIPE

			del kargs['input']

		log.info("kargs: %s", kargs)

		if subprocess.mswindows:
			su = subprocess.STARTUPINFO()
			su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			su.wShowWindow = subprocess.SW_HIDE
			kargs['startupinfo'] = su

		p = subprocess.Popen( list(args), stdout = subprocess.PIPE, 
			stderr = subprocess.STDOUT, **kargs )

		if stdin:
			import errno
			try:
				p.stdin.write(stdin.encode('utf-8'))
			except IOError as e:
				if e.errno != errno.EPIPE:
					raise
			p.stdin.close()

		for line in iter(p.stdout.readline,''):
			log.debug("got line: %s", line)
			if isinstance(line, bytes):
				line = line.decode('utf-8').replace('\r', '')
			yield line
			if p.poll() is not None:
				break

		log.debug("get rest of output")
		data = p.stdout.read()
		if isinstance(data, bytes):
			data = data.decode('utf-8')
		if data:
			for line in data.splitlines(1):
				yield line

		log.debug("waiting for process")
		self.last_exit_code[threading.current_thread().name] = p.wait()
		log.debug("done")
		#return self.menu()

	def exec_output(self, *args, **kargs):
		return ''.join([ x for x in self.execute(*args, **kargs)])

	def exec_result(self, *args, **kargs):
		output = ''.join([ x for x in self.execute(*args, **kargs)])
		return self.last_exit_code[threading.current_thread().name]

	def shell_execute(self, command, **kargs):
		return self.execute( *(self.shell + [command]), **kargs )
		return self.execute( *(self.shell + [cmd_string(command, quote="'")]), **kargs )

class MemXiki(BaseXiki):
	STORAGE = {}

	def write_file(self, path, content):
		self.STORAGE[path] = content

	def read_file(self, path, count=-1):
		if path in self.STORAGE:
			if count is not None and count > 0:
				return self.STORAGE[path][:count]
		return BaseXiki.read_file(self, path, count=count)

	def exists(self, path):
		if path in self.STORAGE:
			return True
		return BaseXiki.exists(self, path)

	def makedirs(self, path):
		return None

class ConsoleXiki(BaseXiki):
	def __init__(self, user_root="~/.pyxiki", plugin_root=None):
		BaseXiki.__init__(self)
		self.user_root = os.path.expandvars(os.path.expanduser(user_root))
		if plugin_root is None:
			plugin_root = []

		self.plugin_root = plugin_root

		# register xiki
		plugin_root = os.path.join(os.path.dirname(__file__), '..')
		plugin_root = os.path.abspath(plugin_root)
		self.register_plugin('xiki', root=plugin_root)

class ProxyXiki:
	def __init__(self, xiki):
		self.xiki = xiki

	def __getattr__(self, name):
		log.debug("proxy: %s", name)
		return getattr(self.xiki, name)


class Registry(type):
	'''XikiCommand Registration'''

	def __init__(cls, name, bases, nmspc):
		super(Registry, cls).__init__(name, bases, nmspc)
		if not hasattr(cls, 'registry'):
			cls.registry = {}

		for b in cls.__bases__:
			if b.__name__ in cls.registry:
				del cls.registry[b.__name__]

		if cls.__name__ in cls.registry:
			if hasattr(cls.registry[cls.__name__], 'unload'):
				cls.registry[cls.__name__].unload()

		log.debug("registered %s", cls.__name__)

		cls.registry[cls.__name__] = cls
		if hasattr(cls, 'loaded'):
			cls.loaded()

	def stash(cls, name):
		if not hasattr(cls, registries):
			cls.registries = {}

		cls.registries[name] = self.registry.copy()

	def emerge(cls, name):
		if not hasattr(cls, registries):
			cls.registries = {}

		self.registry = cls.registries[name]


	# Metamethods, called on class objects:
	def __iter__(cls):
		log.debug("values: %s", [x for x in cls.registry.values()])
		return iter(cls.registry.values())

	def __str__(cls):
		if cls.__name__ in cls.registry:
			return cls.__name__
		return cls.__name__ + ": " + ", ".join([sc.__name__ for sc in cls])

class XikiBase(object):
	def __init__(self, ctx=None):
		self.context     = ctx

RegExp = re.compile('').__class__

@add_metaclass(Registry)
class XikiContext(XikiBase):
	CONTEXT = None
	PATTERN = None
	PS1 = None
	PS2 = None

	NAME = None
	MENU = None

	def __init__(self, *args, **kargs):
		XikiBase.__init__(self, *args, **kargs)

		if isinstance(self.PATTERN, str):
			self.PATTERN = re.compile(self.PATTERN)

		self.node_path = None
		self.xiki_path = None
		self.subcontext = None

	def __getattr__(self, name):
		'''Basic idea is this: If a parent context has implemented a function
		such as "execute", which current class has not, call method from parent 
		context.  This a kind of proxying rather then inheritance.

		In PY 2.x you also have to take into account that a method as a class's
		attribute is of type UnboundMethodType, which can only be called with
		a class's instance.  So attribute im_func has to be taken, which contains
		actual "unbound" method.
		'''
		if 0:
			if self.context:
				if hasattr(self.context.__class__, name):
					method = getattr(self.context.__class__, name)
					if callable(method):
						if hasattr(method, 'im_func'):
							method = method.im_func
						return lambda *args, **kargs: method(self, *args, **kargs)

				return getattr(self.context, name)
		else:
			if self.context:
				return getattr(self.context, name)

		raise AttributeError("%s has not attribute %s" % (self.__class__.__name__, name))

	def set_static(self, name, value, namespace=None):
		'''set a static variable, which persists over runtime.'''

		if namespace is None:
			namespace=str(self)
		return self.context.set_static(name, value, namespace=namespace)

	def get_static(self, name, default=None, namespace=None):
		'''set a static variable, which persists over runtime.'''

		if namespace is None:
			namespace=str(self)
		return self.context.get_static(name, default=default, namespace=namespace)

	def prompt(self):
		if self.PS1:
			return self.PS1
		return None

	def __str__(self):
		if self.NAME:
			return self.NAME

		name = self.__class__.__name__
		if name.startswith('Xiki_'):
			name = name[5:]
		if name.startswith('Xiki'):
			name = name[4:].lower()
		if name.lower().endswith('context'):
			name = name[:-7].lower()
		return name

	def does(self, xiki_path):
		'''
		If you overwrite this method, make sure, that you set attributes
		``node_path`` and ``dispatch_path``.  ``node_path`` represents 
		consumed node_path input and ``dispatch_path`` is the unconsumed
		node_path, which still has to be dispatched to other handlers.
		'''

		if not xiki_path:
			return False

		self.mob = None
		if self.PATTERN:
			self.mob = self.PATTERN.search(xiki_path[0])
			if self.mob:
				try:
					xp = self.mob.group('xiki_path')
				except:
					xp = None

				self.xiki_path = xiki_path[1:]
				if xp:
					self.xiki_path.path.insert(0, (xp, 0))

				data_name = "%s_data" % self.__class__.__name__
				setattr(self, data_name, self.mob.groupdict())

				return True

		elif self.CONTEXT:
			if isinstance(self.CONTEXT, RegExp):
				self.mob = self.CONTEXT.search(xiki_path[0])
				if self.mob:
					self.xiki_path = xiki_path[1:]
					return True

			if isinstance(self.CONTEXT, str):
				if self.CONTEXT == xiki_path[0]:
					self.xiki_path = xiki_path[1:]
					return True

			if callable(self.CONTEXT):
				return self.CONTEXT(xiki_path)

		log.debug("?? %s == %s", self.__class__, xiki_path[0])
		if str(self.__class__) == xiki_path[0]:
			self.xiki_path = xiki_path[1:]
			return True

		return False

	def get_context(self):
		'''returns the actual context, who will do the work.  In :method:`does`
		you may create subcontexts.  The leaf of these subcontexts shall be
		stored in self.subcontext, which is returned here.
		'''

		if self.subcontext:
			return self.subcontext
		else:
			return self

	def root_menuitems(self):
		return ""

	def menu(self):
		if hasattr(self, '__doc__'):
			return self.__doc__

		return ''

	def open(self, input=None, cont=None):
		if self.xiki_path:
			log.debug("open: redirect")
			return self.xiki_path.open(context=self, input=input, cont=cont)
		return self.menu()

	def expanded(self, input=None, cont=None):
		return self.open(input=input, cont=cont)

	def close(self, input=None):
		if self.xiki_path:
			try:
				log.debug("close: redirect")
				return self.xiki_path.close(context=self, input=input)
			except LookupError:
				return None


	def full_expand(self, *args, **kargs):
		return self.expand(*args, **kargs)

	def expand(self, *args, **kargs):
#		names =  [ x.name() for x in XikiContext ]
#		names += [ x.name() for x in XikiAction ]

		return None

	def collapse(self, input=None, *args, **kargs):
		return None


	@classmethod
	def loaded(cls):
		'''implement this to do something after this class is loaded'''

	@classmethod
	def unload(cls):
		'''implement this function if you have to unload anything'''

class XikiDefaultContext(XikiContext):
	def does(self, path):
		self.my_path = path
		return True

	def menu(self):
		return "There is no context to handle %s" % self.my_path