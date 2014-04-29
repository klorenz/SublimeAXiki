# vim: fileencoding=utf8

if __name__ == '__main__':
	import test

import re, os, logging

STRING_RE         = re.compile(r'"(\\.|[^"\\]+)*"')
INDEX_RE          = re.compile(r'\[(\d+)\](?=/|$)')
BULLET_RE         = re.compile(r'[\-–—+]\s')
CONTEXT_RE        = re.compile(r'[@$]')
NODE_LINE_1       = re.compile(r'(?x) (?P<indent>\s*) @ \s* (?P<node>.*) ')
INDENT_RE         = re.compile(r'^[\x20\t]*')

FREE_LINE         = re.compile(r'(?x) (?P<indent>\s*) (?P<node>[^\-–—+].*)')
# NODE_LINE_2       = re.compile(r'(?x) (?P<indent>\s*) (?P<node>\$ .*) ')
NODE_LINE_COMMENT = re.compile(r'(?x) \s+(?:--|—|–)\s+.*$')
PATH_SEP          = re.compile(r'(?:/| -> | → )')

BUTTON_RE         = re.compile(r'^(\s*)\[(\w+)\](?:\s+\[\w+\])*\s*$')

def match_node_line(s):
	from .util import get_indent
	#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

	r = {}
	m = NODE_LINE_1.match(s)
	if m:
		return {
			'indent': m.group('indent'),
			'ctx'   : '@',
			'node'  : [ m.group('node') ],
		}

	# if FREE_LINE.match(s):
	# 	return {
	# 		'indent': m.group('indent'),
	# 		'ctx'   : '@',
	# 		'node'  : [ m.group('node') ],
	# 	}

	r = { 'indent' : get_indent(s), 'ctx': None}
	m = NODE_LINE_COMMENT.search(s)
	if m:
		s = s[:m.start()]

	s = s.strip()

	if not BULLET_RE.match(s):
		if not r['indent']:
			r['node'] = [s]
			return r

		return None

	s = s[1:].strip()

	if s.startswith('@'):
		s = s[1:].strip()
		r['ctx'] = '@'
	elif s.startswith('$ '):
		r['ctx'] = '$'
	elif s.startswith('``') and s.endswith('``'):
		s = s[2:-2]
		r['ctx'] = '``'
	elif s.startswith('`') and s.endswith('`'):
		s = s[1:-1]
		r['ctx'] = '`'
	elif s.startswith('`') and s.endswith('`_'):
		s = s[1:-2]
		r['ctx'] = '`'

	if not s.startswith('$'):
		if s.endswith("/"):
			s = s[:-1]
			r['node'] = re.split(PATH_SEP, s)
			r['node'][-1] += '/'
		else:
			r['node'] = re.split(PATH_SEP, s)

		for i in range(len(r['node'])-1):
			r['node'][i] += '/'
	else:
		r['node'] = [s]

	return r

log = logging.getLogger('xiki.path')

class XikiError(Exception):
	pass


# compare http://stackoverflow.com/questions/2673651/inheritance-from-str-or-int
class XikiInput:
	def __init__(self, value, action=None):
		self.value = value
		self.action = action

	def __getattr__(self, name):
		return getattr(self.value, name)

	# def __eq__(self, x):
	# 	return self.value == x.value and self.action == x.action

class XikiPath:
	def __init__(self, path):
		self.paths = None
		self.path  = None

		# if rootctx is None:
		# 	from .core import XikiContext as rootctx

		# self.rootctx = rootctx
		log.debug("")

		self.input  = None

		if isinstance(path, str):
			if "\n" in path:
				self.paths, self.input = self.path_from_tree(path)
			else:
				self.paths = self.parse(path)

			log.debug("%s -> %s", repr(path), self.paths)
		else:
			self.path = [ isinstance(x, tuple) and x or (x,0) for x in path ]


	def __iter__(self):
		if self.paths:
			for p in self.paths:
				yield p
		else:
			if self.path:
				for p in self.path:
					# if '/' in p[0] and not "://" in p[0]:
					# 	for x in p[0].split('/'):
					# 		yield x
					# else:
						yield p[0]

	def __len__(self):
		if self.paths:
			return len(self.paths)
		if self.path:
			return len(self.path)
		return 0

	def __nonzero__(self):
		if self.paths:
			return bool(self.paths)
		return bool(self.path)

	# def split_elements(self, sep="/"):
	# 	new_path = []
	# 	path = self.path
	# 	for p in self.path:
	# 		new_path += p.split(sep)
	# 	self.path[:] = new_path
	# 	return new_path

	def insert(self, index, path):
		if not isinstance(path, tuple):
			return self.path.insert(index, (path, 0))
		else:
			return self.path.insert(index, path)

	def parse(self, path):
		paths = [[]]

		path = os.path.expandvars(path)

		while path:
			index = 0

			if BULLET_RE.match(path):
				path = path[2:]

			if path.startswith('@'):
				paths.append([])
				path = path[1:].lstrip()

				if path.startswith('$'):
					paths[-1].append( (path, 0) )
					path = ''
					break

			if path.startswith('$'):
				paths.append([(path,0)])
				path = ''
				break

			if path.startswith('"'):
				m = STRING_RE.match(path)
				if m:
					p = m.group(0)
					_path = path[m.end():]

					if _path.startswith('['):
						m = INDEX_RE.match(_path)
						if m:
							index = int(m.group(1))
							_path = _path[m.end():]

					if _path.startswith('/'):
						path = _path[1:]
						p = p.replace('\\"', '"').replace('\\\\', '\\')
						paths[-1].append( (p, index) )
						continue

			append_slash = False

			if '/' in path:
				p, path = path.split('/', 1)
				append_slash = True
			else:
				p = path
				path = ''

			if p.endswith(']'):
				m = INDEX_RE.search(p)
				if m:
					index = int(m.group(1))
					p = p[:m.start()]

			if append_slash:
				p += "/"

			paths[-1].append((p, index))

		return paths

	def path_from_tree(self, lines):
		'''assumes to get a subtree, which is to be processed.

		if you have a full tree like::

			foo/
			  - first
			    + glork
			  - second
			  - third

		And you want to get expanded the "glork", you have to 
		pass::

			foo/
			  - first
			    + glork

		Which results in::

			foo/first/glork
		'''
		from .util import unindent

		node_paths = [[]]
		old_line = None
		indent = None
		from itertools import chain

		lines = lines.rstrip() + "\n"

		log.debug("lines: %s" % lines)
		collect_lines = False
		input, action = None, None

		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		for line in chain(reversed(lines.splitlines(1)), [None]):

			# handle line continuations
			process_line = None
			if line is None:
				process_line = old_line
			elif line.endswith("\\\n"):
				line = line[:-2] + old_line.lstrip()
			else:
				process_line = old_line

			old_line = line

			if process_line is None: continue

			# start processing of line
			line = process_line
			# if 'hardcopy' in line:
			# 	import rpdb2 ; rpdb2.start_embedded_debugger('foo')

			if collect_lines:
				if not line.strip():
					input.append(indent+"\n")
					continue

				if line.startswith(indent):
					input.append(line)
					continue

				input = unindent(''.join(input))
				collect_lines = False
				indent = None

			if indent is None:
				m = BUTTON_RE.match(line)
				if m:
					input = []
					indent, action = m.groups()
					collect_lines = True
					continue

			mob  = match_node_line(line)

			if not mob:
				if indent is None:
					m = INDENT_RE.match(line)
					indent = m.group(0)
					node_paths[-1].append( (line.strip(),0) )
					node_paths.append([])

				continue

			if not line.strip():
				continue

			_indent = mob['indent']

			s = mob['node'][0]
			nodes = mob['node'][1:]

			for n in nodes:
				node_paths[-1].append( (n, 0) )

			if indent is None:
				indent = _indent
				if not s: break

				node_paths[-1].append( (s, 0))
				if mob['ctx']:
					node_paths.append([])
				continue

			if len(_indent) == 0:
				node_paths[-1].append( (s, 0) )
				break

			if len(_indent) == len(indent):
				if node_paths[-1]:
					if node_paths[-1][-1][0] == s:
						s, i = node_paths[-1][-1]
						node_paths[-1][-1] = s, i+1
						continue

			if 0 < len(_indent) < len(indent):
				node_paths[-1].append( (s, 0) )
				if mob['ctx']:
					node_paths.append([])
				indent = _indent

		if not node_paths[-1]:
			node_paths = node_paths[:-1]

		for np in node_paths:
			np.reverse()

		node_paths.reverse()
		log.debug("node_paths: %s", node_paths)
		if input is not None:
			input = XikiInput(value=input, action=action)

		return node_paths, input

	def __str__(self):
		result = []
		if self.paths:
			for p in self.paths:
				result.append("@"+str(XikiPath(p)))
		else:
			for p in self:
				if p.endswith('/'):
					p = p[:-1]
				if "/" in p or p.startswith('@'):
					p = '"%s"' % p.replace("\\", "\\\\").replace('"', '\\"')
				result.append(p)

		return "/".join(result)

	def __repr__(self):
		return "XikiPath("+repr(str(self))+")"

	def __getitem__(self, thing):
		if self.paths:
			return self.paths[thing]
		else:
			if isinstance(thing, slice):
				return XikiPath(self.path[thing])
			else:
				return self.path[thing][0]

	def isdir(self):
		'''return true if this is a directory.'''

		if self.paths:
			path = self.paths[-1]
		else:
			path = self.path

		if not path: return False

		return path[-1][0].endswith('/')

	def isfilepath(self):
		'''if this is a path in file system, return true, else false'''
		if self.paths:
			p = self.paths[0]
		else:
			p = self.path

		if not p:
			return False

		if p[0][0] in ('~', '~/', '.', './', '/'):
			return True

		return False


	def context(self, context=None):
		'''returns a context for this xiki_path'''

		# nested contexts
		if self.paths:
			for p in self.paths:
				context = XikiPath(p).context(context)
			return context

		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

		#from .core import XikiContext

		# single context for this path
		for xiki_context in context.contexts():
			ctx = None
			try:
				ctx = xiki_context(ctx=context)
				log.debug("try %s for %s", ctx, self)

				if ctx.does(self):
					log.info("%s does %s", ctx, self)
					return ctx.get_context()
			except:
				log.error("error querying context %s for doing %s", ctx, 
					self, exc_info=1)

	def complete(self, context, prefix, before="", after=""):
		context = self.context(context)
		log.debug("complete: %s, %s <- %s", prefix, context, self)
		return context.complete(prefix, before=before, after=after)

	def open(self, context, input=None, cont=False):
		context = self.context(context)
		if input is None:
			input = self.input
		log.debug("open: %s <- %s", context, self)
		if not isinstance(input, XikiInput):
			input= XikiInput(input)

		return context.open(input=input, cont=cont)

	def expanded(self, context, input=None):
		context = self.context(context)
		if not isinstance(input, XikiInput):
			input = XikiInput(input)
		log.debug("open: %s <- %s", context, self)
		return context.expanded(input=input, cont=cont)

	def close(self, context, input=None):
		context = self.context(context)
		log.debug("close: %s <- %s", context, self)
		if not isinstance(input, XikiInput):
			input = XikiInput(input)
		return context.close(input=input)
