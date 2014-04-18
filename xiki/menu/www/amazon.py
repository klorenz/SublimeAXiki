def menu(context):
	query = xiki.dialog_input("search amazon")
	if query:
		import webbrowser
		url = "http://www.amazon.com/s?field-keywords={query}".format(locals())
		webbrowser.open(url)

