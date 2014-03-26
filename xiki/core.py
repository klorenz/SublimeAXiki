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


class BaseXiki:
	def __init__(self):
		self.plugins      = {}
		self.search_paths = {}
		self.user_root    = None

	def read_file(self, filename):
		with open(filename, 'r') as f:
			return f.read()

	def open_file(self, filename):
		from .util import os_open, is_text_file

		if is_text_file(filename):
			def _reader():
				with open(filename, 'r') as f:
					for line in f:
						yield line
			return _reader()

		else:
			if platform.system() == 'Linux':
				os_open(filename, 'xdg-open')

			elif platform.system() == 'Windows':
				os_open(filename, 'start')

			elif platform.system() == 'OSX':
				os_open(filename, 'open')

			else:
				raise NotImplementedError("Unhandled system: %s" % platform.system())

			return None


	def makedirs(self, path):
		return os.makedirs(path)

	def get_project_dirs(self):
		return []

	def get_system_dirs(self):
		return []

	def expand_dir(self, name):
		return None

	def listdir(self, dir):
		for x in os.listdir(dir):
			if os.path.isdir(os.path.join(dir, x)):
				yield x+"/"
			else:
				yield x

	def getcwd(self):
		return os.getcwd()

	def path_exists(self, filepath):
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

		if not self.context:
			self.working_dir = self.xiki.getcwd()

			if platform.system() == 'Windows':
				self.shell = ['cmd', '/c']
			else:
				self.shell = ['bash', '-c']

			self.dispatch_path = None

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
		if self.context:
			if hasattr(self.context.__class__, name):
				method = getattr(self.context.__class__, name)
				if callable(method):
					if hasattr(method, 'im_func'):
						method = method.im_func
					return lambda *args, **kargs: method(self, *args, **kargs)
				else:
					return getattr(self.context, name)

		method = getattr(self.__class__, 'default_'+name)
		if callable(method):
			if hasattr(method, 'im_func'):
				method = method.im_func
			return lambda *args, **kargs: method(self, *args, **kargs)

		return getattr(self.context, 'default_'+name)


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
				self.xiki_path = xiki_path[1:]
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

	def default_exists(self, path):
		return self.xiki.path_exists(path)

	def default_listdir(self, dir):
		return self.xiki.listdir(dir)

	def default_execute(self, *args, **kargs):
		log.debug("execute args: %s", args)
		log.info("Executing: %s", self.cmd_string(args))
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		if 'cwd' not in kargs:
			kargs['cwd'] = self.working_dir

		p = subprocess.Popen( list(args), stdout = subprocess.PIPE, **kargs )

		for line in iter(p.stdout.readline,''):
			log.debug("got line: %s", line)
			yield line
			if p.poll() is not None:
				break

		log.debug("get rest of output")
		data = p.stdout.read()
		if data:
			yield data

		log.debug("waiting for process")
		p.wait()
		log.debug("done")
		#return self.menu()

	def dispatch(self, thing, method, *args, **kargs):
		'''
			if thing is an action subclass, this dispatches to method of action object
			if method is None or a XikiContext object, this returns a context
			to handle something

			dispatches a path 
		'''
		log.debug("%s dispatching %s(%s, %s)", self, thing, args, kargs)

		if method is None:
			return self.xiki.dispatch_ctx(self.view, self.line_region, self.action, self, thing)

		if isinstance(method, XikiContext):
			return self.xiki.dispatch_ctx(self.view, self.line_region, self.action, method, thing)

		return getattr(thing(self.xiki, self.view, self.line_region, self.action, 
			ctx=self), method)(*args, **kargs)


	def full_expand(self, *args, **kargs):
		return self.expand(*args, **kargs)

	def expand(self, *args, **kargs):
#		names =  [ x.name() for x in XikiContext ]
#		names += [ x.name() for x in XikiAction ]

		return None

	def collapse(self, input=None, *args, **kargs):
		return None

	def default_mkdir(self, *args):
		self.xiki.makedirs(os.path.join(self.working_dir, *args))

	def default_cmd_string(self, args):
		r = []
		for a in args:
			if not a.isalnum():
				r.append('"'+a.replace('\\', '\\\\').replace('"', '\\"')+'"')
			else:
				r.append(a)
		return ' '.join(r)

	def default_shell_execute(self, *args):
		return self.execute( *(self.shell + self.cmd_string(args)) )

	def default_setcwd(self, *args):
		x = '/'.join(args)
		# maybe expand shell vars and userdir here
		if os.path.isabs(x):
			self.working_dir = x
		else:
			self.working_dir = os.path.join(self.working_dir, x)

	@classmethod
	def loaded(cls):
		'''implement this to do something after this function is loaded'''

	@classmethod
	def unload(cls):
		'''implement this function if you have to unload anything'''