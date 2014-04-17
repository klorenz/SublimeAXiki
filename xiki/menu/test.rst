Here is some little test

- first
- second
  - third
  - third.1
- fourth

Here you see an alias definition

- label:: $ ls

There will be displayed only 

+ label

And on expansion, the command will be executed

<< test/second

<< $ echo <<
	This is input
	for the echo
	command.

	this also

But this is not.

keys/
  - | keys    : ctrl+enter
    | command : xiki
    | context :
    - | 