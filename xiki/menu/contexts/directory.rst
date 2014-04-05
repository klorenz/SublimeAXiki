Directory
=========

This context lets you browse directory trees.  Commands executed in this context are run in current directory as working directory.

Simply start a line with one of following: 

	- ``/`` — for root
	- ``~/`` — for home directory
	- ``./`` — for directory of current view
	- ``~PROJECT_NAME/`` — for a current project directory.

You can find out your current Project directories: 

	>>> xiki.get_project_dirs()

::

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
			log.debug("directory.execute(%s, %s)", args, kargs)
			return self.context.execute(*args, **kargs)