URL
===

Opens URLs.

Handles urls in any strings.  Like::

    .. _search for url: http://google.com/?q=url

    some text and http://google.com/?q=query 

::

	class URL(XikiContext):
		PATTERN = re.compile(r'(?=\w).*\b((?:https?|ftp)://[^\s]*)')

		def open(self, input=None, cont=None):
			url = self.mob.group(1)
			import webbrowser
			webbrowser.open(url)
