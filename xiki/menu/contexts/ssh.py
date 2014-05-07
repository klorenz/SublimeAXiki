"""
SSH
===

SSH context allows you to specify ssh connection details and wraps all other contexts to be run via ssh.

::

	- user@some.domain:1234
		$ ls
		+ /foo/bar

Please note that all commands are run in BatchMode, so you first have to make sure, that you can do passwordless authentication.


Run following commands in a terminal::

	$ ssh-keygen
	$ ssh-copy-id user@some.domain:1234
"""

from xiki.util import cmd_string

class ssh(XikiContext):
	PATTERN = re.compile(r'''(?x) ^
		(?P<cmd>
			(?P<user>[\w\-]+) @ (?P<host>[\w\-]+(\.[\w\-]+)*) 
			(?::(?P<port>\d+))?)
		(?::(?P<extra>.*))?$''')

	SETTINGS = {
		"remote_shell": "bash"
	}

	shell = 'bash'

	def does(self, xiki_path):
		r = XikiContext.does(self, xiki_path)
		if not r: return r

		log.debug("mob: %s", self.mob.groupdict())

		extra = self.mob.group('extra')
		log.debug("extra: %s", extra)
		if extra:
			# handle path$ some command
			pass

		if not self.xiki_path:
			self.xiki_path.insert(0, "~/")

		elif not self.xiki_path.isfilepath():
			log.debug("test xiki_path %s", self.xiki_path)

			# determine if this is still a filepath
			try:
				self.subcontext = self.xiki_path.context(context=self)

			except LookupError:
				log.warning("could not lookup context for %s" % self.xiki_path)
				self.xiki_path.insert(0, "~/")

		if not self.subcontext:
			self.subcontext = self.xiki_path.context(self)

		return True



	def get_ssh_cmd(self):
		cmd = [ 'ssh', '-o', "BatchMode yes" ]
		ssh_data = self.ssh_data

		if ssh_data['port']:
			cmd += [ '-p', ssh_data['port'] ]
		cmd += [ '%(user)s@%(host)s' % ssh_data ]
		return cmd

	def listdir(self, path=None):
		'''usually path is not optional, but we allow it not to be set to 
		list the default ssh landing directory from menu'''

		if path is None:
			output = self.execute('ls', '-F')
		else:
			output = self.execute('ls', '-F', path)

		for line in output:
			line = line.strip()
			if not line: continue
			log.debug("line: %s", line)
			if line[-1] in "*=>@|":
				line = line[:-1]
			yield line

	def read_file(self, path, count=None):
		if count is not None:
			return self.execute('head', '-n', str(count), path)
		else:
			return self.execute('cat', path)

	def open_file(self, path, opener=None, bin_opener=None, text_opener=None):
		raise NotImplementedError("Open file via SSH not yet implemented")
		cache_name = '%(user)s@%(host)s' % ssh_data
		return self.context.open_file( self.cached_file(cache_name, path) )

	def exists(self, path):
		output = ''.join([x for x in 
			self.execute('[ -e %s ] && echo y || echo n' % cmd_string(path))])
		return output.strip() == 'y'

	def get_project_dirs(self):
		return []

	def get_system_dirs(self):
		return []

	SHELL_VAR = re.compile(r"\$\{|\$\w")

	def shell_expand(self, name):
		name = str(name)

		if "$" not in name and "~" not in name:
			return name

		home_dir = self.get_static('~')
		if not home_dir:
			#import spdb ; spdb.start()
			home_dir = ''.join([x for x in self.execute('echo', '~')]).strip()
			self.set_static('~', home_dir)

		if name.startswith('~'):
			name = home_dir + name[1:]

		if not self.SHELL_VAR.search(name):
			return name

		return ''.join([x for x in self.execute('echo', name)]).strip()

	def isdir(self, path):
		output = ''.join([x for x in 
			self.execute('[ -d %s ] && echo y || echo n' % cmd_string(path))])
		return output.strip() == 'y'

	def walk(self, root):
		for line in self.execute('find', root, '-type', 'f'):
			yield line

	def makedirs(self, *path):
		p = cmd_string('/'.join(list(path)))
		self.execute('[ ! -e %s ] && mkdir -p %s' % (p, p))

	def execute(self, *args, **kargs):
		working_dir = kargs.get('cwd')
		cmd = self.get_ssh_cmd()

		log.debug("exec args: %s", args)
		log.debug("self.context: %s", self.context)
	#		if not working_dir:
	#			if self.xiki_path:

		#import spdb ; spdb.start()
		if working_dir:
			args = cmd_string(args)
			cwd  = cmd_string(working_dir)
			rcmd = 'cd %s && %s' % (cwd, args)
			rcmd = cmd_string(rcmd)
			my_cmd = cmd + ['sh', '-c', rcmd ]
			log.debug("my_cmd: %s", my_cmd)
			return self.context.execute(*my_cmd)
		else:
			my_cmd = cmd + list(args)
			log.debug("my_cmd: %s", my_cmd)
			return self.context.execute(*my_cmd)

	def menu(self):
		return [ '+ ~/\n', '+ /\n' ]

	# def menu(self):
	# 	if self.node_path.isdir():
	# 		for line in self.execute('ls', '-F'):
	# 			line = line.strip()
	# 			if not line: continue
	# 			log.debug("line: %s", line)
	# 			if line[-1] in "*=>@|":
	# 				line = line[:-1]

	# 			yield '+ %s\n' % line

	def execute_shell(self, command, **kargs):

		working_dir = kargs.get('cwd')

		# need quoting around entire string
		args = [self.shell, "-c", command ]
		#cmd_string(cmd_string(args), quote="'")]

		log.debug("args: %s", args)

		if working_dir:
			args = cmd_string(args)
			cwd  = cmd_string(working_dir)
			rcmd = 'cd %s && %s' % (cwd, args)
			rcmd =  cmd_string(rcmd)
			return self.execute('sh', '-c', rcmd)
		else:
			return self.execute(*args)