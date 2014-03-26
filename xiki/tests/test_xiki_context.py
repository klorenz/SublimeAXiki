if __name__ == '__main__':
	import sys
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test

from unittest import TestCase

from ..path import XikiPath
from ..core import XikiContext, ConsoleXiki

class CtxStub(XikiContext):
	def root_menuitems(self):
		return None
	def execute(self, *args, **kargs):
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		return ["execute(%s, %s) in %s" % (repr(args), repr(kargs), self.working_dir)]

class MyXiki(ConsoleXiki):
	def getcwd(self):
		return "/foo"
	def makedirs(self, name):
		return None


class TestXikiContext(TestCase):

	def _test_xiki_path(self, path, expected):
		x = XikiPath(path, rootctx=CtxStub).open(MyXiki())
		if isinstance(x, str): x = [x]
		self.assertEquals([y for y in x], expected)

	def test_ssh(self):
		self._test_xiki_path("user@host.com:1234", [
			"+ execute(('ssh', '-p', '1234', 'user@host.com', 'ls', '-F'), "
			"{}) in /foo" 
			])

	def test_execute(self):
		self._test_xiki_path("/foo/bar/$ ls -l",[
		 	"execute(('ls', '-l'), {}) in /foo/bar"
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

