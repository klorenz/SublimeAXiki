if __name__ == '__main__':
	import test

import os, re, sys, logging, platform

from .util import *
from .core import XikiContext, INDENT, Snippet

log = logging.getLogger('xiki.contexts')

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

class directory(XikiContext):
	PS1 = "  $ "
	def root_menuitems(self):
		try:
			import sublime
			folders = ''.join([ "~%s/\n" % os.path.basename(x)
				for x in sublime.active_window().folders() ])
		except:
			folders = ''

		return folders+"~/\n./\n/\n"

	def __repr__(self):
		return "<DirectoryContext: %s>" % self.working_dir

	def does(self, node_path):
		# not yet clear if path-part has to end with "/"
		#import spdb ; spdb.start()
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

		p = node_path
	#	p = self.shell_expand('/'.join(p)).replace('\\', '/')
		p = self.shell_expand(''.join(p)).replace('\\', '/')
		log.debug("p: %s", p)
		p = p.split('/')

		log.debug("p: %s", p)
		_root = '/'.join(p[:2])
		log.debug("_root: %s", _root)
		self.file_name = None
		self.file_path = None

		if os.path.isabs(_root):
			self.working_dir = _root
			p = p[2:]

		elif p[0] == '.':
			self.working_dir = self.getcwd()
			p = p[1:]

		elif p[0] == '~':
			self.working_dir = self.shell_expand('~')
			p = p[1:]

		elif p[0].startswith('~'):
			f = p[0][1:].strip('/')
			if f not in self.get_system_dirs():
				if f not in self.get_project_dirs():
					return False

			self.working_dir = self.expand_dir(f)
			
			p = p[1:]
		else:
			return False

		self.working_dir = os.path.join(self.working_dir, *p)

		if not self.isdir(self.working_dir):
			self.file_path   = self.working_dir
			self.working_dir = os.path.dirname(self.working_dir)
			self.file_name   = node_path[-1]

		# log.debug("p: %s", p)
		# log.debug("working_dir: %s", self.working_dir)

		# #import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		# while p:
		# 	working_dir = os.path.join(self.working_dir, p[0])
		# 	log.debug("try working_dir: %s", working_dir)
		# 	if not self.exists(working_dir):
		# 		continue

		# 		break
		# 	else:
		# 		self.working_dir = working_dir
		# 		p = p[1:]

		# log.debug("p: %s, node_path: %s", p, node_path)
		# if p == node_path: return False

		# if node_path.isdir() and p:
		# 	self.mkdir(*p)
		# 	self.working_dir = os.path.join(self.working_dir, *p)
		# 	p = []

		# if not node_path.isdir() and not p:
		# 	self.file_path   = self.working_dir
		# 	self.working_dir = os.path.dirname(self.working_dir)
		# 	self.file_name   = node_path[-1]

		# if not node_path.isdir() and p:
		# 	self.file_path = os.path.join(self.working_dir, *p)
		# 	self.file_name = p[-1]
		# 	p = p[:-1]
		# 	if p:
		# 		self.mkdir(*p)
		# 		self.working_dir = os.path.join(self.working_dir, *p)
		# 		p = []

		# from .path import XikiPath

		# if p:
		# 	self.xiki_path = XikiPath(p)

		# self.node_path = node_path

		# #if p:
		# #	return False

		return True

	def menu(self):
		log.debug("(menu) working_dir: %s", self.working_dir)
		#log.debug("(menu) node_path: %s", self.node_path.path)

		if self.file_path:
			lines = self.open_file(self.file_path)

			if lines:
				if isinstance(lines, str):
					lines = lines.splitlines(1)
				for line in lines:
					yield "| "+line

		else:
			log.debug("listdir of: %s", self.working_dir)
			for entry in self.listdir(self.working_dir):
				yield '+ %s\n' % entry

	def execute(self, *args, **kargs):
		if not kargs.get('cwd'):
			kargs['cwd'] = self.working_dir
		return self.context.execute(*args, **kargs)


class XikiMenuFiles:
	def __init__(self, xiki):
		self.nodes = {}
		self.dirs  = set()
		self.path = set()
		self.xiki = xiki

	def __getitem__(self, name):
		#import spdb ; spdb.start()

		if name in self.nodes:
			return self.nodes[name]

		slashed_name = name + "/"
		result = set()
		for d in self.nodes:
			if d.startswith(slashed_name):
				result.add("+ "+d.split('/', 2)[1]+"/\n")
		return ''.join(result)

	def add_files_from_path(self, root):
		if root in self.path:
			return

		root_len = len(root)+1
		import imp

		if 'xiki.menu' not in sys.modules:
			sys.modules['xiki.menu'] = imp.new_module('xiki.menu')

		for path_name in self.xiki.walk(root):
			node_name = path_name[root_len:]
			name, ext = os.path.splitext(os.path.basename(path_name))
			node_name = os.path.splitext(node_name)[0]

			d = os.path.dirname(node_name)
			parts = d.split('/')
			for i,p in enumerate(parts, start=1):
				_dir = '/'.join(parts[:i])
				if not _dir: continue
				self.dirs.add(_dir)

			mod_name = 'xiki.menu.%s' % '.'.join(parts)
			m = imp.new_module(mod_name)
			m.__file__ = path_name
			m.__dict__['xiki'] = self.xiki

			if ext == '.py':
				source = self.xiki.read_file(path_name)
				code = compile(source, node_name, 'exec')

				exec_code(code, m.__dict__)

				sys.modules[mod_name] = m

				if not hasattr(m,'menu'):
					if m.__doc__:
						m.menu = lambda: m.__doc__
					else:
						def _sym_menu(mod):
							def menu(ctx):
								result = []
								for a in dir(mod):
									if issubclass(a, XikiContext):
										result.append("+ %s\n" % a)
									elif issubclass(a, XikiAction):
										pass
									elif callable(a):
										result.append("+ %s\n" % a)
								return ''.join(result)
							return menu
						m.menu = _sym_menu(m)

			else:
				source = self.xiki.read_file(path_name)

				menu   = []
				pycode = []
				line_offset = 0
				is_python = False
				
				for i,line in enumerate(source.splitlines(1)):
					if is_python:
						if not line.strip():
							pycode.append(line)
						else:
							indent = get_indent(line)

							if not len(indent):
								code = compile("\n"*line_offset +''.join(pycode), filename=path_name, mode='exec')
								exec_code(code, m.__dict__)
								is_python = False
								menu.append(line)
								pycode = []
								continue
							pycode.append(line)
						continue

					try:
						if line.startswith('class ') or line.startswith('def '):
							compile(line)
							pycode.append(line)
							is_python = True
							line_offset = i

						else:
							menu.append(line)

					except (OverflowError, SyntaxError, ValueError):
						menu.append(line)
						continue

				if menu:
					def _menu(menu):
						return lambda: ''.join(menu)
					m.menu = _menu(menu)

			self.nodes[node_name] = m
			for k,v in self.nodes.items():
				log.debug("%s: %s" %(k,v.__file__))

		self.path.add(root)

	def __contains__(self, name):
		return name in self.nodes or name in self.dirs

	def __iter__(self):
		for n in self.dirs.union(set(self.nodes.keys())):
			yield n

	def update(self):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		for menu_dir in self.xiki.get_search_path('menu'):
			self.add_files_from_path(menu_dir)


g_xiki_menu_files = None

class menu(XikiContext):
	''' Todo: find always right set of menu files, e.g. if switching projects
	'''

	def root_menuitems(self):
		global g_xiki_menu_files
		if g_xiki_menu_files is None:
			g_xiki_menu_files = XikiMenuFiles(self.get_xiki())

		g_xiki_menu_files.update()

		result = set()
		for k in g_xiki_menu_files:
			result.add(os.path.splitext(k.split('/')[0])[0])

		return ''.join(sorted([x+"\n" for x in result if x]))

	def does(self, xiki_path):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		if not xiki_path: return False

		global g_xiki_menu_files
		if g_xiki_menu_files is None:
			g_xiki_menu_files = XikiMenuFiles(self.get_xiki())

		g_xiki_menu_files.update()

		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

		menu = None
		i = len(xiki_path)
		while i > 0:
			name = str(xiki_path[:i])

			if name not in g_xiki_menu_files:
				i -= 1
				continue
			self.menu_path = xiki_path[:i]
			self.xiki_path = xiki_path[i:]
			menu = g_xiki_menu_files[name]
			break

		self.menu = menu

		if menu is not None:
			return True

		if menu is None:
#			if self.action.startswith('collapse'):
#				self.dispatch_path = node_path
#				return True

			return False

		return True

	def open(self, input=None, cont=None):
		#import spdb ; spdb.start()
		if hasattr(self.menu, 'menu'):
			func = getattr(self.menu, 'menu')
			if func.func_code.co_argcount == 0:
				output = func()
			elif func.func_code.co_argcount == 1:
				output = func(self)
			elif func.func_code.co_argcount == 2:
				output = func(self, input)
			else:
				raise NotImplementedError("too many arguments")

			if not isinstance(output, Snippet):
				return find_lines(self.context, output, self.xiki_path)
			else:
				return output

		if isinstance(self.menu, str):
			return self.menu

	def full_expand(self, s=None):
		if hasattr(self.menu, 'menu'):
			return getattr(self.menu, 'menu')()
		if isinstance(self.menu, str):
			return self.menu
		return ""


#class settings(XikiContext):
#	NAME = 'settings'

class xiki(XikiContext):

	def menu(self):
		if platform.system() == 'Windows':
			raise SystemError("Platform Windows is not supported by xiki.")


class ssh(XikiContext):
	PATTERN = re.compile(r'''(?x) ^
		(?P<cmd>
			(?P<user>[\w\-]+) @ (?P<host>[\w\-]+(\.[\w\-]+)*) 
			(?::(?P<port>\d+))?)
		(?::(?P<extra>.*))?$''')

	SETTINGS = '''
	- |remote_shell: bash

	  Specify remote shell to be executed on shell command.

	  See also:
	  - @docs/shell
	'''

	def does(self, xiki_path):
		r = XikiContext.does(self, xiki_path)
		if not r: return r

		#import spdb ; spdb.start()
		log.debug("mob: %s", self.mob.groupdict())

		extra = self.mob.group('extra')
		log.debug("extra: %s", extra)
		if extra:
			# handle path$ some command
			pass

		if not self.xiki_path:
			self.xiki_path.insert(0, "~/")

		elif not self.xiki_path.isfilepath():
			log.debug("test xiki_path %s", self.xiki_path)

			# determine if this is still a filepath
			try:
				self.subcontext = self.xiki_path.context(context=self)

			except LookupError:
				log.warning("could not lookup context for %s" % self.xiki_path)
				self.xiki_path.insert(0, "~/")

		if not self.subcontext:
			self.subcontext = self.xiki_path.context(self)

		return True



	def get_ssh_cmd(self):
		cmd = [ 'ssh' ]
		ssh_data = self.ssh_data

		if ssh_data['port']:
			cmd += [ '-p', ssh_data['port'] ]
		cmd += [ '%(user)s@%(host)s' % ssh_data ]
		return cmd

	def listdir(self, path=None):
		'''usually path is not optional, but we allow it not to be set to 
		list the default ssh landing directory from menu'''

		if path is None:
			output = self.execute('ls', '-F')
		else:
			output = self.execute('ls', '-F', path)

		for line in output:
			line = line.strip()
			if not line: continue
			log.debug("line: %s", line)
			if line[-1] in "*=>@|":
				line = line[:-1]
			yield line

	def read_file(self, path, count=None):
		if count is not None:
			return self.execute('head', '-n', str(count), path)
		else:
			return self.execute('cat', path)

	def open_file(self, path, opener=None, bin_opener=None, text_opener=None):
		raise NotImplementedError("Open file via SSH not yet implemented")
		cache_name = '%(user)s@%(host)s' % ssh_data
		return self.context.open_file( self.cached_file(cache_name, path) )

	def exists(self, path):
		output = ''.join([x for x in 
			self.execute('[ -e %s ] && echo y || echo n' % cmd_string(path))])
		return output.strip() == 'y'

	def get_project_dirs(self):
		return []

	def get_system_dirs(self):
		return []

	def shell_expand(self, name):
		name = str(name)

		if "$" not in name and "~" not in name:
			return name

		home_dir = self.get_static('~')
		if not home_dir:
			home_dir = ''.join([x for x in self.execute('echo', '~')]).strip()
			self.set_static('~', home_dir)

		if name.startswith('~'):
			name = home_dir + name[1:]

		if "$" not in name:
			return name

		return ''.join([x for x in self.execute('echo', name)]).strip()

	def isdir(self, path):
		output = ''.join([x for x in 
			self.execute('[ -d %s ] && echo y || echo n' % cmd_string(path))])
		return output.strip() == 'y'

	def walk(self, root):
		for line in self.execute('find', root, '-type', 'f'):
			yield line

	def makedirs(self, *path):
		p = cmd_string('/'.join(list(path)))
		self.execute('[ ! -e %s ] && mkdir -p %s' % (p, p))

	def execute(self, *args, **kargs):
		working_dir = kargs.get('cwd')
		cmd = self.get_ssh_cmd()

#		if not working_dir:
#			if self.xiki_path:


		if working_dir:
			args = cmd_string(args)
			cwd  = cmd_string(working_dir)
			rcmd = 'cd %s && %s' % (cwd, args)
			rcmd = cmd_string(rcmd)
			return self.context.execute(*(cmd + ['sh', '-c', rcmd ]))
		else:
			return self.context.execute(*(cmd + list(args)))

	def menu(self):
		return [ '+ ~/\n', '+ /\n' ]

	# def menu(self):
	# 	if self.node_path.isdir():
	# 		for line in self.execute('ls', '-F'):
	# 			line = line.strip()
	# 			if not line: continue
	# 			log.debug("line: %s", line)
	# 			if line[-1] in "*=>@|":
	# 				line = line[:-1]

	# 			yield '+ %s\n' % line

	def shell_execute(self, *args, **kargs):

		working_dir = kargs.get('cwd')
		cmd = self.get_ssh_cmd()

		args = [self.remote_shell, "-c", cmd_string(cmd_string(args))]

		if working_dir:
			args = cmd_string(args)
			cwd  = cmd_string(working_dir)
			rcmd = 'cd %s && %s' % (cwd, args)
			rcmd =  cmd_string(rcmd)
			return self.context.execute(*(cmd + ['sh', '-c', rcmd]))
		else:
			return self.context.execute(*(cmd + args))

class root(XikiContext):
	def root_menuitems(self):
		return None

	def does(self,xiki_path):
		return not xiki_path

	def menu(self):
		result = []
		for ctx in self.contexts():
			c = ctx(self)
			items = c.root_menuitems()
			if items:
				result.append(unindent(items))

		result.sort()
		return result


class XikiShell(XikiContext):
	PATTERN = re.compile(r'^\s*\$\$\s+(.*)')

	def open(self, input=None, cont=False):
		return self.context.shell_execute(self.mob.group(1))

class XikiExec(XikiContext):
	PATTERN = re.compile(r'^\s*\$\s+(.*)')
	PS1     = "\$ "

	COMMAND_RE = re.compile(r'''(?x)
		(?:^|(?<=\s))
		(?:

		"((?:\\.|[^"\\]+)*)"
		| '((?:\\.|[^"\\]+)*)'
		| (\S+)

		)
		''')

	def parse_command(self, s):
		result = []
		for m in self.COMMAND_RE.finditer(s):
			dq, sq, nq = m.groups()
			if dq:
				result.append(dq.replace('\\"', '"').replace('\\\\', '\\'))
			elif sq:
				result.append(sq.replace("\\'", "'").replace('\\\\', '\\'))
			else:
				result.append(nq)

		return result

	def open(self, input=None, cont=None):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		s = self.mob.group(1)
		log.debug("%s: %s, %s", self, s, self.node_path)

		#if self.node_path:
		#	self.context.mkdir(*self.node_path)
		#	self.context.setcwd('/'.join(self.node_path))

		return self.context.execute(*self.parse_command(s))

class XikiPython(XikiContext):
	PATTERN = re.compile(r'>>> (.*)')
	PS1     = ">>> "

	def open(self, input=None, cont=None):
		s = self.mob.group(1)
		_stderr = sys.stderr
		_stdout = sys.stdout

		try:
			from io import StringIO
		except ImportError:
			from cStringIO import StringIO

		_output = StringIO()

		r = None

		sys.stderr = _output
		sys.stdout = _output

		is_exec = False
		try:
			code = compile(s, "<string>", mode='eval')
		except SyntaxError:
			code = compile(s+"\n", "<string>", mode='exec')
			is_exec = True

		try:
			if is_exec:
				exec_code(code, sys.modules['__main__'].__dict__)
			else:
				r = eval(s, sys.modules['__main__'].__dict__)
		except:
			import traceback
			traceback.print_exc()
		finally:
			sys.stderr = _stderr
			sys.stdout = _stdout

		_output.seek(0)

		import pprint
		if r is not None:
			return [ pprint.pformat(r) ]
		else:
			return _output.readlines()
