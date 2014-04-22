from sublime_unittest import *
import time, sys

class aXikiTest(BufferTest):
	def setUp(self):
		BufferTest.setUp(self)
		self.view.settings().set('xiki', True)
		self.started = time.time()

	def cmd_ended(self):
		#self.sublime_command
#		if time.time() - self.started > 10:
#			import spdb ; spdb.start()
		aXiki = sys.modules['aXiki.aXiki']
		return not aXiki.xiki.is_processing(self.view)

		#return not self.view.settings().get('xiki_running')

	test_01_hello = (
			'$ echo "hello world"│\n\n',

			v('xiki_continue', {}, 'cmd_ended'),

			'$ echo "hello world"\n'
			'  hello world\n'
			'$ │\n\n'
		)

	test_02_eof = (
			'$ echo "hello world"│',

			v('xiki_continue', {}, 'cmd_ended'),

			'$ echo "hello world"\n'
			'  hello world\n'
			'$ │\n'
		)

	test_03_many_continues = (
			'$ echo "hello world"│\n'
			'\n'
			'more text',

			v('xiki_continue', {}, 30),
			v('xiki_continue', {}, 'cmd_ended'),

			'$ echo "hello world"\n'
			'  hello world\n'
			'$ \n'
			'│\n'
			'\n'
			'more text'
		)

	test_04_many_continues = (
			'a line│\n'
			'\n'
			'more text',

			v('xiki_continue', {}, 30),
			v('xiki_continue', {}, 'cmd_ended'),

			'a line\n'
			'\n'
			'│\n'
			'\n'
			'more text'
		)

	test_05_input_1 = (
			'~/\n'
			'	>>> prin│t(_ + "hello world")\n'
			'	  hello world\n'
			'\n'
			'another line\n',

			v('xiki_input', {}, 'cmd_ended'),

			'~/\n'
			'	>>> prin│t(_ + "hello world")\n'
			'	  hello world\n'
			'	  hello world\n'
			'\n'
			'another line\n',
		)

	test_05_input_2 = (
			'~/\n'
			'	>>> print(_ + "x") <<\n'
			'	  hello │world\n'
			'\n'
			'another line\n',

			v('xiki_input', {}, 'cmd_ended'),

			'~/\n'
			'	>>> print(_ + "x") <<\n'
			'	  hello world\n'
			'	  x\n'
			'│\n'
			'another line\n',
		)

	test_06_form_buttons = (
			unindent("""
			inspect
				- input
				  test
				  │[foo] [bar]
			"""),

			v('xiki', {}, 'cmd_ended'),

			"inspect\n"
			"	- input\n"
			"	  | action: foo\n"
			"	  | ------------------\n"
			"	  | test\n"
			"│"
		)

	test_07_form_buttons = (
			"inspect/input\n"
			"	  test\n"
			"	  [foo] ┤[bar]├\n"
			,
			
			v('xiki_continue', {}, 'cmd_ended'),

			"inspect/input\n"
			"  | action: bar\n"
			"  | ------------------\n"
			"  | test\n"
			"│"
		)

	test_08_collapse_bug = (
			"- foo\n"
			"  - b│ar\n"
			"    \n"
			"  + glork\n",

			v('xiki', {}, 'cmd_ended'),

			"\n",
			"- foo\n"
			"  + bar\n"
			"  + glork\n"
		)
