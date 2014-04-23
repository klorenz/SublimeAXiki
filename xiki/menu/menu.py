def _get_filename(context, path):
	menu_path = '/'.join(path)

	np = os.path.splitext(menu_path)[0]
	menu_files = context.extensions().nodes

	if np in menu_files:
		fn = menu_files[np].__file__
	else:
		fn = None

	return fn


def open(*path, **kwargs):
	context    = kwargs.get('context')
	menu_files = context.extensions().nodes
	menu_path  = '/'.join(path)

	filename = _get_filename(context, path)
	if filename:
		if not filename.startswith(xiki.user_root):
			pass
			# create userroot_path here 
			# 
		return context.open_file(filename)

	if menu_path:
		slashed_p = menu_path+'/'

	result = set()
	sys.stderr.write("menu_path: %s\n" % menu_path)
	for k,v in menu_files.items():
		if k.startswith(slashed_p):
			k += os.path.splitext(v.__file__)[1]
			n = k[len(slashed_p):].split('/')[0]
			result.add(n)

	if not result:
		assert os.path.splitext(menu_path)[1], "No extension provivded"
		content = kwargs.get('input')
		if not content:
			content = ""

		filename = os.path.join(xiki.user_root, xiki.extension_dir, menu_path)
		return context.open_file(filename, content=content)

	return ''.join(sorted(["- %s\n" % x for x in result if x]))


def close(*path, **kwargs):

	if path:
		context = kwargs.get('context')
		filename = _get_filename(context, path)
		if filename is not None:
			context.close_file(filename)

