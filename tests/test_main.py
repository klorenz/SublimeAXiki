from sublime_unittest import *
import time

class aXikiTest(BufferTest):
	def setUp(self):
		BufferTest.setUp(self)
		self.view.settings().set('xiki', True)
		self.started = time.time()

	def cmd_ended(self):
		#self.sublime_command
		if time.time() - self.started > 10:
			import spdb ; spdb.start()
		return not self.view.settings().get('xiki_running')

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
			'$ │\n'
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
