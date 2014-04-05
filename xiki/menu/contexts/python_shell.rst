Python Shell
============

This Xiki Module provides a python shell.  A python shell command is indicated 
by ``>>>`` prompt.

Try this: 

	>>> print("hello world")

::

	class XikiPython(XikiContext):
		PATTERN = re.compile(r'>>> (.*)')
		PS1     = ">>> "

		def open(self, input=None, cont=None):
			s = self.mob.group(1)
			_stderr = sys.stderr
			_stdout = sys.stdout

			try:
				from io import StringIO
			except ImportError:
				from cStringIO import StringIO

			_output = StringIO()

			r = None

			import pydoc
			sys.stderr = _output
			sys.stdout = _output
			_pager = pydoc.pager

			pydoc.pager = pydoc.plainpager

			is_exec = False
			try:
				code = compile(s, "<string>", mode='eval')
			except SyntaxError:
				code = compile(s+"\n", "<string>", mode='exec')
				is_exec = True

			try:
				main = sys.modules['__main__']

				if not hasattr(main, 'help'):
					setattr(main, 'help', pydoc.help)

				if is_exec:
					self.exec_code(code, sys.modules['__main__'].__dict__)
				else:
					r = eval(s, sys.modules['__main__'].__dict__)
			except:
				import traceback
				traceback.print_exc()
			finally:
				sys.stderr = _stderr
				sys.stdout = _stdout
				pydoc.pager = _pager

			_output.seek(0)

			import pprint
			if r is not None:
				return [ pprint.pformat(r) ]
			else:
				return _output.readlines()

