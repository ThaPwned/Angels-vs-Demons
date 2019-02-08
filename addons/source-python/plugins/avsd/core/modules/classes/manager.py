# ../avsd/core/modules/classes/manager.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# AvsD Imports
#   Constants
from ...constants import MENU_MISSING_TEXT
#   Listeners
from ...listeners import OnPluginClassLoad
from ...listeners import OnPluginClassUnload
#   Modules
from ..base import _BaseManager


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'class_manager',
)


# =============================================================================
# >> CLASSES
# =============================================================================
class _ClassManager(_BaseManager):
    module = 'classes'

    def load(self, name):
        super().load(name)

        OnPluginClassLoad.manager.notify(name, self[name])

    def unload(self, name):
        OnPluginClassUnload.manager.notify(name, self[name])

        super().unload(name)

    def _get_default(self, class_type):
        for name, class_ in self.items():
            config = class_.settings.config

            if config['class'] == class_type:
                if config.get('is_default', False):
                    return name

        if self:
            classes = list([name for name, class_ in self.items() if class_.settings.config['class'] == class_type])

            if classes:
                return classes[0]

        raise ValueError('Requires atleast 1 default class of "{0}".'.format(class_type))

    def _validate(self, debug=True):
        from warnings import warn

        for name, class_ in self.items():
            for skill, data in class_.settings.config['skills'].items():
                if 'max' not in data:
                    data['max'] = 1

                    if debug:
                        warn("Missing 'max' key in {0}'s config file for '{1}'".format(name, skill))

                for x in ('name', 'description', 'role', 'lore'):
                    if x not in class_.settings.strings:
                        warn("Missing '{0}' in {1}'s strings files".format(x, name))

                # if skill.lower() not in class_.settings.strings:
                if skill not in class_.settings.strings:
                    # class_.settings.strings[skill.lower()] = MENU_MISSING_TEXT
                    class_.settings.strings[skill] = MENU_MISSING_TEXT

                    if debug:
                        # warn("Missing '{0}' in {1}'s strings files".format(skill.lower(), name))
                        warn("Missing '{0}' in {1}'s strings files".format(skill, name))

                # if '{0} description'.format(skill.lower()) not in class_.settings.strings:
                if '{0} description'.format() not in class_.settings.strings:
                    # class_.settings.strings['{0} description'.format(skill.lower())] = MENU_MISSING_TEXT
                    class_.settings.strings['{0} description'.format(skill)] = MENU_MISSING_TEXT

                    if debug:
                        # warn("Missing '{0} description' in {1}'s strings files".format(skill.lower(), name))
                        warn("Missing '{0} description' in {1}'s strings files".format(skill, name))

            # for level, unlocks in class_.settings.config['unlocks'].items():
            for unlocks in class_.settings.config['unlocks'].values():
                if not isinstance(unlocks, tuple):
                    unlocks = [unlocks]
                # if isinstance(unlocks, tuple):
                #     unlocks = list(unlocks)
                # else:
                #     unlocks = [unlocks]

                for unlock in list(unlocks):
                    if unlock.startswith('unlock'):
                        try:
                            _, skill = unlock.split(':')
                        except ValueError:
                            # unlocks.remove(unlock)

                            if debug:
                                warn("Invalid format of unlock '{0}' in {1}".format(unlock, name))
                        else:
                            if skill not in class_.settings.config['skills']:
                                # unlocks.remove(unlock)

                                if debug:
                                    warn("Invalid skill in '{0}' in {1}".format(unlock, name))
                    elif unlock.startswith(('passive', 'skill')):
                        try:
                            type_, skill, stat, value = unlock.split(':')
                        except ValueError:
                            # unlocks.remove(unlock)

                            if debug:
                                warn("Invalid format of {0} '{1}'".format(type_, unlock))
                        else:
                            if type_ in ('skill', 'passive'):
                                if skill in class_.settings.config[type_ + 's']:
                                    if stat not in class_.settings.config[type_ + 's'][skill]:
                                        # unlocks.remove(unlock)

                                        if debug:
                                            warn("Missing stat '{0}' for unlock '{1}' in {2}".format(stat, unlock, name))
                                else:
                                    # unlocks.remove(unlock)

                                    if debug:
                                        warn("Invalid {0} in unlock '{1}' in {2}".format(type_, unlock, name))
                            else:
                                if debug:
                                    warn("Invalid type '{0}' in unlock '{1}' in {2}".format(type_, unlock, name))
                    else:
                        try:
                            type_, value = unlock.split(':')
                        except ValueError:
                            # unlocks.remove(unlock)

                            if debug:
                                warn("Invalid format '{0}' in {1}".format(unlock, name))
                        else:
                            for ascend, defaults in class_.settings.config['default'].items():
                                if type_ not in defaults:
                                    # unlocks.remove(unlock)

                                    if debug:
                                        warn("Invalid default in {0} unlock '{1}' in {2}".format(ascend, unlock, name))

                    # class_.settings.config['unlocks'][level] = unlocks

    @property
    def default_angel(self):
        return self._get_default('angel')

    @property
    def default_demon(self):
        return self._get_default('demon')
class_manager = _ClassManager()
