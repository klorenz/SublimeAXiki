TODO
====

Be able to add sublime snippets easily::

	- sublime
	  - snippets
	    - name | trigger | scope.name
	      | Here is the snippet
	      |
	      |
	  - completions
	    - name | scope.name
	      - trigger: text
	      - trigger: text
	      - text which is also trigger
	      - this\: trigger: text

Need a IMAP client (first for editing ACLs)::

	- mailbox
	  @ settings
	    - protocol: IMAP
	    - ssl: true
	    - port: 993
	    - username: user
	    - password: pw
	  - INBOX
	  - foo/bar
	  - /foo/
		| here all folders are listed matching foo

Maybe add opportunity to enter password interactively.