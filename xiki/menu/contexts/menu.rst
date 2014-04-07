Menu
====

Handle Menus.  Menus are actually simple extensions to aXiki.

::

	class menu(XikiContext):
		''' Todo: find always right set of menu files, e.g. if switching projects
		'''

		def root_menuitems(self):
			menu_files = self.extensions()
			result = set()
			for k in menu_files:
				result.add(os.path.splitext(k.split('/')[0])[0])

			return ''.join(sorted([x+"\n" for x in result if x]))

		def does(self, xiki_path):
			#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
			if not xiki_path: return False

			menu_files = self.extensions()

			menu = None
			i = len(xiki_path)
			log.debug("xiki_path: %s, %s", i, xiki_path)
			while i > 0:
				name = str(xiki_path[:i])

				log.debug("try: %s", name)

				if name not in menu_files:
					i -= 1
					continue
				self.menu_path = xiki_path[:i]
				self.xiki_path = xiki_path[i:]
				menu = menu_files[name]
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

		def _run_menu(self, input, cont):
			func = getattr(self.menu, 'menu')

			if func.__class__.__name__ != 'function':
				func = func.__call__

			if hasattr(func, 'func_code'):
				code = func.func_code
			else:
				code = func.__code__

			if code.co_argcount == 0:
				output = func()
			elif code.co_argcount == 1:
				output = func(self)
			elif code.co_argcount == 2:
				output = func(self, input)
			else:
				raise NotImplementedError("too many arguments")

			return output

		def open(self, input=None, cont=None):
			log.debug("menu is %s", self.menu)
			if self.xiki_path and input:
				# create new menu
				pass


			if hasattr(self.menu, 'menu'):
				output = self._run_menu(input, cont)

				if not isinstance(output, Snippet):
					return find_lines(self.context, output, self.xiki_path)
				else:
					return output

			if isinstance(self.menu, str):
				return self.menu

			return ""

		def expanded(self, s=None):
			if hasattr(self.menu, 'menu'):
				return self._run_menu(input, cont)

			if isinstance(self.menu, str):
				return self.menu

			return ""