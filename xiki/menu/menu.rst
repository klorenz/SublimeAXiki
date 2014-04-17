Manage Menus
============

- user
- project
- system
- don't panic
  ~~~~~~~~~~~

  Above you see two menus: user and project.  In user section you can browse user-specific menus and in project section project-specific.  In system you can browse system-specific menus.

  If you add a subtree or path in one of sections above, and hit ctrl+enter on it, this menu will be created and opened.  If you hit ctrl+shift+enter and there is content under the node, this content will be initial text for the new menu.

::

	def user(*path):
		root = xiki.user_root
		dir = os.path.join(root, xiki.extension_dir, *path)

		for entry in xiki.listdir(dir):
			yield entry

	def project(*path):
		raise NotImplemented

	def system(*path):
		return "hello world\n"