# ../avsd/core/modules/base.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
#   Configobj
from configobj import ConfigObj
#   Importlib
from importlib import import_module
#   Sys
from sys import modules

# Source.Python Imports
#   Core
from core import AutoUnload
from core import WeakAutoUnload
#   Plugins
from plugins.manager import PluginManager

# AvsD Imports
#   Constants
from ..constants import MENU_MISSING_TEXT
from ..constants.paths import CFG_PATH
#   Translations
from ..translations.strings import LangStrings


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ()


# =============================================================================
# >> CLASSES
# =============================================================================
class _BaseManager(dict):
    def clear(self):
        raise NotImplementedError()

    def load_all(self):
        config = ConfigObj(CFG_PATH / '{0}.ini'.format(self.module), unrepr=True)

        for name, enabled in config.items():
            if enabled:
                self.load(name)

    def load(self, name):
        module = import_module('avsd.modules.{0}.{1}'.format(self.module, name))

        self[name] = module

    def unload_all(self):
        for x in list(self):
            self.unload(x)

    def unload(self, name):
        module_name = 'avsd.modules.{0}.{1}'.format(self.module, name)

        _remove_unload_instances(module_name)

        del self[name]

        del modules[module_name]

    @property
    def module(self):
        raise NotImplementedError()


class _BaseSettings(object):
    def __init__(self, name):
        self._name = name.rsplit('.')[~0]
        self._config = ConfigObj(self.path / '{0}.ini'.format(self.name), unrepr=True)
        self._strings = _LangStrings('classes_strings/{0}'.format(self.name))

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return self._name

    @property
    def strings(self):
        return self._strings

    @property
    def module(self):
        raise NotImplementedError()

    @property
    def path(self):
        raise NotImplementedError()


# TODO: Derpy check to make sure menus don't break even if there's a missing item
class _LangStrings(LangStrings):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            return MENU_MISSING_TEXT


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def _remove_unload_instances(name):
    """Helper cleanup function for when skills are unloaded."""
    # Does the skill have anything that should be auto unloaded?
    if name in AutoUnload._module_instances:
        # Call the PluginManager's method, so they get correctly removed
        PluginManager._unload_auto_unload_instances(AutoUnload._module_instances[name])
        # Remove the skill from the PluginManager
        del AutoUnload._module_instances[name]

    # Does the skill have anything that should be auto unloaded?
    if name in WeakAutoUnload._module_instances:
        # Call the PluginManager's method, so they get correctly removed
        PluginManager._unload_auto_unload_instances(WeakAutoUnload._module_instances[name].values())
        # Remove the skill from the PluginManager
        del WeakAutoUnload._module_instances[name]
