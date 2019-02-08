# ../avsd/core/menus/base.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Menus
from menus.base import _translate_text
from menus.radio import PagedRadioMenu as SPPagedRadioMenu
from menus.radio import PagedRadioOption as SPPagedRadioOption
from menus.radio import BUTTON_BACK
from menus.radio import BUTTON_NEXT
from menus.radio import BUTTON_CLOSE_SLOT

# AvsD Imports
#   Translations
from ..translations import menu_strings


# ============================================================================
# >> CLASSES
# ============================================================================
class PagedMenu(SPPagedRadioMenu):
    def __init__(self, *args, **kwargs):
        kwargs['top_separator'] = ' '
        kwargs['bottom_separator'] = None

        super().__init__(*args, **kwargs)

    def _format_header(self, player_index, page, slots):
        buffer = '{0}\n'.format(_translate_text(self.title, player_index) if self.title else '')

        if self.description is not None:
            buffer += _translate_text(self.description, player_index) + '\n'

        if self.top_separator is not None:
            buffer += self.top_separator + '\n'

        return buffer

    def _format_footer(self, player_index, page, slots):
        buffer = ''

        if self.bottom_separator is not None:
            buffer += self.bottom_separator + '\n'

        if page.index > 0 or self.parent_menu is not None:
            buffer += SPPagedRadioOption(menu_strings['back'])._render(player_index, BUTTON_BACK)

            slots.add(BUTTON_BACK)
        else:
            buffer += ' \n'

        if page.index < self.last_page_index:
            buffer += SPPagedRadioOption(menu_strings['next'])._render(player_index, BUTTON_NEXT)

            slots.add(BUTTON_NEXT)
        else:
            buffer += ' \n'

        buffer += SPPagedRadioOption(
            menu_strings['close'], highlight=False)._render(player_index, BUTTON_CLOSE_SLOT)

        return buffer
