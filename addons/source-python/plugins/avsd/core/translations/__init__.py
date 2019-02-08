# ../avsd/core/translations/__init__.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# AvsD Imports
#   Translations
from .strings import LangStrings


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'config_strings',
    'menu_strings',
    'chat_strings',
    'items_strings',
    'ui_strings',
)


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
# Language strings for the configuration
config_strings = LangStrings('config_strings')
# Language strings for the menus
menu_strings = LangStrings('menu_strings')
# Language strings for the chat
chat_strings = LangStrings('chat_strings')
# Language strings for the chat
items_strings = LangStrings('items_strings')
# Language strings for the UI
ui_strings = LangStrings('ui_strings')
