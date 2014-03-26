if __name__ == '__main__':
	import sys
	from os.path import abspath, join, dirname
	sys.path.insert(0, abspath(join(dirname(__file__), '..')))
	import test


from unittest import TestCase

from ..path import XikiPath

class TestXikiPath(TestCase):
	def test_xiki_path(self):
		for p,e in [
			("foo/bar"     , [[('foo', 0), ('bar', 0)]]),
			("~/foo/bar"   , [[("~", 0), ("foo", 0), ("bar", 0)]]),
			("~/foo/@bar"  , [[("~", 0), ("foo", 0)], [("bar", 0)]]),
			([("foo", 0), ("bar", 0)], ["foo", "bar"]),
			("foo\n  + bar\n  + glork\n", [[('foo', 0), ('glork', 0)]]),
		]:
			self.assertEquals( [x for x in XikiPath(p)], e)
