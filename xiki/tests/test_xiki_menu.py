import sys

if __name__ == '__main__':
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test

from unittest import TestCase

from ..path import XikiPath
from ..core import XikiContext, MemXiki
from ..contexts import XikiMenuFiles

class MyXiki(MemXiki):

	def __init__(self,*args, **kargs):
		MemXiki.__init__(self,*args,**kargs)
		self.menu_files = XikiMenuFiles(self)
		#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
		self.menu_files.update()

	MY_STORAGE = {}
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

class TestXikiMenu(TestCase):
	xiki = MyXiki()

print(sys.modules.keys())

for mod_name in sys.modules:
	if mod_name.startswith('xiki.menu'):
		mod = sys.modules[mod_name]
		for name in dir(mod):
			method_name = 'test_'+mod_name.replace('.', '_')+'_'+name
			if name.startswith('_test'):
				setattr(TestXikiMenu, method_name, getattr(mod, name))

