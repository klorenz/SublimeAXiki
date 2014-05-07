# vim:fileencoding=utf-8:

if __name__ == '__main__':
	import sys
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test


from unittest import TestCase

from ..parser import parse
from ..util import unindent

class TestDataParser(TestCase):
	pass

def gen_test_data_parser(s, e):
	def _test(self):
		d = parse(s)
		self.assertEquals(d, e)

	return _test

for n,p,e in [
	(1, unindent("""
		foo: bar
		key: value
		    and more data
		list:
		    - first
		    - "second"
		    - third: true
		      forth: 1
		"""),
		{
			'foo': 'bar',
			'key': 'value\nand more data\n',
			'list': [
				'first', 
				u'second', 
				{'forth': 1, 'third': True}
			]
		}
		),
# 	(14, unindent('''
# 		- Contact
# 		  - Add
# 		    ===

# 		    Name : Mickey Mouse
# 		    Email: mickey@mouse.com

# 		    [SUBMIT]
# 	'''),
# 	{'path': [[('Contact', 0), ('Add', 0)]],
# 	 'input': XikiInput(action = 'SUBMIT', value = "===\n\nName : Mickey Mouse\nEmail: mickey@mouse.com\n\n")
# 	}
# 	),

	]:

	setattr(TestDataParser, 'test_data_parser_%s' % n, gen_test_data_parser(p, e))

