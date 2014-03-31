WHITESPACE = r'\s+'

HANGING = r'(?m)\S.*\n([\x20\t]+\S.*\n|[\x20\t]*\n)*'

KEY = r':?([^:]+):((?=\n)|[\x20\t]+)'

def is_list(s):
	from .path import BULLET_RE
	return BULLET_RE.match(s)


def syntax_error(message, lineno=None, filename=None):
	e = SyntaxError(message)
	e.lineno = lineno
	e.filename = filename
	return e

def whitespace(s, lineno):
	m = WHITESPACE.match(s)
	if m:
		lineno = m.group(0).count("\n")+1
		s = s[m.end():]
	return s, lineno


def parse(input, data=None, lineno=1, filename=None):
	'''Get a data tree out of s.

	Examples::

		foo: bar
		key: value
			and more data
		list:
			- first
			- "second"
			- third: true
			  forth: 1

	| foo: bar
	| key: value
	| 	and more data

	:foo: bar
	:key: value
		and more data
	'''

	s = input

	# remove "| " if present
	if s.startswith('| '):
		s = ''.join([ l[2:] for l in s.splitlines(1) ])

	# JSON is fine
	try:
		return json.load(s)
	except:
		pass

	# skip whitespace
	s, lineno = whitespace(s, lineno)

	# parse list
	if is_list(s):
#		unindent(s[2:], hang=True)
		result = []

		while s:
			s, lineno = whitespace(s, lineno)

			if not s:
				return result

			m = HANGING.match(s)
			if not m:
				raise syntax_error("unexpected end of file: %s" % s, lineno=lineno)

			current, s = s[:m.end()], s[m.end():]

			current = current[1:]
			if current[0] in "\x20\t":
				current = current[1:]

			if current[0] == "\n":
				lineno += 1

			result.append(parse(unindent(current, hang=True), lineno=lineno))
			line_no += current.count("\n")

	# parse dictionary
	if is_dictionary(s):
		result = {}

		while s:
			s, lineno = whitespace(s, lineno)

			if not s:
				return result

			m = HANGING.match(s)
			if not m:
				raise syntax_error("unexpected end of file: %s" % s.split("\n", 1)[0], lineno=lineno)

			current, s = s[:m.end()], s[m.end():]

			m = KEY.match(current)
			if not m:
				raise syntax_error("key expected: %s" % s.split("\n", 1)[0], lineno=lineno)

			key = m.group(1).strip()
			if current[m.end()] == "\n":
				lineno += 1
			value = parse(unindent(current[m.end():], hang=True), lineno=lineno)

			result[key] = value

	# else we keep this string
	return s
