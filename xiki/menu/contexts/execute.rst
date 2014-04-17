Execute
=======

This context executes a command.  Indicator for execution command is ``$`` prompt.

::

    $ echo "hello world"

Execute context executes a command always within its current context.  I.e. it uses execute method from parent context, to execute the command.  Execute context is smart about its input.  If you have anything in command, which indicates, that this command should be rather executed in a shell, then it is executed in shell.

::

	$ echo "executed from shell" | echo


Finally here follows the code::

	class XikiExec(XikiContext):
		PATTERN = re.compile(r'^\s*\$\s+(.*)')
		PS1     = "$ "

		COMMAND_RE = re.compile(r'''(?x)
			(?:^|(?<=\s))
			(?:

			"((?:\\.|[^"\\]+)*)"
			| '((?:\\.|[^"\\]+)*)'
			| (\S+)

			)
			''')

		def parse_command(self, s):
			result = []
			is_shell_command = False
			for m in self.COMMAND_RE.finditer(s):
				dq, sq, nq = m.groups()
				if dq:
					result.append(dq.replace('\\"', '"').replace('\\\\', '\\'))
				elif sq:
					result.append(sq.replace("\\'", "'").replace('\\\\', '\\'))
				else:
					if ("`" in nq or nq in ("|", ">", "<") or nq.startswith('1>')
						or nq.startswith('2>')):
							return None
					result.append(nq)

			return result

		def open(self, input=None, cont=None):
			#import rpdb2 ; rpdb2.start_embedded_debugger('foo')
			s = self.mob.group(1)
			log.debug("%s: %s, %s", self, s, self.node_path)
			if not s.strip():
				return ""

			cmd = self.parse_command(s)
			if not cmd:
				return self.context.execute_shell(s, input=input)
			else:
				return self.context.execute(*cmd, input=input)
	
	
	

