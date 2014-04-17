def menu(context):
	import sys, os
	mod_name = context.__class__.__module__
	return os.path.dirname(sys.modules[mod_name].__file__)
