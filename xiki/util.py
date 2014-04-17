if __name__ == '__main__':
	import test

import logging, re, subprocess
log = logging.getLogger('xiki.util')

INDENT_RE = re.compile(r'^[\x20\t]*')

def get_indent(line):
	'''returns indentation of a line.'''

	if isinstance(line, str):
		return INDENT_RE.match(line).group(0)

	raise NotImplementedError("for type ")


def get_args(line, mob):
	kwargs = {}

	if mob is True:
		args = (line,)
	else:
		kargs = mob.groupdict()
		args  = mob.groups()
		if not kargs and not args:
			args = (line,)

	return args, kwargs


TEXT_CHARACTERS = re.compile(r'[\x20-\x7f\n\r\t\b]')

# taken from http://stackoverflow.com/questions/1446549/how-to-identify-binary-and-text-files-using-python
def is_text_file(filename, bytes=None):
	import string

	if bytes is None:
		f = open(filename, 'rb')
		s = f.read(512)
		f.close()
	else:
		s = bytes

	if not s:
		# Empty files are considered text
		return True

	if isinstance(s, str):
		s = s.encode('utf-8')

	if b"\0" in s:
		# Files with null bytes are likely binary
		return False

	chars = 0
	bytes = 0
	for x in s:
		if x in (10, 13, 8, 9):
			chars += 1
		elif x < 32 or x > 127:
			bytes += 1
		else:
			chars += 1

	# If more than 30% non-text characters, then
	# this is considered a binary file
	if float(bytes)/float(len(s)) > 0.30:
		return False

	return True

def os_open(path, opener):
	p = subprocess.Popen([opener, path])
	p.wait()

def unindent(s, hang=False):
	if not isinstance(s, str):
		return s

	if hang:
		first_line, s = s.split("\n", 1)
		first_line += "\n"
		if first_line == "\n":
			first_line = ""
	else:
		first_line = ""
		if s.startswith("\n"):
			s = s[1:]

	indent = INDENT_RE.match(s).group(0)
	indent_len = len(indent)

	r = []
	for line in s.splitlines(1):
		if line.startswith(indent):
			r.append(line[indent_len:])
		else:
			r.append(line)

	return first_line+''.join(r)

NON_ESCAPE_CHARS = re.compile(r'^[\w\-/\.=~]+$')
def cmd_string(args, quote='"'):
	if isinstance(args, str):
		args = [args]
	r = []
	for a in args:
		if a == '|':
			r.append(a)
		elif a.startswith('1>'):
			r.append(a)
		elif a.startswith('2>'):
			r.append(a)
		elif a == '>':
			r.append(a)
		elif a == '<':
			r.append(a)
		elif a.startswith('-'):
			r.append(a)
		elif not NON_ESCAPE_CHARS.match(a):
			q = quote
			r.append(q+a.replace('\\', '\\\\').replace(q, '\\'+q)+q)
		else:
			r.append(a)

	return ' '.join(r)

def indent(s, indent="", hang=False):
	if isinstance(indent, int):
		indent = indent*" "

	if not isinstance(s, str):
		if not isinstance(s, list):
			s = [y for y in s]
		s = ''.join(s)

	s = indent.join(s.splitlines(1))

	if hang:
		return s
	else:
		return indent+s

indent_lines = indent

def find_lines(context, text, node_path):
	from .core import XikiPath, INDENT

	log.debug("node_path: %s", node_path)
	lines  = text.splitlines(1)
	path   = node_path
	result = []
	collecting = False
	need_indent = False

	indentation = ['']

	if not node_path:
		collecting = True

	was_empty = False

	#import spdb ; spdb.start()
	insert_xiki_path = None
	insert_input = None

	path_i = 0
	i = -1
	while i < len(lines):
		i += 1
		if i >= len(lines):
			break
		line = lines[i]

		log.debug("line: %s" % line.rstrip())

		if insert_input is not None:
			if not line.strip():
				insert_input.append("\n")
				continue

			else:
				ind = get_indent(line)

				if ind.startswith(indentation[-1]):
					insert_input.append(line[len(indentation[-1]):])
					continue
				else:
					indentation.pop()

					insert = XikiPath(insert_xiki_path).open(context, input=insert_input)
					if collecting:
						result.append(indent_lines(insert, ind))
					else:
						lines[i+1:i+2] = indent_lines(insert, indentation[-1]).splitlines(1)

					insert_input     = None
					insert_xiki_path = None

		if collecting:
			# line not empty
			if line.strip():
				ind = get_indent(line)

				# not indented anymore
				if not ind.startswith(indentation[-1]):
					break

				if len(ind) == len(indentation[-1]):
					line = line[len(ind):]

					if line.startswith('<<'):  # insert
						line = line.rstrip()
						if line.endswith('<<'):
							line = line[:-2].rstrip()
							insert_xiki_path = line
							need_indent = True
							continue
						else:
							insert = XikiPath(line[2:].strip()).open(context)
							result.append(indent_lines(insert, ind))
					else:
						if line.startswith('- '):
							line = '+'+line[1:]
							if '::' in line:
								line = line.split('::', 1)[0]

						result.append(line)

					last_same_line = line

				if len(ind) > len(indentation[-1]):
					if last_same_line.startswith('+'):
						continue
					else:
						result.append(line)

				continue

			# line empty
			else:
				result.append('\n')
				continue

		else:
			# skip empty lines
			if not line.strip():
				was_empty = True
				continue
			else:
				was_empty = False

		log.debug("path: %s, %s" % (i, path))

		if not line.startswith(indentation[-1]):
			indentation.pop()
			need_indent = False
			path_i -= 1
			break

		indent = get_indent(line)
		line = line.strip()

		if need_indent:
			# there is an indented line here
			if len(indent) > len(indentation[-1]):
				indentation.append(indent)

				if insert_xiki_path:
					insert_input = []
					if was_empty:
						insert_input.append("\n")
					insert_input.append(line+"\n")
					need_indent = False
					last_same_line = line
					continue

				if path_i >= len(path):
					collecting = True
					if line[0] == '-':
						line = '+'+line[1:]

					if was_empty:
						result.append("\n")

					result.append(line+"\n")
					last_same_line = line
					need_indent = False
					continue

			need_indent = False

			# there is no indented line here
			if path_i >= len(path):
				# if we allowed multiple items in a list, we had to backtrack
				# here maybe, but for now we are done, because there is no 
				# input
				return ""

		if line.startswith('<<'):
			if line.endswith('<<'):
				line = line[:-2].rstrip()
				insert_xiki_path = line
				need_indent = True
			else:
				insert = XikiPath(line[2:].strip()).open(context)
				lines[i+1:i+2] = indent_lines(insert, indent).splitlines(1)
			continue

		if line.startswith('+'):
			raise NotImplementedError("not yet implemented")
			insert = XikiPath(line[2:].strip()).expanded(context)
			lines[i:i+1] = [ indent + '-' + line[1:]+"\n"]
			lines[i+1:i+2] = [ indent+INDENT+l for l in insert.splitlines(1) ]

		if line[0] in '-@':
			if len(indent) > len(indentation[-1]):
				continue

			command = None
			_line = line[1:].strip()
			if '::' in  _line:
				_line, command = [x.strip() for x in _line.split('::', 1)]

			if ':' in _line:
				_line = _line.split(':', 1)[0]

			if _line != path[path_i]:
				continue

			if _line == path[path_i]:
				if command:
					insert = XikiPath(command).expanded(context)
					_indent = indent + INDENT
					lines[i+1:i+2] = indent_lines(insert, _indent).splitlines(1)
				else:
					path_i += 1
					need_indent = True

	log.debug("result: %s", result)

	return ''.join(result).rstrip()+"\n"


SLUGIPY_RE = re.compile(r'[^\w]+')
def slugipy(x):
	"""pythonic slugify, such that there are only \w chars in name, starting
	with a alphabetic char, a sequence of non-\w chars is replaced by "_",
	so "foo bar" and "foo-bar" will both be translated to "foo_bar"
	"""

	return SLUGIPY_RE.sub("_", x)

def slugify(x):
	return SLUGIPY_RE.sub("-", x)