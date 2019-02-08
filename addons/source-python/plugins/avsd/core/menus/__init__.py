# ../avsd/core/menus/__init__.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
from collections import defaultdict

# Source.Python Imports
#   Events
from events import Event
#   Listeners
from listeners import OnClientDisconnect
from listeners import OnLevelInit
#   Menus
from menus import SimpleMenu

# AvsD Imports
#   Listeners
from ..listeners import OnPlayerItemPickup
from ..listeners import OnPlayerSwitchClassPost
#   Menus
from .base import PagedMenu


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
_players = defaultdict(dict)
_item_general_menu_swaps = []
_general_menu_swaps = []
_general_menu_refreshes = []

main_menu = SimpleMenu()
main2_menu = SimpleMenu()
class_menu = SimpleMenu()
change_class = PagedMenu()
class_info = SimpleMenu()
class_info_angels = PagedMenu()
class_info_demons = PagedMenu()
class_info_detailed = SimpleMenu()
class_info_detailed_skills = PagedMenu()
class_info_detailed_skills_info = PagedMenu()
class_info_detailed_lore = PagedMenu()
ability_menu = PagedMenu()
skill_menu = SimpleMenu()
spend_skills = PagedMenu()
reset_skills = SimpleMenu()
skill_info = PagedMenu()
skill_info_detailed = PagedMenu()
shop_menu = SimpleMenu()
shop_buy_category_menu = PagedMenu()
shop_buy_category_buy_menu = PagedMenu()
shop_buy_category_buy_real_menu = PagedMenu()
shop_sell_menu = PagedMenu()
shop_info_category_menu = PagedMenu()
shop_info_category_info_menu = PagedMenu()
shop_info_category_info_detailed_menu = PagedMenu()
shop_inventory_menu = PagedMenu()
bank_menu = SimpleMenu()
bank_value_menu = PagedMenu()
quests_menu = PagedMenu()
quest_menu = SimpleMenu()
requirements_menu = PagedMenu()
quest_description_menu = PagedMenu()
ascension_menu = SimpleMenu()
ascend_menu = SimpleMenu()
ascension_info_menu = SimpleMenu()
vessel_menu = SimpleMenu()
help_menu = SimpleMenu()
commands_menu = PagedMenu()
# commands_menu = SimpleMenu()
# commands_menu1 = SimpleMenu()
# commands_menu2 = SimpleMenu()
about_menu = SimpleMenu()
mail_menu = SimpleMenu()
mail_inbox_menu = PagedMenu()
mail_view_menu = SimpleMenu()
mail_view_settings_menu = SimpleMenu()
mail_view_settings_verify_menu = SimpleMenu()
item_zone_menu = SimpleMenu()

bank_menu.is_first_round = False
bank_menu.is_allowed_to_withdraw = True

change_class.parent_menu = class_menu
class_info_angels.parent_menu = class_info
class_info_demons.parent_menu = class_info
class_info_detailed_skills.parent_menu = class_info_detailed
class_info_detailed_skills_info.parent_menu = class_info_detailed_skills
class_info_detailed_lore.parent_menu = class_info_detailed
spend_skills.parent_menu = skill_menu
skill_info.parent_menu = skill_menu
skill_info_detailed.parent_menu = skill_info
shop_buy_category_menu.parent_menu = shop_menu
shop_buy_category_buy_menu.parent_menu = shop_buy_category_menu
shop_buy_category_buy_real_menu.parent_menu = shop_buy_category_buy_menu
shop_sell_menu.parent_menu = shop_menu
shop_info_category_menu.parent_menu = shop_menu
shop_info_category_info_menu.parent_menu = shop_info_category_menu
shop_info_category_info_detailed_menu.parent_menu = shop_info_category_info_menu
shop_inventory_menu.parent_menu = shop_menu
ability_menu.parent_menu = main_menu
bank_value_menu.parent_menu = bank_menu
quests_menu.parent_menu = main_menu
requirements_menu.parent_menu = quest_menu
quest_description_menu.parent_menu = quest_menu
commands_menu.parent_menu = help_menu
mail_inbox_menu.parent_menu = mail_menu

class_info_detailed_skills.top_separator = ''
class_info_detailed_skills_info.top_separator = ''
class_info_detailed_lore.top_separator = ''
spend_skills.top_separator = ''
skill_info.top_separator = ''
skill_info_detailed.top_separator = ''
shop_buy_category_buy_menu.top_separator = ''
shop_buy_category_buy_real_menu.top_separator = ''
shop_info_category_info_menu.top_separator = ''
shop_info_category_info_detailed_menu.top_separator = ''
requirements_menu.top_separator = ''
quest_description_menu.top_separator = ''

_general_menu_swaps.append([change_class, class_menu])
_general_menu_swaps.append([ability_menu, main_menu])
_general_menu_swaps.append([skill_menu, main_menu])
_general_menu_swaps.append([spend_skills, main_menu])
_general_menu_swaps.append([reset_skills, main_menu])
_general_menu_swaps.append([skill_info, main_menu])
_general_menu_swaps.append([skill_info_detailed, main_menu])
_general_menu_swaps.append([shop_buy_category_menu, shop_menu])
_general_menu_swaps.append([shop_buy_category_buy_menu, shop_menu])
_general_menu_swaps.append([shop_buy_category_buy_real_menu, shop_menu])
_general_menu_swaps.append([shop_sell_menu, shop_menu])
_general_menu_swaps.append([shop_info_category_menu, shop_menu])
_general_menu_swaps.append([shop_info_category_info_menu, shop_menu])
_general_menu_swaps.append([shop_inventory_menu, shop_menu])
_general_menu_swaps.append([ascend_menu, ascension_menu])
_general_menu_swaps.append([vessel_menu, main2_menu])

_general_menu_refreshes.append(main_menu)
_general_menu_refreshes.append(main2_menu)
_general_menu_refreshes.append(class_menu)
_general_menu_refreshes.append(change_class)
_general_menu_refreshes.append(shop_menu)
_general_menu_refreshes.append(ascension_menu)

_item_general_menu_swaps.append(shop_buy_category_menu)
_item_general_menu_swaps.append(shop_buy_category_buy_menu)
_item_general_menu_swaps.append(shop_buy_category_buy_real_menu)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnClientDisconnect
def on_client_disconnect(index):
    _players.pop(index, None)


@OnLevelInit
def on_level_init(map_name):
    bank_menu.is_first_round = True
    bank_menu.is_allowed_to_withdraw = False


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('teamplay_round_start')
def teamplay_round_start(event):
    if bank_menu.is_first_round:
        bank_menu.is_first_round = False
    else:
        bank_menu.is_allowed_to_withdraw = True


@Event('player_spawn')
def player_spawn(event):
    # Cyclic import
    from ..players.entity import Player

    userid = event['userid']
    avsdplayer = Player.from_userid(userid)

    if avsdplayer.ready:
        if avsdplayer.player.team_index in (2, 3):
            _refresh(avsdplayer.index)
        else:
            _close(avsdplayer.index)


@Event('player_team')
def player_team(event):
    if not event['disconnect']:
        # Cyclic import
        from ..players.entity import Player

        userid = event['userid']
        avsdplayer = Player.from_userid(userid)

        if avsdplayer.ready:
            if event['team'] in (2, 3):
                _refresh(avsdplayer.index)
            else:
                _close(avsdplayer.index)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerItemPickup
def on_player_item_pickup(avsdplayer, item, quality):
    for menu in _item_general_menu_swaps:
        if menu.is_active_menu(avsdplayer.index):
            menu.close()

            shop_menu.send(avsdplayer.index)
            break


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if not avsdplayer._is_bot:
        if new is None:
            _close(avsdplayer.index)
        elif old is None:
            _refresh(avsdplayer.index)


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def _close(index):
    for menu, forward in _general_menu_swaps:
        if menu.is_active_menu(index):
            menu.close(index)

            forward.send(index)


def _refresh(index):
    for refresh in _general_menu_refreshes:
        if refresh.is_active_menu(index):
            queue = SimpleMenu.get_user_queue(index)
            queue._refresh()
            break
