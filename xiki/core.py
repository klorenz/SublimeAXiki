# vim: fileencoding=utf8

if __name__ == '__main__':
    import test

import logging, re, os, time, subprocess, platform, threading, sys, json
log = logging.getLogger('xiki.core')

from .util import *
from .path import XikiPath, BULLET_RE
from .interface import *

# from six.py
def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        for slots_var in orig_vars.get('__slots__', ()):
            orig_vars.pop(slots_var)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper

os_path_exists = os.path.exists
os_path_join   = os.path.join
os_walk        = os.walk

INDENT = "  "

class XikiSettings:
    def __init__(self, xiki):
        self.xiki = xiki
        self.settings = {}

    def __getitem__(self, name):
        return self.settings[name]

    def __setitem__(self, name, value):
        self.settings[name] = value

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def set(self, name, value):
        self[name] = value

    def append(self, name, value):
        if not name in self.settings:
            self.settings[name] = []
        self.settings[name].append(value)

class Snippet:
    def __init__(self, thing):
        if isinstance(thing, str):
            self.snippet = [ unindent(thing) ]

    def indented(self, indent=""):
        s = str(self)
        indent = indent.replace(INDENT, "\t")
        s = ''.join([ indent+"\t"+l for l in s.splitlines(1) ])
        print("s: %s" % repr(s))
        s = s.rstrip() + "\n"
        return s

    def __str__(self):
        return ''.join([x for x in self.snippet])

    def __iter__(self):
        yield str(self)


class XikiError(Exception):
    pass


class XikiFileAlreadyExists(XikiError):
    pass


class XikiLookupError(XikiError):
    pass


PY3 = sys.version_info[0] >= 3


def exec_code(code, globals=None, locals=None):
    if PY3:
        import builtins
        getattr(builtins, 'exec')(code, globals, locals)
        exec(code, globals, locals)
    else:
        #frame = sys._getframe()
        exec(code, globals, locals)
        #eval("exec code in globals, locals", frame.f_globals, frame.f_locals)

class XikiExtensions:

    def __init__(self, xiki):
        self.nodes = {}
        self.dirs  = set()
        self.path = set()
        self.xiki = xiki
        self.titles = {}
        self.updating = False

    def __getitem__(self, name):
        #import spdb ; spdb.start()

        if name in self.nodes:
            return self.nodes[name]

        if name in self.titles:
            return self.titles[name]

        slashed_name = name + "/"
        result = set()
        log.debug("keys nodes: %s" % self.nodes.keys())
        for d in self.titles:
            if d.startswith(slashed_name):
                result.add("+ "+d.split('/', 2)[1]+"\n")
        return ''.join(result)

    def get_title(self, name, docstring):

        line = 1
        if "\n" in docstring:
            title, doc = docstring.split("\n", 1)
        else:
            title, doc = docstring, ""

        if title.startswith('<<'):
            if title.endswith('<<'):
                raise NotImplementedError("TODO: title with input")

            docstring = XikiPath(title[2:]).open(self.xiki)
            if not isinstance(docstring, str):
                docstring = ''.join([x for x in docstring])
                
            log.debug("docstring: %s", docstring)

            if "\n" in docstring:
                title, doc = docstring.split("\n", 1)
            else:
                title, doc = docstring, ""

            if title.endswith(':'):
                title = title[:-1]

        if doc:
            if doc[0].isalnum():
                title = name
                doc = docstring
                line = 0


        # elif doc[0] != "\n" and not doc[0].isalnum():
        #   doc = doc.split("\n", 1)[1]
        #   line = 2

        # i print= 0
        # while doc[i].isspace():
        #   if doc[i] == "\n":
        #       line += 1
        #   i += 1
        # if i:
        #   doc = doc[i:]

        return title, doc, line

    def add_file_python(self, path_name, m, name):
        title = name

        source = self.xiki.read_file(path_name)

        try:
            code = compile(source, filename=path_name, mode='exec')

            exec_code(code, m.__dict__)


            if not hasattr(m,'menu') and not hasattr(m, 'open'):

                if hasattr(m, 'Menu'):
                    m.menu = m.Menu()
                    if not callable(m.menu):
                        m.menu.__call__ = lambda: m.Menu.__doc__

                if m.__doc__:

                    title, doc, line_offset = self.get_title(name, m.__doc__)
                    m.menu = lambda: doc

                else:
                    def _sym_menu(mod):
                        def menu(ctx):
                            import types
                            result = []
                            for a in dir(mod):
                                if isinstance(a, type):
                                    if issubclass(a, XikiContext):
                                        result.append("+ %s\n" % a)
                                    elif callable(a):
                                        result.append("+ %s\n" % a)
                                elif callable(a):
                                    result.append("+ %s\n" % a)
                            return ''.join(result)
                        return menu
                    m.menu = _sym_menu(m)
            return title

        except:
            log.error("error loading %s", path_name, exc_info=1)


    def add_file_any(self, path_name, m, name):
        source = self.xiki.read_file(path_name)

        title, doc, line_offset = self.get_title(name, source)
        m.menu = lambda: doc

        menu   = []
        pycode = []
        is_python = False
        non_py_indent = None
        popped = []

        try:
            
            for i,line in enumerate(doc.splitlines(1)):
                if is_python:
                    if not line.strip():
                        pycode.append(line)
                    else:
                        indent = get_indent(line)

                        if len(indent) <= len(pycode_indent):

                            try:
                                sys.stderr.write("%s\n" % pycode)

                                code = compile("\n"*(line_offset+1)+unindent(''.join(pycode)), filename=path_name, mode='exec')
                                exec_code(code, m.__dict__)

                                is_python = False
                                menu.append(line)

                            except:
                                log.warning("assumed python code, but got compilation error", exc_info=1)
                                menu += popped
                                menu += pycode

                            finally:
                                pycode = []
                                is_python = False

                            continue

                        pycode.append(line)

                    continue

                if non_py_indent:
                    if not line.strip():
                        menu.append(line)
                        continue
                    ind = get_indent(line)
                    if len(ind) > non_py_indent:
                        menu.append(line)
                        continue

                    non_py_indent = None

                try:
                    stripped = line.strip()

                    if stripped.lower().startswith('example') and stripped.endswith('::'):
                        non_py_indent = get_indent(line)
                        continue

                    if stripped.startswith('class ') or stripped.startswith('def '):
                        pycode_indent = get_indent(line)
                        pycode.append(line)
                        is_python = True
                        line_offset = i

                        # pop indicating line in restructured text
                        if len(menu) > 2:
                            if menu[-2].endswith('::\n') and not menu[-1].strip():
                                popped = []
                                popped.append(menu.pop())
                                popped.append(menu.pop())
                                # and remove empty lines before
                                while not menu[-1].strip():
                                    popped.append(menu.pop())

                                popped.reverse()

                    else:
                        menu.append(line)

                except (OverflowError, SyntaxError, ValueError):
                    menu.append(line)
                    continue

            if is_python:
    #                   import spdb ; spdb.start()
                code = compile("\n"*(line_offset+1)+unindent(''.join(pycode)), filename=path_name, mode='exec')
                exec_code(code, m.__dict__)

            if menu:
                def _menu(menu):
                    return lambda: ''.join(menu)
                m.menu = _menu(menu)

            return title
        except:
            log.error("error loading %s", path_name, exc_info=1)


    def add_files_from_path(self, root):
        #if root in self.path:
        #   return
        if not self.xiki.exists(root):
            return

        root_len = len(root)+1
        import imp

        mod_base = 'xiki.%s' % self.xiki.name

        if mod_base not in sys.modules:
            sys.modules[mod_base] = imp.new_module(mod_base)

        mod_base = 'xiki.%s.ext' % self.xiki.name

        if mod_base not in sys.modules:
            sys.modules[mod_base] = imp.new_module(mod_base)

        for path_name in self.xiki.walk(root):
            node_name = path_name[root_len:]
            name, ext = os.path.splitext(os.path.basename(path_name))
            node_name = os.path.splitext(node_name)[0]
            dir_name  = os.path.dirname(node_name)

            log.debug("node_name: %s", node_name)
            if node_name in self.nodes:
                m = self.nodes[node_name]
                modification_time = self.xiki.getmtime(path_name)
                log.debug("file %s changed?", path_name)
                log.debug("modification_time %s, created %s", modification_time, m.time_created)
                if modification_time < m.time_created:
                    log.debug("file %s is unchanged" % path_name)
                    continue
                else:
                    log.debug("file %s changed" % path_name)

                    if hasattr(m, 'unload'):
                        m.unload()

            d = os.path.dirname(node_name)
            parts = d.split('/')
            for i,p in enumerate(parts, start=1):
                _dir = '/'.join(parts[:i])
                if not _dir: continue
                self.dirs.add(_dir)

            # create module

            mod_name = '%s.%s' % (mod_base, '.'.join(parts))

            m = imp.new_module(mod_name)
            m.__file__ = path_name
            m.xiki = self.xiki
            m.XikiContext = XikiContext
            m.XikiPath = XikiPath
            m.Snippet  = Snippet
            m.log = logging.getLogger(mod_name)
            m.os  = os
            m.sys = sys
            m.re  = re
            m.time_created = time.time()

#           import spdb ; spdb.start()

            if ext == '.py':
                title = self.add_file_python(path_name, m, name)

            else:
                title = self.add_file_any(path_name, m, name)

            if not title:
                continue

            sys.modules[mod_name] = m

            m.title = lambda: title
            if dir_name:
                self.titles["%s/%s" % (dir_name, title)] = m
            else:
                self.titles[title] = m

            self.nodes[node_name] = m

        #for k,v in self.nodes.items():
        #   log.debug("%s: %s" %(k,v.__file__))

        self.path.add(root)

    def __contains__(self, name):
        return name in self.nodes or name in self.dirs or name in self.titles

    def __iter__(self):
        log.debug("dirs: %s", self.dirs)
        log.debug("node_keys: %s", self.nodes.keys())
        for n in self.dirs.union(set(self.titles.keys())):
            yield n

    def update(self, extdir):
        if self.updating:
            return
        try:
            self.updating = True

            log.debug("updating from %s", extdir)
            #import rpdb2 ; rpdb2.start_embedded_debugger('foo')
            for menu_dir in self.xiki.get_search_path(extdir):
                log.debug("menu: updating from %s", menu_dir)
                self.add_files_from_path(menu_dir)
        finally:
            self.updating = False


class BaseXiki(
    StaticVariableInterface, 
    SettingsInterface, 
    FileSystemInterface,
    ExecuteProgramInterface,
    CompletionInterface,
    ):

    def __init__(self, name=None):
        if name is None:
            name = self.__class__.__name__
        self.name = name

        import tempfile
        self.plugins      = {}
        self.search_paths = {}
        self.cache_dir    = tempfile
        self.storage      = {}

        self.last_exit_code = {}

        if platform.system() == 'Windows':
            if "great" == self.execute_output("bash", "echo", "great").strip():
                self.shell = ['bash', '-c']
            else:
                self.shell = ['cmd', '/c']

            self.storage['home'] = os.path.expanduser('~/AppData/Roaming/axiki')
        else:
            self.shell = ['bash', '-c']
            self.storage['home'] = os.path.expanduser('~/.config/axiki')

        op = os.path
        xiki_dir = op.abspath(op.join(op.dirname(__file__), '..'))

        if os.path.exists(xiki_dir):
            self.register_plugin('xiki', xiki_dir)

        self.static_vars       = {}
        self.default_storage   = 'home'
        self.default_extension = '.xiki'
        self.extension_dir     = 'menu'
        self._extensions       = XikiExtensions(self)
        self.encoding          = 'utf-8'
        self.lock              = threading.Lock()

    def lock_acquire(self):
        log.debug("acquire lock")
        #import spdb ; spdb.start()
        self.lock.acquire()

    def lock_release(self):
        log.debug("release lock")
        self.lock.release()

    def locked(self):
        return self

    def __enter__(self):
        self.lock_acquire()
        return self

    def __exit__(self, type, value, traceback):
        log.debug("exiting locked section: %s, %s, %s", type, value, traceback)
        self.lock_release()

    def exec_code(self, code, globals=None, locals=None):
        return exec_code(code, globals, locals)

    def extensions(self):
        self._extensions.update(self.extension_dir)
        return self._extensions

    def extensions_list(self, layer=None, path=None):
        """layer may be system, user or project"""
        if layer == 'user':
            dir = self.user_root
        elif layer == 'project':
            # dunno
            pass
        elif layer == 'system':
            pass

    def extensions_edit(self, path, layer='user', content=None):
        pass

    def get_setting(self, name, default=None, namespace=None, layer=None):
        settings = self.get_data("settings/%s" % namespace, default={})

        if not settings:
            return default

        return settings.get(name, default)

    def set_setting(self, name, value, namespace=None, layer=None):
        settings = self.get_data("settings/%s" % namespace, default={})

        if not settings:
            settings = {}

        settings[name] = value
        self.put_data("settings/%s" % namespace, settings, overwrite=True)

    def settings(self, namespace=None, layer=None):
        return self.get_data("settings/%s" % namespace, default={})

    def contexts(self):
        """Protocol for contexts:

        - Yield all contexts, except the menu context and the default
          context.
        - Yield menu context.
        - Yield default context.
        """
        default = None
        menu = None
        for ctx in list(XikiContext):
            if ctx.__name__ == "XikiDefaultContext":
                default = ctx
                continue
            if ctx.__name__ == 'menu':
                menu = ctx
                continue
            if ctx.__module__.startswith('xiki.contexts'):
                yield ctx
            if ctx.__module__.endswith('.xiki.contexts'):
                yield ctx
            if ctx.__module__.startswith('xiki.%s' % self.name):
                yield ctx

        if menu:
            yield menu

        if default:
            yield default

    def parse_data(self, string):
        from .parser import parse
        return parse(str(string))

    def assemble_data(self, data):
        from .parser import assemble
        return assemble(data)

    def isroot(self):
        if isinstance(self, BaseXiki):
            return True
        return False


    def _get_storage(self, storage, type):
        if storage is None:
            storage = self.default_storage

        path = self.expand_dir(storage)

        menu_dir = os.path.join(path, type)
        if not self.exists(menu_dir):
            self.makedirs(menu_dir)

        return menu_dir


    def list_data(self, name, storage=None, type=None):
        if type is None:
            type = self.extension_dir

        menu_dir = self._get_storage(storage, type)
        path = menu_dir
        if name:
            name = str(name)
            path = os.path.join(menu_dir, name)

        return self.listdir(path)


    def put_data(self, name, data, storage=None, type=None, overwrite=False):
        if type is None:
            type = self.extension_dir

        menu_dir = self._get_storage(storage, type)
        name     = str(name)
        filepath = os.path.join(menu_dir, name)

        if not os.path.splitext(filepath)[1]:
            filepath += self.default_extension

        if self.exists(filepath) and not overwrite:
            raise XikiFileAlreadyExists("File already exists: %s" % filepath)

        if not isinstance(data, (str, bytes)):
            if type == self.extension_dir:
                data = self.assemble_data(data)
            else:
                data = json.dumps(data)

        self.write_file(filepath, data)

        return data


    def get_data(self, name, storage=None, type=None, default=None):
        if type is None:
            type = self.extension_dir

        menu_dir = self._get_storage(storage, type)

        filepath = os.path.join(menu_dir, str(name))

        if not self.exists(filepath):
            return default

        result = self.read_file(filepath)
        if result:
            if result[0] in '"[{':
                try:
                    return json.loads(result)
                except:
                    pass
            if type == self.extension_dir:
                try:
                    return self.parse_data(result)
                except:
                    pass

        return result

    #def search_data(self, name=None, type=None, **query):


    def change_bullet(self, line, bullet):
        '''exchanges the bullet from line, if it is a bullet'''
        line = line.strip()
        b = BULLET_RE.match(line)
        if b:
            return bullet+line[1:]
        return None

    def prompt(self):
        if hasattr(self, 'PS1'):
            return self.PS1
        return None

    def snippet(self, s):
        return Snippet(s)

    def get_xiki(self):
        return self

    def tempfile(self, name, content):
        import tempfile
        x = tempfile.gettmpdir()
        x = os.path.join(x, name)
        self.write_file(name, content)
        return x


    def cached_file(self, filename):
        content = self.read_file(filename)


    def open_file(self, filename, opener=None, text_opener=None, bin_opener=None, content=None):
        '''open a file in current environment.  Usually you would here
        hook in your editor'''

        from .util import os_open, is_text_file

        if not self.exists(filename):
            if text_opener:
                return text_opener(filename)

            if opener:
                return opener(filename)

            if content:
                return content.splitlines(1)

            return ""

        if is_text_file(filename, self.read_file(filename, 512)):

            if text_opener:
                r = text_opener(filename)
                if r is not None:
                    return r
            if opener:
                r = opener(filename)
                if r is not None:
                    return r

                #filename += xiki.default_extension

            def _reader():
                with open(filename, 'r') as f:
                    for line in f:
                        yield line
            return _reader()

        else:
            if bin_opener:
                r = bin_opener(filename)
                if r is not None:
                    return r

            if opener:
                r = opener(filename)
                if r is not None:
                    return r

            if platform.system() == 'Linux':
                os_open(filename, 'xdg-open')

            elif platform.system() == 'Windows':
                os_open(filename, 'start')

            elif platform.system() == 'OSX':
                os_open(filename, 'open')

            else:
                raise NotImplementedError("Unhandled system: %s" % platform.system())

            return None

    def close_file(self, filename):
        return None

    def get_project_dirs(self):
        '''return root project directories. these are only the names, which
        will be expanded by expand_dir'''

        return []

    def get_system_dirs(self):
        '''return system directories, these are only the names, wich will be
        expanded by expand_dir'''

        return []

    # def get_user_dirs(self):
    #   if hasattr(self, 'user_root'):
    #       return [ self.user_root ]
    #   return []

    def expand_dir(self, path):
        '''expand project and system directory names here'''
        if path in self.storage:
            return self.storage[path]
        raise XikiLookupError("Storage %s not found" % path)

    def shell_expand(self, path):
        '''expands ~ and shellvars in current environment'''
        return os.path.expandvars(os.path.expanduser(path))


    def register_plugin(self, name, root=None):

        if root is None:
            root = self.plugin_root

        if isinstance(root, list):
            for r in root:
                self.register_plugin(name, r)
            return

        log.info("register plugin %s -> %s", name, root)

        res_location = "%s/%s/" % (root, name)
        loclen = len(res_location)

        if name not in self.plugins:
            self.plugins[name] = {'files': set(), 'root': res_location[:-1] }

        for r in self.walk(root):
            if r.startswith(res_location):
                self.plugins[name]['files'].add(r[loclen:])


    def get_search_path(self, name):
        log.debug("search_paths: %s", self.search_paths)

        if name in self.search_paths:
            if self.search_paths[name]:
                return self.search_paths[name]

        slashed_name = name
        if not slashed_name.endswith('/'):
            slashed_name += '/'

        search_path = []
        if hasattr(self, 'user_root'):
            search_path.append("%s/%s" % (self.user_root, name))

        for p in self.get_project_dirs():
            search_path.append("%s/%s" % (self.expand_dir(p), name))

        for p in self.get_system_dirs():
            search_path.append("%s/%s" % (self.expand_dir(p), name))

        for p in self.plugins:
            plugin_files = self.plugins[p]['files']
            root = self.plugins[p]['root']
            for f in plugin_files:
                if f.startswith(slashed_name):
                    search_path.append('%s/%s' % (root, name))
                    break

        self.search_paths[name] = search_path

        log.debug("search_path: %s", search_path)
        return search_path

    def open(self, path, input=None, cont=False):
        self.extensions()
        return XikiPath(path).open(self, input=input, cont=cont)

    def close(self, path, input=None):
        self.extensions()
        return XikiPath(path).close(self, input=input)


    # FileSystemInterface -----------------------------------------------------

    def isdir(self, path):
        result = os.path.isdir(path)
        log.debug("isdir? %s, %s", path, result)
        return result

    def listdir(self, dir):
        '''list directory content without '.' and '..' '''
        for x in os.listdir(dir):
            if os.path.isdir(os.path.join(dir, x)):
                yield x+"/"
            else:
                yield x

    def exists(self, filepath):
        return os.path.exists(filepath)

    def walk(self, root):
        for dir, dirs, files in os.walk(root):
            if '.git' in dirs: dirs.remove('.git')
            if '.hg'  in dirs: dirs.remove('.hg')
            if '.svn' in dirs: dirs.remove('.svn')
            for fn in files:
                fn = os.path.join(dir, fn).replace('\\', '/')
                yield fn

    def getmtime(self, path):
        return os.path.getmtime(path)

    def write_file(self, filepath, content):
        dirname = os.path.dirname(filepath)
        if not self.exists(dirname):
            self.makedirs(dirname)

        with open(filepath, 'w') as f:
            f.write(content)

    def read_file(self, filename, count=None):
        '''read first count bytes/chars from filename. If you pass no 
        count, entire content of file is returned'''

        with open(filename, 'r') as f:
            if count is None:
                return f.read()
            else:
                return f.read(count)

    def getcwd(self):
        return os.getcwd()

    def makedirs(self, *path):
        '''make all directories in given path'''

        path = os.path.join(*path)
        if not os.path.isabs(path):
            path = os.path.join(self.getcwd(), path)
        return os.makedirs(path)


    # StaticVariableInterface -------------------------------------------------

    def get_static(self, name, default=None, namespace=None):

        assert namespace is not None, "namespace must be given"

        if namespace not in self.static_vars:
            return default

        return self.static_vars[namespace].get(name, default)


    def set_static(self, name, value, namespace):

        if namespace not in self.static_vars:
            self.static_vars[namespace] = {}

        self.static_vars[namespace][name] = value

    def clear_static(self, namespace):

        self.static_vars[namespace] = {}

    # ExecuteProgramInterface -------------------------------------------------

    def execute(self, *args, **kargs):
        log.debug("execute args: %s", args)
        log.info("Executing: %s", cmd_string(args))
        #import rpdb2 ; rpdb2.start_embedded_debugger('foo')
        if 'cwd' not in kargs:
            kargs['cwd'] = self.getcwd()

        stdin = None
        if 'input' in kargs:
            if kargs['input'] is not None:
                stdin = kargs['input']
                kargs['stdin'] = subprocess.PIPE

            del kargs['input']

        encoding = self.encoding
        if 'encoding' in kargs:
            encoding = kargs['encoding']
            del kargs['encoding']

        log.info("kargs: %s", kargs)

        if subprocess.mswindows:
            su = subprocess.STARTUPINFO()
            su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            su.wShowWindow = subprocess.SW_HIDE
            kargs['startupinfo'] = su

        p = subprocess.Popen( list(args), stdout = subprocess.PIPE, 
            stderr = subprocess.STDOUT, **kargs )

        if stdin:
            import errno
            try:
                p.stdin.write(stdin.encode(encoding))
            except IOError as e:
                if e.errno != errno.EPIPE:
                    raise
            p.stdin.close()

        for line in iter(p.stdout.readline,''):
            log.debug("got line: %s", line)
            if isinstance(line, bytes):
                line = line.decode(encoding).replace('\r', '')
            yield line
            if p.poll() is not None:
                break

        log.debug("get rest of output")
        data = p.stdout.read()
        if isinstance(data, bytes):
            data = data.decode(encoding)
        if data:
            for line in data.splitlines(1):
                yield line

        log.debug("waiting for process")
        self.last_exit_code[threading.current_thread().name] = p.wait()
        log.debug("done")
        #return self.menu()

    def get_last_exit_code(self):
        return self.last_exit_code[threading.current_thread().name]

    def execute_output(self, *args, **kargs):
        return ''.join([ x for x in self.execute(*args, **kargs)])

    def execute_result(self, *args, **kargs):
        self.execute_output(self, *args, **kargs)
        return self.get_last_exit_code()

    def execute_shell(self, command, **kargs):
        return self.execute( *(self.shell + [command]), **kargs )
        return self.execute( *(self.shell + [cmd_string(command, quote="'")]), **kargs )

    # CompletionInterface -----------------------------------------------------
    
    def complete(self, prefix, before="", after=""):
        return None

class MemXiki(BaseXiki):
    STORAGE = {}

    def write_file(self, path, content):
        self.STORAGE[path] = content

    def read_file(self, path, count=-1):
        if path in self.STORAGE:
            if count is not None and count > 0:
                return self.STORAGE[path][:count]
        return BaseXiki.read_file(self, path, count=count)

    def exists(self, path):
        if path in self.STORAGE:
            return True
        return BaseXiki.exists(self, path)

    def makedirs(self, path):
        return None

class ConsoleXiki(BaseXiki):
    def __init__(self, user_root="~/.pyxiki", plugin_root=None):
        BaseXiki.__init__(self)
        self.user_root = os.path.expandvars(os.path.expanduser(user_root))
        if plugin_root is None:
            plugin_root = []

        self.plugin_root = plugin_root

        # register xiki
        plugin_root = os.path.join(os.path.dirname(__file__), '..')
        plugin_root = os.path.abspath(plugin_root)
        self.register_plugin('xiki', root=plugin_root)

class ProxyXiki:
    def __init__(self, xiki):
        self.xiki = xiki

    def __getattr__(self, name):
        log.debug("proxy: %s", name)
        return getattr(self.xiki, name)


class Registry(type):
    '''XikiCommand Registration'''

    def __init__(cls, name, bases, nmspc):
        super(Registry, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, 'registry'):
            cls.registry = {}

        for b in cls.__bases__:
            if b.__name__ in cls.registry:
                del cls.registry[b.__name__]

        if cls.__name__ in cls.registry:
            if hasattr(cls.registry[cls.__name__], 'unload'):
                cls.registry[cls.__name__].unload()

        log.debug("registered %s", cls.__name__)

        cls.registry[cls.__name__] = cls
        if hasattr(cls, 'loaded'):
            cls.loaded()

    def stash(cls, name):
        if not hasattr(cls, registries):
            cls.registries = {}

        cls.registries[name] = self.registry.copy()

    def emerge(cls, name):
        if not hasattr(cls, registries):
            cls.registries = {}

        self.registry = cls.registries[name]


    # Metamethods, called on class objects:
    def __iter__(cls):
        log.debug("values: %s", [x for x in cls.registry.values()])
        return iter(cls.registry.values())

    def __str__(cls):
        if cls.__name__ in cls.registry:
            return cls.__name__
        return cls.__name__ + ": " + ", ".join([sc.__name__ for sc in cls])

class XikiBase(object):
    def __init__(self, ctx=None):
        self.context     = ctx

RegExp = re.compile('').__class__

@add_metaclass(Registry)
class XikiContext(
    XikiBase, 
    NamespaceInterface,
    StaticVariableInterface,
    ExecuteProgramInterface,
    SettingsInterface,
    CompletionInterface,
    FileSystemInterface,
    PromptInterface,
    ):

    CONTEXT = None
    PATTERN = None

    NAME = None
    MENU = None

    def __init__(self, *args, **kargs):
        XikiBase.__init__(self, *args, **kargs)

        if isinstance(self.PATTERN, str):
            self.PATTERN = re.compile(self.PATTERN)

        self.node_path = None
        self.xiki_path = None
        self.subcontext = None

    def __getattr__(self, name):
        if self.context:
            return getattr(self.context, name)

        raise AttributeError("%s has not attribute %s" % (self.__class__.__name__, name))

    def __str__(self):
        if self.NAME:
            return self.NAME

        name = self.__class__.__name__
        if name.startswith('Xiki_'):
            name = name[5:]
        if name.startswith('Xiki'):
            name = name[4:].lower()
        if name.lower().endswith('context'):
            name = name[:-7].lower()
        return name

    def does(self, xiki_path):
        '''
        If you overwrite this method, make sure, that you set attributes
        ``node_path`` and ``dispatch_path``.  ``node_path`` represents 
        consumed node_path input and ``dispatch_path`` is the unconsumed
        node_path, which still has to be dispatched to other handlers.
        '''

        if not xiki_path:
            return False

        self.mob = None
        if self.PATTERN:
            self.mob = self.PATTERN.search(xiki_path[0])
            if self.mob:
                try:
                    xp = self.mob.group('xiki_path')
                except:
                    xp = None

                self.xiki_path = xiki_path[1:]
                if xp:
                    self.xiki_path.path.insert(0, (xp, 0))

                data_name = "%s_data" % self.__class__.__name__
                setattr(self, data_name, self.mob.groupdict())

                return True

        elif self.CONTEXT:
            if isinstance(self.CONTEXT, RegExp):
                self.mob = self.CONTEXT.search(xiki_path[0])
                if self.mob:
                    self.xiki_path = xiki_path[1:]
                    return True

            if isinstance(self.CONTEXT, str):
                if self.CONTEXT == xiki_path[0]:
                    self.xiki_path = xiki_path[1:]
                    return True

            if callable(self.CONTEXT):
                return self.CONTEXT(xiki_path)

        log.debug("?? %s == %s", self.__class__, xiki_path[0])
        if str(self.__class__) == xiki_path[0]:
            self.xiki_path = xiki_path[1:]
            return True

        return False

    def get_context(self):
        '''returns the actual context, who will do the work.  In :method:`does`
        you may create subcontexts.  The leaf of these subcontexts shall be
        stored in self.subcontext, which is returned here.
        '''

        if self.subcontext:
            return self.subcontext
        else:
            return self

    def root_menuitems(self):
        return ""

    def menu(self):
        if hasattr(self, '__doc__'):
            return self.__doc__

        return ''

    def open(self, input=None, cont=None):
        if self.xiki_path:
            log.debug("open: redirect")
            return self.xiki_path.open(context=self, input=input, cont=cont)
        return self.menu()

    def expanded(self, input=None, cont=None):
        return self.open(input=input, cont=cont)

    def close(self, input=None):
        if self.xiki_path:
            try:
                log.debug("close: redirect")
                return self.xiki_path.close(context=self, input=input)
            except LookupError:
                return None

    @classmethod
    def loaded(cls):
        '''implement this to do something after this class is loaded'''

    @classmethod
    def unload(cls):
        '''implement this function if you have to unload anything'''

class XikiDefaultContext(XikiContext):
    def does(self, path):
        self.my_path = path
        return True

    def menu(self):
        return "There is no context to handle %s" % self.my_path
