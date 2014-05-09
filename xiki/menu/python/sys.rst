
This gives you some information about python running this xiki.

- modules — list of loaded modules
- version — python version

::

    def modules(name=None, action=None):
        import sys
        if action == "doc":
            return "<< >>> help(%s)\n" % repr(name)
        elif action == "symbols":
            return sorted(dir(sys.modules[name]))
    
        if name:
            return ['doc', 'symbols']
            # return "<< >>> help(%s)\n" % repr(name)
        return sorted(sys.modules.keys())
    
    def version():
        return sys.version

