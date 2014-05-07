
def menu(name=None, context=None, input=None):
    if name is None:
        name = xiki.dialog_input("name of bookmarklet")

    if input is None:
        return Snippet("""
            - ${1:name}
              // add code of bookmarklet below
              ${2:alert("hello world");}
              ${3:[submit]}
            """)

    result = unindent("""
    <title>Bookmarklet</title>
    <p>Click the link and try it out.  Then drag the link to your toolbar to 
    create a bookmarklet:</p>

    <a href="javascript:
    (function(){
    {}
    })()
    ">{}</a>
    """).format(input, name)

    path = xiki.tempfile("bookmarklet.html", content=result)
    import webbrowser
    webbrowser.open("file://"+path)
    
    return ""

