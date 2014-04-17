# vim:fileencoding=utf-8:

if __name__ == '__main__':
	import sys
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test


from unittest import TestCase

from ..path import XikiPath, XikiInput
from ..util import unindent

class TestXikiPath(TestCase):
	pass

def gen_test_xiki_path(p, e):
	def _test(self):
		xiki_path = XikiPath(p)
		if isinstance(e, dict):
			self.assertEquals( [x for x in xiki_path], e['path'])
			self.assertEquals( xiki_path.input, e['input'])
		else:
			self.assertEquals( [x for x in xiki_path], e)

	return _test

for n,p,e in [
	(1, "foo1/bar"     , [[('foo1/', 0), ('bar', 0)]]),
	(2, "~/foo2/bar"   , [[("~/", 0), ("foo2/", 0), ("bar", 0)]]),
	(3, "~/foo3/@bar"  , [[("~/", 0), ("foo3/", 0)], [("bar", 0)]]),
	(4, [("foo", 0), ("bar", 0)], ["foo", "bar"]),
	(5, unindent('''
	 - @foo4  
	   + bar  
	   + glork
	 '''), 
	 [[('foo4', 0), ('glork', 0)]]
	),
	(6, unindent('''
	 - foo5  
	   + bar  
	   + ``glork``
	 '''), 
	 [[('foo5', 0)], [('glork', 0)]]
	),
	(7, unindent('''
	 - foo6 -- This is a Comment
	   + bar  
	   + `glork` — This is a Comment
	 '''), 
	 [[('foo6', 0)], [('glork', 0)]]
	),
	(8, unindent('''
	 - foo7 -> bar
	   + bar  
	   + glork
	 '''), 
	 [[('foo7/', 0), ('bar', 0), ('glork', 0)]]
	),

	(9, unindent('''
		root@havanna.moduleworks.com
		  + ~/
		    + hardcopy.3
		    + kiwi/
		      + csv-2014-01/
	'''),
	[[('root@havanna.moduleworks.com', 0), ('~/', 0), ('kiwi/', 0), ('csv-2014-01/', 0)]]
	),
	(10, unindent('''
		root@havanna.moduleworks.com:/
		  + ~/
		    + hardcopy.3
		
		    + kiwi/
		      + csv-2014-01/
	'''),
	[[('root@havanna.moduleworks.com:/', 0), ('~/', 0), ('kiwi/', 0), ('csv-2014-01/', 0)]]
	),
	(11, unindent('''
		root@havanna.moduleworks.com:~
		  + ~/
		    + hardcopy.3
		    + kiwi/
		      + csv-2014-01/
	'''),
	[[('root@havanna.moduleworks.com:~', 0), ('~/', 0), ('kiwi/', 0), ('csv-2014-01/', 0)]]
	),
	(12, unindent('''
		root@havanna.moduleworks.com:~$ echo "hello world"
	'''),
	[[('root@havanna.moduleworks.com:~$ echo "hello world"', 0)]]
	),
	(13, unindent('''
		$ pip --help
	'''),
	[[('$ pip --help', 0)]]
	),
	(14, unindent('''
		- Contact
		  - Add
		    ===

		    Name : Mickey Mouse
		    Email: mickey@mouse.com

		    [SUBMIT]
	'''),
	{'path': [[('Contact', 0), ('Add', 0)]],
	 'input': XikiInput(action = 'SUBMIT', input  = "===\n\nName : Mickey Mouse\nEmail: mickey@mouse.com\n\n")
	}
	),

	]:

	setattr(TestXikiPath, 'test_xiki_path_%s' % n, gen_test_xiki_path(p, e))

