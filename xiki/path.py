# vim: fileencoding=utf8

if __name__ == '__main__':
	import test

import re, os, logging

STRING_RE = re.compile(r'"(\\.|[^"\\]+)*"')
INDEX_RE  = re.compile(r'\[(\d+)\](?=/|$)')

BULLET_RE = re.compile(r'[\-–—+]\s')
CONTEXT_RE = re.compile(r'[@$]')

log = logging.getLogger('xiki.path')

class XikiError(Exception):
	pass

class XikiPath:
	def __init__(self, path, rootctx=None):
		self.paths = None
		self.path  = None

		if rootctx is None:
			from .core import XikiContext as rootctx

		self.rootctx = rootctx

		if isinstance(path, str):
			if "\n" in path:
				self.paths = self.path_from_tree(path)
			else:
				self.paths = self.parse(path)
		else:
			self.path = path

	def __iter__(self):
		if self.paths:
			for p in self.paths:
				yield p
		else:
			for p in self.path:
				yield p[0]

	def __len__(self):
		return len(self.path)

	def __nonzero__(self):
		if self.paths:
			return bool(self.paths)
		return bool(self.path)

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

			if '/' in path:
				p, path = path.split('/', 1)
			else:
				p = path
				path = ''

			if p.endswith(']'):
				m = INDEX_RE.search(p)
				if m:
					index = int(m.group(1))
					p = p[:m.start()]

			paths[-1].append((p+"/", index))

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
		from .util import get_indent

		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

		node_paths = [[]]

		indent = None
		for line in reversed(lines.splitlines(1)):
			_indent = get_indent(line)

			s = line.strip()

			if indent is None:
				indent = _indent
				if not s:
					break

				if BULLET_RE.match(s) or s[0] == '@':
					s = s[1:].strip()
				node_paths[-1].append( (s, 0) )
				continue

			if len(_indent) == 0:
				node_paths[-1].append( (s, 0) )
				break

			if len(_indent) == len(indent):
				if BULLET_RE.match(s):
					if node_paths[-1]:
						s = s[1:].strip()
						if node_paths[-1][-1][0] == s:
							s, i = node_paths[-1][-1]
							node_paths[-1][-1] = s, i+1
							continue

			if 0 < len(_indent) < len(indent):
				if BULLET_RE.match(s):
					s = s[1:].strip()
					node_paths[-1].append( (s, 0) )
				if s[0] == '@':
					node_paths.append([])
					node_paths[-1].append( (s[1:].strip(), 0) )
				if s[0] == '$':
					node_paths[-1].append( (s, 0) )

				indent = _indent

		for np in node_paths:
			np.reverse()

		node_paths.reverse()
		log.debug("node_paths: %s", node_paths)
		return node_paths

	def __str__(self):
		result = []
		if self.paths:
			for p in self.paths:
				result.append("@"+str(XikiPath(p)))
		else:
			for p in self:
				if "/" in p or "@" in p:
					p = '"%s"' % p.replace("\\", "\\\\").replace('"', '\\"')
				result.append(p)
		return "/".join(result)

	def __getitem__(self, thing):
		if self.paths:
			return self.paths[thing]
		else:
			if isinstance(thing, slice):
				return XikiPath(self.path[thing])
			else:
				return self.path[thing][0]

	def isdir(self):
		if self.paths:
			path = self.paths[-1]
		else:
			path = self.path

		if not path: return False

		return path[-1][0].endswith('/')

	def context(self, xiki, context=None):
		'''returns a context for this xiki_path'''

		# root context
		if context is None:
			context = self.rootctx(xiki)

		# nested contexts
		if self.paths:
			for p in self.paths:
				context = XikiPath(p).context(xiki, context)
			return context

		from .core import XikiContext

		# single context for this path
		for xiki_context in XikiContext:
			ctx = xiki_context(xiki, ctx=context)
			log.debug("try %s for %s", ctx, self)
			if ctx.does(self):
				log.info("%s does %s", ctx, self)
				return ctx

		raise XikiError("context not found for %s" % self)

	def open(self, xiki, context=None, input=None, cont=False):
		context = self.context(xiki, context)
		return context.open(input=input, cont=cont)

	def close(self, xiki, context=None, input=None):
		context = self.context(xiki, context)
		return context.close(input=input)
