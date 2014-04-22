
This gives a view into aXiki Internals.

- contexts — list active contexts
- input — inspect input

::

	def contexts():
		from xiki.core import XikiContext
		for ctx in XikiContext:
			yield "- %s\n" % str(ctx)

	def _make_context_doc(ctx):
		"""this does not work :( """
		def _context_doc():
			if hasattr(ctx, '__doc__'):
				return ctx.__doc__ or ""
			return ""
		setattr(contexts, str(ctx), _context_doc)

	for ctx in XikiContext:
		_make_context_doc(ctx)

	def input(input=None):
		result = ''
		if hasattr(input, 'action'):
			result += (""
				+ "| action: %s\n" % input.action 
				+ "| ------------------\n"
				)

		if input is not None:
			result += ''.join([ 
				"| "+line for line in input.splitlines(1)
				])

		return result


