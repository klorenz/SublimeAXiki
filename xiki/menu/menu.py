def menu(*path, **kwargs):
	context = kwargs.get('context')

	#context=None, input=None):
	menu_path = '/'.join(path)
	sys.stderr.write("menu_path: %s\n" % menu_path)

	np = os.path.splitext(menu_path)[0]
	menu_files = context.extensions().nodes

	if np in menu_files:
		fn = menu_files[np].__file__
		if not fn.startswith(xiki.user_root):
			pass
			# create userroot_path here 
			# 
		return context.open_file(menu_files[np].__file__)

	if menu_path:
		menu_path += '/'

	result = set()
	sys.stderr.write("menu_path: %s\n" % menu_path)
	for k,v in menu_files.items():
		sys.stderr.write("k: %s\n" % k)
		sys.stderr.write("v: %s\n" % v)
		if k.startswith(menu_path):
			k += os.path.splitext(v.__file__)[1]
			n = k[len(menu_path):].split('/')[0]
			sys.stderr.write("n: %s\n" % n)
			result.add(n)

	return ''.join(sorted(["- %s\n" % x for x in result if x]))