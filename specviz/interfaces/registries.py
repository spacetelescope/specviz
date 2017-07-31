import os, sys

import importlib
import inspect


class Registry(object):
    """
    Maintains a set of referential objects.

    Attributes
    ----------
    members: list
        The list of members belonging to this registry.
    """
    def __init__(self):
        self._members = []

    @property
    def members(self):
        return self._members

    def add(self, member):
        self._members.append(member)

    def get(self):
        raise NotImplementedError()


class PluginRegistry(Registry):
    """Loads and stores custom plugins."""
    def __init__(self):
        super(PluginRegistry, self).__init__()

        usr_path = os.path.join(os.path.expanduser('~'), '.specviz')

        # This order determines priority in case of duplicates; paths higher
        # in this list take precedence
        check_paths = [usr_path]

        if not os.path.exists(usr_path):
            os.mkdir(usr_path)

        for path in check_paths:
            for mod in [x for x in os.listdir(path) if x.endswith('.py')]:
                mod = mod.split('.')[0]

                sys.path.insert(0, path)

                mod = importlib.import_module(mod)

                cls_members = inspect.getmembers(
                    mod, lambda member: inspect.isclass(member)
                                        and 'Plugin' in [x.__name__
                                                         for x in
                                                         member.__bases__])

                for cls_name, cls_plugin in cls_members:
                    self._members.append(cls_plugin)

                sys.path.pop(0)


plugin_registry = PluginRegistry()