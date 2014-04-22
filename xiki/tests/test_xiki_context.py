if __name__ == '__main__':
	import sys
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test

from unittest import TestCase, skip

from ..path import XikiPath
from ..core import XikiContext, ConsoleXiki

class MyXiki(ConsoleXiki):
	def getcwd(self):
		return "/foo"
	def makedirs(self, name):
		return None
	def execute(self, *args, **kargs):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		print("args: %s, kargs: %s" % (args, kargs) )

		if args[-1].startswith('[ -d /foo/bar '):
#			import rpdb2 ; rpdb2.start_embedded_debugger('foo')
			return ["y\n"]

		if args[-1].startswith('~/'):
			return ["/home/"+args[-1][2:]]

		return ["execute(%s, %s)" % (repr(args), repr(kargs))]


class TestXikiContext(TestCase):

	def _test_xiki_path(self, path, expected):
		xiki = MyXiki()
		xiki.extensions()
		x = XikiPath(path).open(xiki)
		if isinstance(x, str): x = [x]
		self.assertEquals([y for y in x], expected)

	def test_ssh_rootmenu(self):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		self._test_xiki_path("user@host.com:1234", [
			"+ execute(('ssh', '-p', '1234', 'user@host.com', 'ls', '-F'), "
			"{})\n" 
			])

	def test_ssh_home(self):
		self._test_xiki_path("user@host.com:1234/foo/bar", [
			"+ execute(('ssh', '-p', '1234', 'user@host.com', 'ls', '-F'), "
			"{})\n" 
			])

	# @skip
	# def test_ssh_root(self):
	# 	self._test_xiki_path("user@host.com:1234//foo/bar", [
	# 		"+ execute(('ssh', '-p', '1234', 'user@host.com', 'ls', '-F', '/foo/bar'), "
	# 		"{})\n" 
	# 		])


	def test_execute(self):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		self._test_xiki_path("/foo/bar/$ ls -l",[
		 	"execute(('ls', '-l'), {'input': None, 'cwd': '/foo/bar'})"
			])

	def test_root_menu(self):
		self._test_xiki_path("", [
			'directory\ndocs\nip\ntest\ntodo\n',
			'exec\n',
			'shell\n',
			'ssh\n',
			'xiki\n',
			'~/\n./\n/\n'
			])

	def test_menu(self):
		import sys, os
		self._test_xiki_path("directory/", [ 
			os.path.dirname(sys.modules[XikiContext.__module__].__file__)+"\n"
			])


#"execute(('ls', '-l'), {}) in /foo"

