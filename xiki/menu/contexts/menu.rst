Menu
====

Handle Menus.  Menus are actually simple extensions to aXiki.

You have multiple opportunities to add active content to a menu.

::

	class menu(XikiContext):
		''' Todo: find always right set of menu files, e.g. if switching projects
		'''

		def root_menuitems(self):
			menu_files = self.extensions()
			result = set()
			for k in menu_files:
				if k.startswith('/'):
					result.add(k[1:])
				else:
					result.add(os.path.splitext(k.split('/')[0])[0])

			return ''.join(sorted([x+"\n" for x in result if x]))

		def does(self, xiki_path):
			#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

			#import spdb ; spdb.start()
			if not xiki_path: return False

			#xiki_path.split_elements()
			import logging
			log.setLevel(logging.DEBUG)

			menu_files = self.extensions()

			menu = None

			path = "/".join(xiki_path).split("/")
			i = len(path)
			log.debug("menu path: %s, %s", i, path)

			while i > 0:
			#	name = str(xiki_path[:i])
				name = "/".join(path[:i])

				log.debug("try: %s", name)

				if name not in menu_files:
					i -= 1
					continue

				self.menu_path = XikiPath(path[:i])
				self.xiki_path = XikiPath(path[i:])
				menu = menu_files[name]
				break

			log.debug("name: %s", name)

			self.menu = menu

			if menu is not None:
				return True

			if menu is None:

		#			if self.action.startswith('collapse'):
		#				self.dispatch_path = node_path
		#				return True

				return False

			return True

		def _run_menu(self, input, cont, xiki_path=None, function='menu'):
			reserved = 0

			menu_func = self.menu
			from xiki.util import slugipy
			if xiki_path is None:
				xiki_path = []

			while xiki_path:
				func_name = xiki_path[0]
				if hasattr(menu_func, func_name):
					menu_func = getattr(menu_func, func_name)
					xiki_path = xiki_path[1:]
				else:
					func_name = slugipy(func_name)
					if hasattr(menu_func, func_name):
						menu_func = getattr(menu_func, func_name)
						xiki_path = xiki_path[1:]
					else:
						break

			if hasattr(menu_func, function):
				menu_func = getattr(menu_func, function)

			while xiki_path:
				func_name = xiki_path[0]

				if hasattr(menu_func, func_name):
					menu_func = getattr(menu_func, func_name)
					xiki_path = xiki_path[1:]
				else:
					func_name = slugipy(func_name)
					if hasattr(menu_func, func_name):
						menu_func = getattr(menu_func, func_name)
						xiki_path = xiki_path[1:]
					else:
						break

			if menu_func.__class__.__name__ != 'function':
				menu_func = menu_func.__call__

			if hasattr(menu_func, 'func_code'):
				code = menu_func.func_code
			else:
				code = menu_func.__code__

			kwargs = {}

			argcount = code.co_argcount
			argnames = code.co_varnames[:argcount]

			if 'context' in argnames:
				argcount -= 1
				kwargs['context'] = self

			if 'ctx' in argnames:
				argcount -= 1
				kwargs['ctx'] = self

			if 'input' in argnames:
				argcount -= 1
				kwargs['input'] = input

			gets_slurpy_args   = code.co_flags & 0x04
			gets_slurpy_kwargs = code.co_flags & 0x08

			if gets_slurpy_kwargs:
				kwargs['input']   = input
				kwargs['context'] = self
				kwargs['ctx'] = self

			args = []
			if gets_slurpy_args:
				args     = xiki_path
				argcount = len(xiki_path)
			elif argcount:
				if argcount == len(xiki_path):
					args = [ x for x in xiki_path ]

				args = xiki_path[:argcount]

			log.debug("run: %s(%s, %s)", menu_func.__name__, args, kwargs)
			output = menu_func(*args, **kwargs)
			if isinstance(output, str):
				if output.startswith("\n"):
					from xiki.util import unindent
					output = unindent(output)

			return output, xiki_path[argcount:]

		def open(self, input=None, cont=None):
			log.debug("menu is %s", self.menu)
			if self.xiki_path and input:

				# create new menu
				pass

			for name in ('open', 'menu'):
				if hasattr(self.menu, name):
					output, xiki_path = self._run_menu(input, cont, self.xiki_path, function=name)

					if not isinstance(output, Snippet):
						if not output:
							return ''

						if not isinstance(output, str):
							from xiki.parser import assemble
							output = assemble(output)

						if not isinstance(output, str):
							output = ''.join([x for x in output])

						from xiki.util import find_lines
						return find_lines(self.context, output, xiki_path)
					else:
						return output

			if isinstance(self.menu, str):
				return self.menu

			return ""

		def close(self, input=None):
			log.debug("close called")
			if hasattr(self.menu, 'close'):
				log.debug("has close: %s", self.xiki_path)

				output, xiki_path = self._run_menu(input=input, cont=None, xiki_path=self.xiki_path, function='close')
				return output

		def expanded(self, s=None):
			if hasattr(self.menu, 'menu'):
				return self._run_menu(input, cont)

			if isinstance(self.menu, str):
				return self.menu

			return ""

