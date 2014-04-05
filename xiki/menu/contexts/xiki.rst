Original Xiki
=============

This handler provides commandline interface to original Xiki_.

.. _Xiki: http://xiki.org

::

	class xiki(XikiContext):

		def menu(self):
			import platform
			if platform.system() == 'Windows':
				raise SystemError("Platform Windows is not supported by xiki.")

			xiki_menu = ''.join([x for x in XikiPath('$ ls `xiki directory`/menu').open(self)])

			for x in xiki_menu.splitlines():
				yield "+ "+os.path.splitext(x)[0]+"/\n"

		def open(self, input=None, cont=None):
			if self.xiki_path:
				return XikiPath('$ xiki "%s"' % self.xiki_path).open(self, input=input, cont=cont)
			else:
				return self.menu()

