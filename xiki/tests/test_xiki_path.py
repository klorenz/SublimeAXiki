# vim:fileencoding=utf-8:

if __name__ == '__main__':
	import sys
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test


from unittest import TestCase

from ..path import XikiPath
from ..util import unindent

class TestXikiPath(TestCase):
	pass



def gen_test_xiki_path(p, e):
	return lambda s: s.assertEquals( [x for x in XikiPath(p)], e)

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
	]:

	setattr(TestXikiPath, 'test_xiki_path_%s' % n, gen_test_xiki_path(p, e))

