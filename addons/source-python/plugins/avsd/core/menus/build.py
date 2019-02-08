# ../avsd/core/menus/build.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
from collections import defaultdict
#   Copy
from copy import deepcopy
#   Datetime
from datetime import datetime
from datetime import timedelta
#   Textwrap
from textwrap import wrap

# Source.Python Imports
#   Menus
from menus import PagedOption
from menus import Text
#   Players
from players.helpers import get_client_language

# AvsD Imports
#   Config
from ..config import cfg_ascend_cash_requirement
from ..config import experiences_data
from ..config import items_data
#   Constants
from ..constants import DIFFICULTY_CHAR
from ..constants import DIFFICULTY_CHAR_EMPTY
from ..constants import MAX_CASH
from ..constants import MENU_MISSING_TEXT
from ..constants import ItemQuality
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
from . import class_info_detailed
from . import class_info_detailed_skills
from . import class_info_detailed_skills_info
from . import class_info_detailed_lore
from . import ability_menu
from . import spend_skills
from . import reset_skills
from . import skill_info
from . import skill_info_detailed
from . import shop_menu
from . import shop_buy_category_menu
from . import shop_buy_category_buy_menu
from . import shop_buy_category_buy_real_menu
from . import shop_sell_menu
from . import shop_info_category_info_menu
from . import shop_info_category_info_detailed_menu
from . import shop_inventory_menu
from . import bank_menu
from . import bank_value_menu
from . import quests_menu
from . import quest_menu
from . import requirements_menu
from . import quest_description_menu
from . import ascension_menu
from . import ascend_menu
from . import vessel_menu
from . import mail_menu
from . import mail_inbox_menu
from . import mail_view_menu
from . import mail_view_settings_menu
from . import item_zone_menu
#   Modules
from ..modules.classes.manager import class_manager
#   Players
from ..players.entity import Player
#   Quests
from ..quests import quest_manager
#   Translations
from ..translations import items_strings
from ..translations import menu_strings


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
MAX_LEVEL = max([int(x) for x in experiences_data['required']]) + 1


# ============================================================================
# >> BUILD CALLBACKS
# ============================================================================
@main_menu.register_build_callback
def main_menu_build(menu, client):
    active_class = Player.from_index(client).active_class

    menu[3].selectable = menu[3].highlight = active_class is not None
    menu[4].selectable = menu[4].highlight = active_class is not None and active_class.settings._abilities


@main2_menu.register_build_callback
def main2_menu_build(menu, client):
    active_class = Player.from_index(client).active_class

    menu[4].selectable = menu[4].highlight = active_class is not None


@class_menu.register_build_callback
def class_menu_build(menu, client):
    menu[2].selectable = menu[2].highlight = Player.from_index(client).active_class is not None


@change_class.register_build_callback
def change_class_build(menu, client):
    player = Player.from_index(client)
    team = player.player.team_index
    current_class = player.current_class

    class_type = 'angels' if team == 3 else 'demons'

    menu.title.tokens['type'] = menu_strings[class_type]

    menu.clear()

    for name in player.allowed_classes:
        settings = class_manager[name].settings

        # option = PagedOption(settings.strings.get('name', MENU_MISSING_TEXT), name)
        option = PagedOption(settings.strings['name'], name)
        option.selectable = option.highlight = name != current_class

        menu.append(option)


@class_info_detailed.register_build_callback
def class_info_detailed_build(menu, client):
    settings = _players[client]['viewing'].settings
    difficulty = settings.config['difficulty']

    # menu[0].text.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    # menu[1].text.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    menu[1].text.tokens['name'] = settings.strings['name']
    # menu[2].text.tokens['description'] = settings.strings.get('description', MENU_MISSING_TEXT)
    menu[2].text.tokens['description'] = settings.strings['description']
    # menu[3].text.tokens['difficulty'] = difficulty * DIFFICULTY_CHAR + ('' if difficulty == 5 else (5 - difficulty) * DIFFICULTY_CHAR_EMPTY)
    menu[3].text.tokens['difficulty'] = difficulty * DIFFICULTY_CHAR + ('' if difficulty == 5 else (5 - difficulty) * DIFFICULTY_CHAR_EMPTY)
    # menu[4].text.tokens['role'] = settings.strings.get('role', MENU_MISSING_TEXT)
    menu[4].text.tokens['role'] = settings.strings['role']


@class_info_detailed_skills.register_build_callback
def class_info_detailed_skills_build(menu, client):
    settings = _players[client]['viewing'].settings

    # menu.title.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    menu.description.tokens['name'] = settings.strings['name']

    menu.clear()

    for skill in settings.config['skills']:
        # menu.append(PagedOption(settings.strings.get(skill.lower(), MENU_MISSING_TEXT), skill))
        # menu.append(PagedOption(settings.strings[skill.lower()], skill))
        menu.append(PagedOption(settings.strings[skill], skill))


@class_info_detailed_skills_info.register_build_callback
def class_info_detailed_skills_info_build(menu, client):
    settings = _players[client]['viewing'].settings
    skill = _players[client]['skill']

    # menu.title.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings.get(skill.lower(), MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings[skill.lower()]
    menu.description.tokens['name'] = settings.strings[skill]

    menu.clear()

    # info = settings.strings.get('{0} description'.format(skill.lower()), MENU_MISSING_TEXT)
    # info = settings.strings['{0} description'.format(skill.lower())]
    info = settings.strings['{0} description'.format(skill)]

    # if info != MENU_MISSING_TEXT:
    info = info.get_string(get_client_language(client))

    for text in wrap(info, 30):
        menu.append(text)


@class_info_detailed_lore.register_build_callback
def class_info_detailed_lore_build(menu, client):
    settings = _players[client]['viewing'].settings

    # menu.title.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    menu.description.tokens['name'] = settings.strings['name']

    menu.clear()

    # info = settings.strings.get('lore', MENU_MISSING_TEXT)
    info = settings.strings['lore']

    # if info != MENU_MISSING_TEXT:
    info = info.get_string(get_client_language(client))

    for text in wrap(info, 30):
        menu.append(text)


@ability_menu.register_build_callback
def ability_menu_build(menu, client):
    avsdplayer = Player.from_index(client)
    active_class = avsdplayer.active_class
    settings = active_class.settings

    menu.clear()

    # menu.title.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)

    for name in sorted(settings._abilities, key=lambda x: settings._abilities[x]._index):
        # option = PagedOption(settings.strings.get(name.lower(), MENU_MISSING_TEXT), name)
        # option = PagedOption(settings.strings[name.lower()], name)
        option = PagedOption(settings.strings[name], name)
        option.highlight = option.selectable = active_class.skills[name].level

        menu.append(option)


@spend_skills.register_build_callback
def spend_skills_build(menu, client):
    active_class = Player.from_index(client).active_class

    # menu.title.tokens['points'] = active_class.point
    menu.description.tokens['points'] = active_class.point

    menu.clear()

    settings = active_class.settings

    for skill in settings.config['skills']:
        # option = PagedOption(settings.strings.get(skill.lower(), MENU_MISSING_TEXT), skill)
        # option = PagedOption(settings.strings[skill.lower()], skill)
        option = PagedOption(settings.strings[skill], skill)

        menu.append(option)

        if option.value == MENU_MISSING_TEXT:
            continue

        skill = active_class.skills[option.value]

        option.selectable = option.highlight = skill.enabled and bool(active_class.point) and skill.level < skill.max

        if skill.enabled:
            text = deepcopy(menu_strings['spend skills line 1'])
            text.tokens['name'] = option.text
            text.tokens['level'] = skill.level
            text.tokens['max'] = skill.max

            option.text = text


@skill_info.register_build_callback
def skill_info_build(menu, client):
    active_class = Player.from_index(client).active_class

    menu.clear()

    settings = active_class.settings

    # menu.title.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    menu.description.tokens['name'] = settings.strings['name']

    for skill in settings.config['skills']:
        # menu.append(PagedOption(settings.strings.get(skill.lower(), MENU_MISSING_TEXT), skill))
        # menu.append(PagedOption(settings.strings[skill.lower()], skill))
        menu.append(PagedOption(settings.strings[skill], skill))


@reset_skills.register_build_callback
def reset_skills_build(menu, client):
    player = Player.from_index(client)
    active_class = player.active_class

    value = cfg_ascend_cash_requirement.get_int()

    menu[2].text.tokens['cash'] = '{0:,}'.format(value).replace(',', '.')
    # menu[3].text.tokens['name'] = active_class.settings.strings.get('name', MENU_MISSING_TEXT)
    menu[3].text.tokens['name'] = active_class.settings.strings['name']
    menu[4].selectable = menu[4].highlight = player.cash >= value


@skill_info_detailed.register_build_callback
def skill_info_detailed_build(menu, client):
    active_class = Player.from_index(client).active_class

    menu.clear()

    settings = active_class.settings
    skill = _players[client]['skill']

    # menu.title.tokens['name'] = settings.strings.get('name', MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings.get(skill.lower(), MENU_MISSING_TEXT)
    # menu.description.tokens['name'] = settings.strings[skill.lower()]
    menu.description.tokens['name'] = settings.strings[skill]

    # info = settings.strings.get('{0} description'.format(skill.lower()), MENU_MISSING_TEXT)
    # info = settings.strings['{0} description'.format(skill.lower())]
    info = settings.strings['{0} description'.format(skill)]

    # if info != MENU_MISSING_TEXT:
    info = info.get_string(get_client_language(client))

    for text in wrap(info, 30):
        menu.append(text)


@shop_menu.register_build_callback
def shop_menu_build(menu, client):
    active_class = Player.from_index(client).active_class
    allow = active_class is not None

    menu[2].selectable = menu[2].highlight = allow and active_class.items.total_unequipped < active_class.max_slots
    menu[3].selectable = menu[3].highlight = allow and [item for item in active_class.items.valid if not item.equipped]
    menu[5].selectable = menu[5].highlight = allow


@shop_buy_category_menu.register_build_callback
def shop_buy_category_menu_build(menu, client):
    player = Player.from_index(client)
    active_class = player.active_class
    current_class = player.current_class
    free_space = active_class.items.total_unequipped < active_class.max_slots

    # menu.title.tokens['cash'] = player.cash + player.player.cash

    for option in menu:
        # option.selectable = option.highlight = bool(option.class_items[current_class] + option.class_items['all'])
        option.selectable = option.highlight = bool(list(item_manager.get_items_by_class_and_category(current_class, option.value))) and free_space

        # # TODO: Remove found_items after testing
        # if option.found_items:
        #     for item in items_data['items'].values():
        #         if item['category'] == option.value:
        #             if item['allow'] == current_class:
        #                 option.selectable = option.highlight = True

        #                 break
        #     else:
        #         option.selectable = option.highlight = False


@shop_buy_category_buy_menu.register_build_callback
def shop_buy_category_buy_menu_build(menu, client):
    player = Player.from_index(client)
    active_class = player.active_class
    cash = player.player.cash + player.cash
    current_class = player.current_class
    free_space = active_class.items.total_unequipped < active_class.max_slots

    menu.clear()

    # menu.title.tokens['cash'] = cash
    menu.description.tokens['category'] = menu_strings[_players[client]['category']]

    # for category in menu:
    #     if category.value == _players[client]['category']:
    #         items = items_data['items']

    #         for name in set(category.class_items[current_class] + category.class_items['all']):
    for name in item_manager.get_items_by_class_and_category(current_class, _players[client]['category']):
        cost = {}
        item = item_manager[name]

        for x in ItemQuality:
            quality = x.name.lower()

            if quality in item['quality']:
                price = item['quality'][quality].get('buy')

                if price is not None:
                    cost[x] = price

        if cost:
            # option = PagedOption(items_strings.get('{0} name'.format(name), name), [name, cost])
            option = PagedOption(items_strings['{0} name'.format(name)], [name, cost])
            option.selectable = option.highlight = any([cash >= price for price in cost.values()]) and free_space

            menu.append(option)

            # break

    # for name, item in items_data['items'].items():
    #     if item['category'] == _players[client]['category']:
    #         if item['allow'] == current_class or current_class in item['allow']:
    #             cost = {}

    #             for x in ItemQuality:
    #                 quality = x.name.lower()

    #                 if quality in item['quality']:
    #                     price = item['quality'][quality].get('buy')

    #                     if price is not None:
    #                         cost[x] = price

    #             if cost:
    #                 option = PagedOption(items_strings['{0} name'.format(name)], [name, cost])
    #                 option.selectable = option.highlight = any([cash >= price for price in cost.values()])

    #                 menu.append(option)


@shop_buy_category_buy_real_menu.register_build_callback
def shop_buy_category_buy_real_menu_build(menu, client):
    player = Player.from_index(client)
    cash = player.player.cash + player.cash
    active_class = player.active_class
    free_space = active_class.items.total_unequipped < active_class.max_slots

    menu.clear()

    quality_count = defaultdict(int)

    for item in [item for item in player.items.valid if item.name == _players[client]['item']]:
        # print(item.name, item.quality, item.count)
        quality_count[item.quality] = item.count

    # menu.title.tokens['cash'] = cash
    # menu.description.tokens['name'] = items_strings.get('{0} name'.format(_players[client]['item']), _players[client]['item'])
    menu.description.tokens['name'] = items_strings['{0} name'.format(_players[client]['item'])]

    for quality in ItemQuality:
        if quality in _players[client]['cost']:
            cost = _players[client]['cost'][quality]

            option = PagedOption(deepcopy(menu_strings['shop buy category buy real menu line']), [quality, cost])

            option.text.tokens['quality'] = menu_strings[quality.name.lower()]
            option.text.tokens['cost'] = cost
            option.text.tokens['count'] = quality_count[quality]

            option.selectable = option.highlight = cash >= cost and free_space

            menu.append(option)
        else:
            menu.append(' ')


@shop_sell_menu.register_build_callback
def shop_sell_menu_build(menu, client):
    player = Player.from_index(client)

    menu.clear()

    # menu.title.tokens['cash'] = player.player.cash + player.cash

    # items_count = defaultdict(lambda: defaultdict(int))

    # for item in player.items.valid:
    #     if not item.equipped:
    #         items_count[item.name][item.quality] += 1

    # for name in items_count:
    #    for quality, count in items_count[name].items():

    for item in player.items.valid:
        if item.count == 1 and item.equipped:
            continue

        name = item.name
        quality = item.quality

        option = PagedOption(deepcopy(menu_strings['shop sell menu line']), item)

        option.text.tokens['quality'] = menu_strings[quality.name.lower()]
        # option.text.tokens['name'] = items_strings.get('{0} name'.format(name), name)
        option.text.tokens['name'] = items_strings['{0} name'.format(name)]
        # option.text.tokens['gain'] = items_data['items'][name]['quality'][quality.name.lower()]['sell']
        option.text.tokens['gain'] = item_manager[name]['quality'][quality.name.lower()]['sell']
        # option.text.tokens['count'] = items_count[name][quality]
        option.text.tokens['count'] = item.count - (1 if item.equipped else 0)

        menu.append(option)


@shop_info_category_info_menu.register_build_callback
def shop_info_category_info_menu_build(menu, client):
    menu.clear()

    # menu.title.tokens['category'] = menu_strings[_players[client]['category']]
    menu.description.tokens['category'] = menu_strings[_players[client]['category']]

    # for name, item in items_data['items'].items():
    #     if item['category'] == _players[client]['category']:
    for name in item_manager.get_items_by_category(_players[client]['category']):
        # menu.append(PagedOption(items_strings.get('{0} name'.format(name), name), name))
        menu.append(PagedOption(items_strings['{0} name'.format(name)], name))


@shop_info_category_info_detailed_menu.register_build_callback
def shop_info_category_info_detailed_menu_build(menu, client):
    menu.clear()

    item = _players[client]['item']

    # menu.title.tokens['name'] = items_strings.get('{0} name'.format(item), item)
    # menu.description.tokens['name'] = items_strings.get('{0} name'.format(item), item)
    menu.description.tokens['name'] = items_strings['{0} name'.format(item)]

    # info = items_strings.get('{0} desc'.format(item), MENU_MISSING_TEXT)
    info = items_strings['{0} desc'.format(item)]

    # if info != MENU_MISSING_TEXT:
    info = info.get_string(get_client_language(client))

    for text in wrap(info, 30):
        menu.append(text)


@shop_inventory_menu.register_build_callback
def shop_inventory_menu_build(menu, client):
    player = Player.from_index(client)

    menu.clear()

    # menu.title.tokens['count'] = len(player.items.valid)
    menu.title.tokens['count'] = player.items.total
    menu.title.tokens['total'] = player.max_slots

    # items_count = defaultdict(lambda: defaultdict(int))

    # for item in player.items.valid:
    #     items_count[item.name][item.quality] += 1

    # for name in items_count:
    #     for quality, count in items_count[name].items():

    for item in player.items.valid:
        name = item.name
        quality = item.quality

        option = PagedOption(deepcopy(menu_strings['shop inventory menu line' + (' equipped' if item.equipped else '')]))

        option.selectable = False

        option.text.tokens['quality'] = menu_strings[quality.name.lower()]
        # option.text.tokens['name'] = items_strings.get('{0} name'.format(name), name)
        option.text.tokens['name'] = items_strings['{0} name'.format(name)]
        # option.text.tokens['count'] = items_count[name][quality]
        option.text.tokens['count'] = item.count

        menu.append(option)


@bank_menu.register_build_callback
def bank_menu_build(menu, client):
    # avsdplayer = Player.from_index(client)

    # menu[0].text.tokens['cash'] = avsdplayer.cash
    menu[3].selectable = menu[3].highlight = menu.is_allowed_to_withdraw


@bank_value_menu.register_build_callback
def bank_value_menu_build(menu, client):
    avsdplayer = Player.from_index(client)
    player = avsdplayer.player

    # menu.title.tokens['cash'] = avsdplayer.cash

    for option in menu:
        if avsdplayer.data['_bank_option'] == 'deposit':
            option.selectable = option.highlight = option.value <= player.cash
        else:
            option.selectable = option.highlight = option.value <= avsdplayer.cash and (player.cash + option.value) <= MAX_CASH


@quests_menu.register_build_callback
def quests_menu_build(menu, client):
    menu.clear()

    player = Player.from_index(client)

    if player._quest_sort == QuestSort.DEFAULT:
        data = quest_manager.values()
    elif player._quest_sort in (QuestSort.NAME_ASC, QuestSort.NAME_DESC):
        language = get_client_language(client)

        data = sorted(quest_manager.values(), key=lambda x: x.strings[x._name].get_string(language), reverse=player._quest_sort == QuestSort.NAME_DESC)
        # try:
        #     data = sorted(quest_manager.values(), key=lambda x: x.strings[x._name].get_string(language), reverse=player._quest_sort == QuestSort.NAME_DESC)
        # except AttributeError:
        #     data = sorted(quest_manager.values(), key=lambda x: x.strings[x._name].get_string(language) if hasattr(x.strings[x._name], 'get_string') else x.strings[x._name], reverse=player._quest_sort == QuestSort.NAME_DESC)
    elif player._quest_sort in (QuestSort.PROGRESS_ASC, QuestSort.PROGRESS_DESC):
        data = sorted(quest_manager.values(), key=lambda x: x.get_progress_percentage(player, False), reverse=player._quest_sort == QuestSort.PROGRESS_ASC)

    menu.append(PagedOption(menu_strings['quests menu sort {0}'.format(player._quest_sort.value)]))

    for quest in data:
        text = deepcopy(menu_strings['quests menu line'])
        text.tokens['name'] = quest.strings[quest._name]
        text.tokens['percentage'] = quest.get_progress_percentage(player)

        menu.append(PagedOption(text, quest.name))


@quest_menu.register_build_callback
def quest_menu_build(menu, client):
    player = Player.from_index(client)
    quest = quest_manager[player.data['_viewing_quest']]

    # menu[0].text.tokens['name'] = quest.strings[quest._name]
    menu[1].text.tokens['name'] = quest.strings[quest._name]
    menu[4].text.tokens['percentage'] = quest.get_progress_percentage(player)

    if quest._job is not None:
        buffer = ''
        delta = quest._job.next_run

        if not isinstance(delta, timedelta):
            delta -= datetime.now()

        if delta.days >= 7:
            buffer += str(delta.days // 7) + 'w '

        if delta.days % 7:
            buffer += str(delta.days % 7) + 'd '

        if delta.seconds >= 3600:
            buffer += '{:02d}:'.format(delta.seconds // 3600)
        else:
            buffer += '00:'

        if delta.seconds >= 60:
            buffer += '{:02d}:'.format(delta.seconds % 3600 // 60)
        else:
            buffer += '00:'

        if delta.seconds % 60:
            buffer += '{:02d}'.format(delta.seconds % 60)
        else:
            buffer += '00'
    else:
        buffer = menu_strings['quest menu never']

    menu[5].text.tokens['time'] = buffer


@requirements_menu.register_build_callback
def requirements_menu_build(menu, client):
    menu.clear()

    player = Player.from_index(client)
    quest = quest_manager[player.data['_viewing_quest']]

    # menu.title.tokens['name'] = quest.strings[quest._name]
    menu.description.tokens['name'] = quest.strings[quest._name]

    for requirement in quest.requirements:
        progress = quest.get_progress_percentage(player)

        text = deepcopy(quest.strings['{0} description'.format(requirement.name)])

        try:
            text.tokens['value'] = requirement.get_progress(player)
            text.tokens['count'] = requirement.count
            text.tokens['percentage'] = progress

            menu.append(PagedOption(text, highlight=progress == 100, selectable=False))
        except AttributeError:
            menu.append(Text(text))


@quest_description_menu.register_build_callback
def quest_description_menu_build(menu, client):
    menu.clear()

    player = Player.from_index(client)
    quest = quest_manager[player.data['_viewing_quest']]

    # menu.title.tokens['name'] = quest.strings[quest._name]
    menu.description.tokens['name'] = quest.strings[quest._name]

    info = quest.strings[quest._description]

    if info != MENU_MISSING_TEXT:
        if quest.format is None:
            info = info.get_string(get_client_language(client))
        else:
            info = info.get_string(get_client_language(client), **quest.get_format())

    for text in wrap(info, 30):
        menu.append(text)


@ascension_menu.register_build_callback
def ascension_menu_build(menu, client):
    player = Player.from_index(client)

    menu[2].selectable = menu[2].highlight = player.current_class is not None


@ascend_menu.register_build_callback
def ascend_menu_build(menu, client):
    active_class = Player.from_index(client).active_class

    menu[3].text.tokens['name'] = active_class.settings.strings.get('name', MENU_MISSING_TEXT)
    menu[5].selectable = menu[5].highlight = active_class.level == MAX_LEVEL


@vessel_menu.register_build_callback
def vessel_menu_build(menu, client):
    player = Player.from_index(client)
    team = player.player.team_index

    attr = '_current_{0}_vessel'.format('angel' if team == 3 else 'demon')

    value = getattr(player, attr)

    for option in menu[2:4]:
        option.selectable = option.highlight = option.value != value


@mail_menu.register_build_callback
def mail_menu_build(menu, client):
    player = Player.from_index(client)

    if player.inbox.valid:
        menu[2].text = menu_strings['mail menu line 1 multiple']
        menu[2].text.tokens['value'] = len(player.inbox.valid)

        menu[2].selectable = menu[2].highlight = True
    else:
        menu[2].text = menu_strings['mail menu line 1']

        menu[2].selectable = menu[2].highlight = True


@mail_inbox_menu.register_build_callback
def mail_inbox_menu_build(menu, client):
    menu.clear()

    player = Player.from_index(client)

    for mail in player.inbox.valid:
        # if mail.message.startswith('_quest_complete_'):
        if mail['message'].startswith('_quest_complete_'):
            menu.append(PagedOption(deepcopy(menu_strings[f'mail inbox menu quest {mail["status"].name.lower()}']), mail))

        # text = deepcopy(quest.strings['{0} description'.format(requirement.name)])

        # try:
        #     text.tokens['value'] = requirement.get_progress(player)
        #     text.tokens['count'] = requirement.count
        #     text.tokens['percentage'] = progress

        #     menu.append(PagedOption(text, highlight=progress == 100, selectable=False))
            # quest = mail['message'].split('_quest_complete_')[1]


@mail_view_menu.register_build_callback
def mail_view_menu_build(menu, client):
    menu[0] = menu[1] = menu[2] = menu[3] = menu[4] = menu[5] = menu[6] = Text(' ')

    mail = _players[client]['mail']

    if mail['message'].startswith('_quest_complete_'):
        menu[0] = Text(menu_strings['mail view menu quest line 1'])
        menu[1] = Text(menu_strings['mail view menu quest line 2'])

        quest = mail['message'].split('_quest_complete_')[1]
        quest = quest_manager[quest]

        menu[0].text.tokens['name'] = quest.strings[quest._name]

        for i, reward in enumerate(mail['rewards'], 2):
            # menu[i] = Text(f'{reward["name"]}: {reward["value"]}')
            menu[i] = Text(menu_strings[f'mail view menu quest reward {reward["name"]}'])
            menu[i].text.tokens['value'] = reward['value']


@mail_view_settings_menu.register_build_callback
def mail_view_settings_menu_build(menu, client):
    mail = _players[client]['mail']

    menu[2].selectable = menu[2].highlight = bool(mail['rewards']) and mail['status'] != MailStatus.REWARDED


@item_zone_menu.register_build_callback
def item_zone_menu_build(menu, client):
    player = Player.from_index(client)
    items = player.data['_items']

    if len(items) > 1:
        menu[1] = Text(menu_strings['item zone menu line 1 multiple'])
        menu[1].text.tokens['count'] = len(items)
    else:
        menu[1] = Text(menu_strings['item zone menu line 1'])

    name = items[0].name
    quality = items[0].quality.name.lower()

    menu[1].text.tokens['quality'] = menu_strings[quality]
    # menu[1].text.tokens['name'] = items_strings.get('{0} name'.format(name), name)
    menu[1].text.tokens['name'] = items_strings['{0} name'.format(name)]
    menu[3].text.tokens['value'] = item_manager[name]['quality'][quality]['sell']

    menu[2].selectable = menu[2].highlight = player.slot < items_data['inventory']['max'] and player.cash >= items_data['inventory']['cost']
