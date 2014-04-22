Manage Menus
============



- new

- user
- project
- system
- settings
- don't panic
  ~~~~~~~~~~~

  Above you see two menus: user and project.  In user section you can browse user-specific menus and in project section project-specific.  In system you can browse system-specific menus.

  If you add a subtree or path in one of sections above, and hit ctrl+enter on it, this menu will be created and opened.  If you hit ctrl+shift+enter and there is content under the node, this content will be initial text for the new menu.

::

	def user(*path):
		root = xiki.user_root
		dir = os.path.join(root, xiki.extension_dir, *path)
		dir = os.path.normpath(dir)

		for entry in xiki.listdir(dir):
			yield entry

	def project(*path):
		raise NotImplemented

	def system(*path):
		return "hello world\n"

	def settings(*path):
		pass

	def new(*path, input=None):
		root = xiki.user_root
		filename = os.path.join(root, xiki.extension_dir, *path)
		filename = os.path.normpath(filename)

		# default extension if not provided
		if '.' not in os.path.basename(filename):
			filename += xiki.default_extension

		if not input:
			input = None

		xiki.open_file(filename, content=input)

	def edit(*path, input=None):



