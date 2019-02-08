# ../avsd/core/menus/select.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Menus
from menus import SimpleMenu
#   Messages
from messages import SayText2

# AvsD Imports
#   Config
from ..config import cfg_ascend_cash_requirement
from ..config import items_data
#   Constants
from ..constants import MAX_CASH
from ..constants import MailStatus
from ..constants import QuestSort
#   Items
from ..items import item_manager
#   Menus
from . import _players
from . import main_menu
from . import main2_menu
from . import class_menu
from . import change_class
from . import class_info
from . import class_info_angels
from . import class_info_demons
from . import class_info_detailed
from . import class_info_detailed_skills
from . import class_info_detailed_skills_info
from . import ability_menu
from . import skill_menu
from . import spend_skills
from . import reset_skills
from . import skill_info
from . import skill_info_detailed
from . import shop_menu
from . import shop_buy_category_menu
from . import shop_buy_category_buy_menu
from . import shop_buy_category_buy_real_menu
from . import shop_sell_menu
from . import shop_info_category_menu
from . import shop_info_category_info_menu
from . import shop_info_category_info_detailed_menu
from . import shop_inventory_menu
from . import bank_menu
from . import bank_value_menu
from . import quests_menu
from . import quest_menu
from . import ascension_menu
from . import ascend_menu
from . import ascension_info_menu
from . import vessel_menu
from . import help_menu
# from . import commands_menu
# from . import commands_menu1
# from . import commands_menu2
from . import mail_menu
from . import mail_inbox_menu
from . import mail_view_menu
from . import mail_view_settings_menu
from . import mail_view_settings_verify_menu
from . import item_zone_menu
#   Listeners
from ..listeners import OnPlayerReset
from ..listeners import OnPlayerUpgradeSkill
#   Modules
from ..modules.classes.manager import class_manager
#   Players
from ..players.entity import Player
#   Translations
from ..translations import chat_strings
from ..translations import items_strings
from ..translations import menu_strings
from ..translations import ui_strings


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
change_to_message = SayText2(chat_strings['change to'])
withdraw_first_message = SayText2(chat_strings['withdraw first'])
reset_skills_message = SayText2(chat_strings['reset skills'])
item_bought_message = SayText2(chat_strings['item bought'])
item_sold_message = SayText2(chat_strings['item sold'])
ascended_message = SayText2(chat_strings['ascended'])
gain_item = SayText2(chat_strings['gain item'])
gain_item_sold = SayText2(chat_strings['gain item sold'])


# ============================================================================
# >> SELECT CALLBACKS
# ============================================================================
@main_menu.register_select_callback
@main2_menu.register_select_callback
@class_menu.register_select_callback
@skill_menu.register_select_callback
@shop_menu.register_select_callback
@quest_menu.register_select_callback
@ascension_menu.register_select_callback
@ascension_info_menu.register_select_callback
@help_menu.register_select_callback
# @commands_menu.register_select_callback
# @commands_menu1.register_select_callback
# @commands_menu2.register_select_callback
@mail_menu.register_select_callback
@mail_view_menu.register_select_callback
def return_callback_select(menu, client, option):
    return option.value


@class_info.register_select_callback
def class_info_select(menu, client, option):
    if isinstance(option.value, tuple):
        _players[client]['class'] = option.value[0]

        return option.value[1]

    return option.value


@change_class.register_select_callback
def change_class_select(menu, client, option):
    if isinstance(option.value, str):
        name = option.value

        player = Player.from_index(client)

        player.current_class = name

        change_to_message.send(client, name=class_manager[name].settings.strings['name'])

    return option.value


@class_info_angels.register_select_callback
@class_info_demons.register_select_callback
def class_info_duo_select(menu, client, option):
    _players[client]['viewing'] = class_manager[option.value]

    return class_info_detailed


@class_info_detailed.register_select_callback
def class_info_detailed_select(menu, client, option):
    if option.choice_index == 7:
        return {'angels':class_info_angels, 'demons':class_info_demons}[_players[client]['class']]

    return option.value


@class_info_detailed_skills.register_select_callback
def class_info_detailed_skills_select(menu, client, option):
    _players[client]['skill'] = option.value

    return class_info_detailed_skills_info


@ability_menu.register_select_callback
def ability_menu_select(menu, client, option):
    avsdplayer = Player.from_index(client)

    if avsdplayer.player.dead:
        return menu

    active_class = avsdplayer.active_class

    if active_class is not None:
        active_class.skills[option.value]()

    queue = SimpleMenu.get_user_queue(client)

    if not queue:
        return menu


@spend_skills.register_select_callback
def spend_skills_select(menu, client, option):
    player = Player.from_index(client)
    skill = player.skills[option.value]

    OnPlayerUpgradeSkill.manager.notify(player, skill, skill.level, skill.level + 1)

    skill.level += 1
    player.point -= 1

    return menu


@reset_skills.register_select_callback
def reset_skills_select(menu, client, option):
    if option.choice_index == 3:
        player = Player.from_index(client)

        OnPlayerReset.manager.notify(player)

        player.cash -= cfg_ascend_cash_requirement.get_int()

        for skill in player.skills.values():
            player.point += skill.level

            skill.level = 0

        reset_skills_message.send(client)

        return skill_menu

    return option.value


@skill_info.register_select_callback
def skill_info_select(menu, client, option):
    _players[client]['skill'] = option.value

    return skill_info_detailed


@shop_buy_category_menu.register_select_callback
def shop_buy_category_menu_select(menu, client, option):
    _players[client]['category'] = option.value

    return shop_buy_category_buy_menu


@shop_buy_category_buy_menu.register_select_callback
def shop_buy_category_buy_menu_select(menu, client, option):
    _players[client]['item'] = option.value[0]
    _players[client]['cost'] = option.value[1]

    return shop_buy_category_buy_real_menu


@shop_buy_category_buy_real_menu.register_select_callback
def shop_buy_category_buy_real_menu_select(menu, client, option):
    avsdplayer = Player.from_index(client)
    player = avsdplayer.player
    name = _players[client]['item']

    quality, cost = option.value

    if avsdplayer.cash + player.cash < cost:
        return menu

    if avsdplayer.cash >= cost:
        avsdplayer.cash -= cost
    else:
        diff = cost - avsdplayer.cash

        avsdplayer.cash = 0

        player.cash -= diff

    avsdplayer.items.give(name, quality)

    # item_bought_message.send(client, name=items_strings.get('{0} name'.format(name)), value=cost)
    item_bought_message.send(client, name=items_strings['{0} name'.format(name)], value=cost)

    if avsdplayer.items.total >= avsdplayer.max_slots:
        return shop_menu

    return menu.parent_menu


@shop_sell_menu.register_select_callback
def shop_sell_menu_select(menu, client, option):
    avsdplayer = Player.from_index(client)
    player = avsdplayer.player
    item = option.value

    avsdplayer.items.destroy(item)
    # item.count -= 1

    name = item.name
    quality = item.quality

    # name, quality = option.value

    # for item in avsdplayer.items.valid:
    #     if item.name == name and item.quality == quality and not item.equipped:
    #         avsdplayer.items.destroy(item)
    #         break

    # gain = items_data['items'][name]['quality'][quality.name.lower()]['sell']
    gain = item_manager[name]['quality'][quality.name.lower()]['sell']

    if player.cash + gain <= MAX_CASH:
        player.cash += gain
    else:
        if player.cash == MAX_CASH:
            avsdplayer.cash += gain
        else:
            diff = MAX_CASH - player.cash

            player.cash = MAX_CASH

            avsdplayer.cash += gain - diff

    # item_sold_message.send(client, name=items_strings.get('{0} name'.format(name), name), value=gain)
    item_sold_message.send(client, name=items_strings['{0} name'.format(name)], value=gain)

    # if avsdplayer.items.valid:
    if avsdplayer.items.total_unequipped:
        return menu

    return menu.parent_menu


@shop_info_category_menu.register_select_callback
def shop_info_category_menu_select(menu, client, option):
    _players[client]['category'] = option.value

    return shop_info_category_info_menu


@shop_info_category_info_menu.register_select_callback
def shop_info_category_info_menu_select(menu, client, option):
    _players[client]['item'] = option.value

    return shop_info_category_info_detailed_menu


@shop_inventory_menu.register_select_callback
def shop_inventory_menu_select(menu, client, option):
    pass


@bank_menu.register_select_callback
def bank_menu_select(menu, client, option):
    if option.choice_index in (1, 2):
        if option.choice_index == 2 and not menu.is_allowed_to_withdraw:
            withdraw_first_message.send(client)
        else:
            player = Player.from_index(client)

            player.data['_bank_option'] = ['withdraw', 'deposit'][option.choice_index == 1]

            return bank_value_menu

    return option.value


@bank_value_menu.register_select_callback
def bank_value_menu_select(menu, client, option):
    avsdplayer = Player.from_index(client)
    player = avsdplayer.player

    if avsdplayer.data['_bank_option'] == 'deposit':
        player.cash -= option.value
        avsdplayer.cash += option.value
    else:
        player.cash += option.value
        avsdplayer.cash -= option.value

    return menu


@quests_menu.register_select_callback
def quests_menu_select(menu, client, option):
    player = Player.from_index(client)

    if option.value is None:
        try:
            quest_sort = QuestSort(player._quest_sort.value + 1)
        except ValueError:
            quest_sort = QuestSort.DEFAULT

        player._quest_sort = quest_sort

        return menu

    player.data['_viewing_quest'] = option.value

    return quest_menu


@ascend_menu.register_select_callback
def ascend_menu_select(menu, client, option):
    if option.choice_index == 4:
        Player.from_index(client).ascend += 1

        ascended_message.send(client)

    return option.value


@vessel_menu.register_select_callback
def vessel_menu_select(menu, client, option):
    if isinstance(option.value, int):
        player = Player.from_index(client)
        team = player.player.team_index

        attr = '_current_{0}_vessel'.format('angel' if team == 3 else 'demon')

        setattr(player, attr, option.value)

        return menu

    return option.value


@mail_inbox_menu.register_select_callback
def mail_inbox_menu_select(menu, client, option):
    _players[client]['mail'] = option.value

    if option.value['status'] == MailStatus.NEW:
        option.value['status'] = MailStatus.READ

    return mail_view_menu


@mail_view_settings_menu.register_select_callback
def mail_view_settings_menu_select(menu, client, option):
    if option.choice_index == 1:
        player = Player.from_index(client)
        mail = _players[client]['mail']

        for reward in mail['rewards']:
            # player.hudinfo.add_message(f'You have gained {reward["value"]} {reward["name"]}!')
            player.hudinfo.add_message(ui_strings['ui gained'], value=reward['value'], name=reward['name'])
            setattr(player, reward['name'], getattr(player, reward['name']) + reward['value'])

        mail['status'] = MailStatus.REWARDED

        return menu
    elif option.choice_index == 2:
        pass

    return option.value


@mail_view_settings_verify_menu.register_select_callback
def mail_view_settings_verify_menu_select(menu, client, option):
    if option.choice_index == 1:
        _players[client]['mail']['status'] = MailStatus.DELETE

        return mail_inbox_menu

    return mail_view_settings_menu


@item_zone_menu.register_select_callback
def item_zone_menu_select(menu, client, option):
    player = Player.from_index(client)

    if option.choice_index == 1:
        if player.slot < items_data['inventory']['max']:
            if player.cash >= items_data['inventory']['cost']:
                player.slot += 1

                item = player.data['_items'][0]
                item.remove()

                player.items.give(item.name, item.quality)

                gain_item.send(player.index, quality=menu_strings[item.quality.name.lower()], name=items_strings.get('{0} name'.format(item.name), item.name))
    elif option.choice_index == 2:
        item = player.data['_items'][0]
        item.remove()

        value = item_manager[item.name]['quality'][item.quality.name.lower()]['sell']
        player.cash += value

        gain_item_sold.send(player.index, cash=value, quality=menu_strings[item.quality.name.lower()], name=items_strings.get('{0} name'.format(item.name), item.name))
    elif option.choice_index == 3:
        player.data['_items'][0].remove()

    if '_items' in player.data:
        return menu
