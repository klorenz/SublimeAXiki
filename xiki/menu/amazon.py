def menu(context):
	query = xiki.dialog_input("search amazon")

	if query:
		url = "http://www.amazon.com/s?field-keywords={}".format(query)

		import webbrowser
		webbrowser.open(url)

	return ""

