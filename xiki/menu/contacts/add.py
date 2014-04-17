
def menu(ctx, input):
	if input:
		d = ctx.parse(input)

		if ctx.context.isroot():
			return ctx.store(d['email'], input=input, storage=d.get('storage'))
		else:
			return ctx.write_file(d['email']+'.xiki', input)
	else:
		return ctx.snippet('''
		first name: $1
		last name : $2
		email     : $3
		mobile    : $4
		storage   : ${5:user}
		${0:[SUBMIT]}
		''')

from xiki.util import unindent

def _test(testcase):
	output = testcase.xiki.open("contacts/add")
	o = ''.join([x for x in output])

	testcase.assertEquals(o, unindent('''
		first name: $1
		last name : $2
		email     : $3
		mobile    : $4
		storage   : ${5:user}
		${0:[SUBMIT]}
		''')
		)

def _test_store(testcase):
	output = testcase.xiki.open("contacts/add", input=unindent('''
		first name: Mickey
		last name : Mouse
		email     : mm@disney.com
	'''))

	testcase.assertEquals(output, [])
