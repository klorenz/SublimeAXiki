"""
test

sublime/settings
"""

def settings(*path, ctx=None, input=None):
	import sys, sublime

	modname = 'Preferences Editor.Preferences Editor'

	if modname not in sys.modules:
		return """
			You have to install "Preferences Editor" for managing sublime 
			preferences with aXiki. You find more information at 

			https://sublime.wbond.net/packages/Preferences%20Editor

			Or you can directly install it with

			- sublime/install/Preferences Editor
			"""
	prefedit = sys.modules[modname]

	prefs = prefedit.load_preferences()

	if not path:
		yield "- Preferences\n"
		yield "- Distraction Free\n"
		for k in sorted(prefs.keys()):
			if k not in ['Preferences', 'Distraction Free']:
				yield "- %s\n" % k

	from xiki.util import indent

	def list_data(name):
		platform_default = 'default_'+sublime.platform()

		data = prefs[name]
		for k in sorted(data['default']):
			for d in ('user', platform_default, 'default'):
				if d not in data: continue
				if k in data[d]:
					_data = data[d][k]
					yield "%s:\n%s\n" % (k, indent(_data['description'], "    | ")+"\n"+indent(sublime.encode_value(_data['value']), "    "))+"\n"
					break

	if len(path) == 1:
		name = path[0]
		for x in list_data(name):
			yield x


def install(package_name, ctx):
	if 'Package Control' not in sys.modules:
		return """
			You have to install "Package Control" for managing packages with
			aXiki.  You find more information at

				https://sublime.wbond.net
		"""

	m = sys.modules
	package_installer = m['Package Control.package_control.package_installer']
	package_manager   = m['Package Control.package_control.package_manager']
	thread_progress   = m['Package Control.package_control.thread_progress']

	manager = package_manager.PackageManager()
	thread  = package_installer.PackageInstallerThread(manager, name, None)
	thread.start()
	thread_progress.ThreadProgress(thread, 'Installing package %s' % name,
		'Package %s successfully installed')

