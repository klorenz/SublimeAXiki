# vim: fileencoding=utf8

if __name__ == '__main__':
	import test

import logging, re, os, time, subprocess, platform
log = logging.getLogger('xiki.core')

from .util import *
from .path import XikiPath

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


class BaseXiki:
	def __init__(self):
		import tempfile
		self.plugins      = {}
		self.search_paths = {}
		self.user_root    = None
		self.cache_dir    = tempfile

		if platform.system() == 'Windows':
			self.shell = ['cmd', '/c']
		else:
			self.shell = ['bash', '-c']

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
		return None

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

		res_location = "%s/%s/" % (root, name)
		loclen = len(res_location)

		self.plugins[name] = {'files': set(), 'root': res_location[:-1] }

		for r in self.walk(root):
			if r.startswith(res_location):
				self.plugins[name]['files'].add(r[loclen:])

	def get_search_path(self, name):
		if name in self.search_paths:
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
		return XikiPath(path).open(self, input=input, cont=cont)

	def close(self, path, input=None):
		return XikiPath(path).close(self, input=input)

	def execute(self, *args, **kargs):
		log.debug("execute args: %s", args)
		log.info("Executing: %s", cmd_string(args))
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		if 'cwd' not in kargs:
			kargs['cwd'] = self.getcwd()

		p = subprocess.Popen( list(args), stdout = subprocess.PIPE, **kargs )

		for line in iter(p.stdout.readline,''):
			log.debug("got line: %s", line)
			if isinstance(line, bytes):
				line = line.decode('utf-8')
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
		p.wait()
		log.debug("done")
		#return self.menu()

	def shell_execute(self, *args):
		return self.execute( *(self.shell + cmd_string(args)) )

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

	# Metamethods, called on class objects:
	def __iter__(cls):
		log.debug("values: %s", [x for x in cls.registry.values()])
		return iter(cls.registry.values())

	def __str__(cls):
		if cls.__name__ in cls.registry:
			return cls.__name__
		return cls.__name__ + ": " + ", ".join([sc.__name__ for sc in cls])

class XikiBase(object):
	def __init__(self, xiki, ctx=None):
		self.xiki        = xiki
		self.context     = ctx

RegExp = re.compile('').__class__

@add_metaclass(Registry)
class XikiContext(XikiBase):
	CONTEXT = None
	PATTERN = None

	NAME = None
	MENU = None

	def __init__(self, *args, **kargs):
		XikiBase.__init__(self, *args, **kargs)

		if isinstance(self.PATTERN, str):
			self.PATTERN = re.compile(self.PATTERN)

		self.node_path = None
		self.xiki_path = None

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

		if str(self.__class__) == xiki_path[0]:
			self.xiki_path = xiki_path[1:]

		return False

	def root_menuitems(self):
		return str(self)+"\n"

	def menu(self):
		if hasattr(self, '__doc__'):
			return self.__doc__

		return ''

	def open(self, input=None, cont=None):
		if self.xiki_path:
			return self.xiki_path.open(self.xiki, context=self, input=input, cont=cont)
		return self.menu()

	def close(self, input=None):
		if self.xiki_path:
			return self.xiki_path.close(self.xiki, context=self, input=input)

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
		'''implement this to do something after this function is loaded'''

	@classmethod
	def unload(cls):
		'''implement this function if you have to unload anything'''