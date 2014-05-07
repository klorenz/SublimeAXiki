def menu(context):
	query = xiki.dialog_input("search amazon")

	if query:
		url = "http://www.amazon.com/s?field-keywords={}".format(query)

		print("url: %s" % url)

		import webbrowser
		webbrowser.open(url)

	return ""

