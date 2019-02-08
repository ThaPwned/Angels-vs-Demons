# ../avsd/core/constants/__init__.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
#   Enum
from enum import IntEnum
#   Re
from re import compile as re_compile

# AvsD Imports
#  Translations
from ..translations.strings import TranslationStrings


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'DIFFICULTY_CHAR',
    'DIFFICULTY_CHAR_EMPTY',
    'EMULATE_ABILITY_CHANCE',
    'MAX_CASH',
    'MENU_MISSING_TEXT',
    'QUEST_RESET_REGEX',
    'ItemQuality',
    'MailStatus',
    'QuestSort',
)


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
# CRYSTAL_CHAR = chr(10070)
CRYSTAL_CHAR = chr(9830)
DIFFICULTY_CHAR = chr(9733)
DIFFICULTY_CHAR_EMPTY = chr(9734)

EMULATE_ABILITY_CHANCE = 0.5

MAX_CASH = 50000

QUEST_RESET_REGEX = re_compile(r'([a-zA-Z]+)(\(?[:a-zA-Z0-9]*\))?')

# MENU_MISSING_TEXT = '-> MISSING <-'


# =============================================================================
# >> CLASSES
# =============================================================================
class ItemQuality(IntEnum):
    POOR = 0
    NORMAL = 1
    RARE = 2
    EXCEPTIONAL = 3
    PERFECT = 4

    @classmethod
    def from_str(cls, name):
        return getattr(cls, name.upper())


class MailStatus(IntEnum):
    NEW = 0
    READ = 1
    REWARDED = 2
    DELETE = 3


class QuestSort(IntEnum):
    DEFAULT = 0
    NAME_ASC = 1
    NAME_DESC = 2
    PROGRESS_ASC = 3
    PROGRESS_DESC = 4


class _MissingText(TranslationStrings):
    # def __getitem__(self, item):
    #     return '-> MISSING <-'

    def get_string(self, *a, **kw):
        return '-> MISSING <-'
MENU_MISSING_TEXT = _MissingText()
