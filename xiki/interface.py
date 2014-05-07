"""
Xiki Interfaces
===============

Here you find functions of :class:`XikiContext` grouped by Interfaces for 
documentation reasons.

If you implement one of the interfaces in your :class:`XikiContext` subclass,
you may provide the interfaces in your base class for better readability.  
Please use them always after :class:`XikiContext`, which is the major base 
class.

"""

def dispatch(method):
    method_name = method.__name__

    def dispatcher(self, *args, **kargs):
        return getattr(self.context, method_name)(*args, **kargs)

    dispatcher.__doc__  = method.__doc__
    dispatcher.__name__ = method_name

    return dispatcher

class Interface:
    """Base class for interfaces.
    """
    def __init__(self, context):
        self.context = context

class ExecuteProgramInterface(Interface):
    """Interface to program execution.
    """

    @dispatch
    def execute(self, *args, **kargs):
        """This method executes external programs and generates lines of output.
        So there is returned a generator, which yields line by line of program
        output.

        First argument is the program's name, other arguments are program's 
        parameters.  If you do output redirection to a file or a program, 
        command is passed to a shell.

        :param cwd:
            Current working directory.

        :param input:
            The program's input to stdin.

        :param encoding:
            Defaults to xiki's encoding
        """

    @dispatch
    def execute_shell(self, *args, **kargs):
        """Use shell to execute given program. See :method:`execute` for more
        information."""

    @dispatch
    def get_last_exit_code(self):
        """return last exit code of program executed by :method:`execute`"""

    @dispatch
    def execute_output(self, *args, **kargs):
        """run :method:`execute` and return its output as single string."""

    @dispatch
    def execute_result(self, *args, **kargs):
        """run :method:`execute` and return its exit code."""

class NamespaceInterface(Interface):
    """This Interface lets you implement a method to return name of current
    namespace.
    """
    NAMESPACE = None

    def get_namespace(self):
        if self.NAMESPACE is None:
            return str(self)
        return self.NAMESPACE

    def get_namespaces(self):
        """return a list of user defined namespaces for this context"""
        namespaces = self.get_setting(".namespaces", namespace=str(self), default=[])
        return set(namespaces)

    def del_namespace(self, namespace):
        namespaces = self.get_namespaces()
        if namespace in namespaces:
            namespaces.discard(namespace)
            self.set_setting('.namespaces', list(namespaces), namespace=str(self))

    def set_namespace(self, namespace):
        namespaces = self.get_namespaces()
        if namespace not in namespaces:
            namespaces.add(namespace)
            self.set_setting('.namespaces', list(namespaces), namespace=str(self))
        self.NAMESPACE = namespace


class StaticVariableInterface(Interface):
    """This Interface provides static variable handling.  Static variables
    are intended to be bound to a special Xiki instance, but live for multiple 
    XikiRequests.

    This 
    """

    def get_static(self, name, default=None, namespace=None):
        """Get value of :param:`name` in :param:`namespace`.  Use 
        :param:`default`, if value not present.

        :param name:
        :param default:
        :param namespace:
            optional, if not given it defaults to name of calling 
            :class:`XikiContext` subclass.
        """

        if namespace is None:
            namespace=self.get_namespace()

        return self.context.get_static(name, default=default, namespace=namespace)

    def set_static(self, name, value, namespace=None):
        """Set :param:`name` in :param:`namespace` to :param:`value`.

        :param name:
        :param value:
        :param namespace:
            optional, if not given it defaults to name of calling 
            :class:`XikiContext` subclass.
        """

        if namespace is None:
            namespace=self.get_namespace()

        return self.context.set_static(name, value, namespace=namespace)

    def clear_static(self, namespace=None):
        """Clear all static variables of given namespace.  If :param:`namespace`
        not present, all static variables are cleared.

        :param namespace:
            optional, if not given it defaults to name of calling 
            :class:`XikiContext` subclass.
        """
        if namespace is None:
            namespace=self.get_namespace()

        return self.context.clear_static(namespace=namespace)


class CompletionInterface(Interface):

    def complete(self, prefix, before="", after=""):
        """
        :param prefix:
            Thing, which shall be completed.

        :param before:
            Some text before the cursor including the prefix.

        :param after:
            Some text after cursor.

        """

        return []


class PromptInterface(Interface):
    """If your context provides a prompt, and you want to have shell-like
    behaviour in editor, you will have to feed or implement this interface.

    Feed it by simply setting :attr:`PS1`.

    :attribute PS1:
        Prompt String 1.
    """

    PS1 = None

    def prompt(self):
        """Return prompt."""
        if self.PS1:
            return self.PS1
        return None


import os

class FileSystemInterface(Interface):

    @dispatch
    def isdir(self, path):
        """Tell if :param:`path` is directory or not.

        :param path:
        """

    @dispatch
    def listdir(self, path):
        '''list directory content without '.' and '..' 

        :param path:
        '''

    @dispatch
    def exists(self, path):
        """tell if :param:`path` exists or not.

        :param path:
        """

    @dispatch
    def walk(self, path):
        """walk :param:`path` and yield all existing filenames including
        :param:`path`.

        :param path:
        """

    @dispatch
    def getmtime(self, path):
        """return last modification time of :param:`path`

        :param path:
        """

    @dispatch
    def write_file(self, path, content):
        """write :param:`content` to :param:`path`.

        :param path:
        :param content:
        """

    @dispatch
    def read_file(self, path, count=None):
        '''read first count bytes/chars from filename. If you pass no 
        count, entire content of file is returned

        :param path:
        :param count:
        '''

    @dispatch
    def getcwd(self):
        """return current working directory"""

    @dispatch
    def makedirs(self, *path):
        '''make all directories in given path, path may be spread over 
        arguments and will be joined by directory separator

        :param path:
        '''

    @dispatch
    def tempfile(self, name, content):
        """create a tempfile.
        """


class DataInterface(Interface):
    """This interface provides reader and writer for data."""


class SettingLayer:
    def __init__(self, value):
        self.value = value

class UserSetting(SettingLayer):
    pass

class ProjectSetting(SettingLayer):
    pass


class SettingsInterface(Interface):
    """This interface is intended to handle persistent configuration settings.
    """
    SETTINGS = {}

    def get_setting(self, name, default=None, namespace=None, layer=None):
        """Get value of :param:`name` in :param:`namespace`.  Use 
        :param:`default`, if value not present.

        :param name:
        :param default:
        :param namespace:
            optional, if not given it defaults to name of calling 
            :class:`XikiContext` subclass.
        """
        if namespace is None:
            namespace=self.get_namespace()

        if isinstance(self.SETTINGS, str):
            import spdb ; spdb.start()

        _default = self.SETTINGS.get(name)

        if isinstance(_default, UserSetting):
            layer = 'user'
            _default = _default.value

        if isinstance(_default, ProjectSetting):
            layer = 'project'
            _default = _default.value

        if default is None:
            default = _default

        return self.context.get_setting(name, default, namespace=namespace, layer=layer)

    def set_setting(self, name, value, namespace=None, layer=None):
        """Set :param:`name` in :param:`namespace` to :param:`value`.

        :param name:
        :param value:
        :param namespace:
            optional, if not given it defaults to name of calling 
            :class:`XikiContext` subclass.
        """
        if namespace is None:
            namespace=self.get_namespace()

        return self.context.set_setting(name, value, namespace=namespace, layer=layer)

    def settings(self, namespace=None, layer=None):
        """return a dictionary like object holding all settings.
        """
        if namespace is None:
            namespace=self.get_namespace()

        settings = self.context.settings(namespace=namespace, layer=layer)

        for k,v in self.SETTINGS.items():

            if isinstance(v, SettingLayer):
                v = v.value

            if k not in settings:
                settings[k] = v

        return settings


