# ../avsd/core/modules/classes/settings.py

# =============================================================================
# >> IMPORTS
# =============================================================================

# AvsD Imports
#   Constants
from ...constants.paths import CLASS_CFG_PATH
#   Modules
from ..base import _BaseSettings


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'Settings',
)


# =============================================================================
# >> CLASSES
# =============================================================================
class Settings(_BaseSettings):
    path = CLASS_CFG_PATH
    module = 'classes'

    def __init__(self, name):
        super().__init__(name)

        self._abilities = {}

    def ability(self, ability):
        assert ability.name is not None

        self._abilities[ability.name] = ability(len(self._abilities))
