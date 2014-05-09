import re
COMMENT = re.compile(r'(?s)//[^\n]*|/\*.*?\*/')

def menu(name=None, context=None, input=None):
    if name is None:
        #name = xiki.dialog_input("name of bookmarklet")
        name = 'name'

    if input is None:
        return Snippet("""
            - ${1:%s}
              // add code of bookmarklet below
              ${2:alert("hello world");}
              ${3:[submit]}
            """ % name)

    from xiki.util import unindent

    input = str(input)

    input = COMMENT.sub('', input)
    input = input.replace("\n", "").replace('&', '&amp;').replace('"', '&quot;')

    result = unindent("""
    <title>Bookmarklet</title>
    <p>Click the link and try it out.  Then drag the link to your toolbar to 
    create a bookmarklet:</p>

    <a href="javascript:(function(){%s})()">%s</a>
    """) % (input, name)

    path = xiki.tempfile("bookmarklet.html", content=result)
    import webbrowser
    webbrowser.open("file://"+path)
    
    return ""

