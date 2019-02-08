# ../avsd/core/constants/__init__.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
#   Paths
from paths import CFG_PATH as _CFG_PATH
from paths import TRANSLATION_PATH as _TRANSLATION_PATH
from paths import PLUGIN_DATA_PATH

# AVSD Imports
#   Constants
from .info import info


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'CFG_PATH',
    'CLASS_CFG_PATH',
    'DATA_PATH',
    'STRUCTURE_PATH',
    'TRANSLATION_PATH',
)


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
# Configuration path
CFG_PATH = _CFG_PATH / info.name
# Class configuration path
CLASS_CFG_PATH = CFG_PATH / 'classes'
# Translation path
TRANSLATION_PATH = _TRANSLATION_PATH / info.name
# Data path
DATA_PATH = PLUGIN_DATA_PATH / info.name
# Structure path
STRUCTURE_PATH = DATA_PATH / 'structure'


# Loop through all our directories
for _name in __all__:
    # Get the path.Path instance
    _path = globals()[_name]

    # Does the directory not exist?
    if not _path.isdir():
        # Create it
        _path.mkdir()
