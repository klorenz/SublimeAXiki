'''Entry point for xiki.py'''

if __name__ == '__main__':
	import test

def open(path, input=None):
	'''opens path.  if input is given, this is usually interpreted as
	"store input to path and get the output of this operation".
	'''

	from .path import XikiPath
	xiki_path = XikiPath(path)
	return xiki_path.open(input=input)

def close(path, input=None):
	'''closes a path.  if input is given, this is usually interpreted as
	"store input to path and do not care about the output".
	'''
	from .path import XikiPath
	xiki_path = XikiPath(path)
	return xiki_path.close(input=input)


def sheet(content, point=None, action=None):
	'''you can also let xiki handle a worksheet for you.  point may be either
	a integer or a pair of (line, col), action specifies the action you want
	to do there.
	'''

	if not isinstance(point, tuple):
		raise NotImplementedError("please pass (line, col)")

	line, col = point
	lines = content.splitlines(1)
	start_lines = lines[:line]

	# ... and so on ...


def main():
	import argparse

	parser = argparse.ArgumentParser(
		description = "a very simple xiki clone",
		epilog = __doc__
		)

	# common arguments

	parser.add_argument(
		'-r', '--root',
		default = "~",
		help = "root of xiki configuration"
		)

