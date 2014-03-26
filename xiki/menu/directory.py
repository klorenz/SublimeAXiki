def menu(ctx):
	import sys, os
	return os.path.dirname(sys.modules[ctx.__class__.__module__].__file__)
