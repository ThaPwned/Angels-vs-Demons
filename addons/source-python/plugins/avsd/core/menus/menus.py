# ../avsd/core/menus/menus.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
# from collections import defaultdict

# Source.Python Imports
#   Menus
from menus import PagedOption
from menus import SimpleOption
from menus import Text

# AvsD Imports
# #   Config
# from ..config import items_data
#   Constants
from ..constants import MENU_MISSING_TEXT
#   Items
from ..items import item_manager
#   Listeners
from ..listeners import OnPluginClassLoad
from ..listeners import OnPluginClassUnload
#   Menus
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
from . import class_info_detailed_lore
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
from . import requirements_menu
from . import quest_description_menu
from . import ascension_menu
from . import ascend_menu
from . import ascension_info_menu
from . import vessel_menu
from . import help_menu
from . import commands_menu
# from . import commands_menu1
# from . import commands_menu2
from . import mail_menu
from . import mail_inbox_menu
from . import mail_view_menu
from . import mail_view_settings_menu
from . import mail_view_settings_verify_menu
from . import item_zone_menu
from .build import _players  # Just to load it
from .select import _players  # Just to load it
#   Modules
# from ..modules.classes.manager import class_manager
#   Translations
from ..translations import menu_strings


# ============================================================================
# >> MENU TITLES
# ============================================================================
change_class.title = menu_strings['change class title']
class_info_angels.title = menu_strings['angels info title']
class_info_demons.title = menu_strings['demons info title']
class_info_detailed_skills.title = menu_strings['class info detailed skills title']
class_info_detailed_skills.description = menu_strings['class info detailed skills description']
class_info_detailed_skills_info.title = menu_strings['class info detailed skills info title']
class_info_detailed_skills_info.description = menu_strings['class info detailed skills info description']
class_info_detailed_lore.title = menu_strings['class info detailed lore title']
class_info_detailed_lore.description = menu_strings['class info detailed lore description']
spend_skills.title = menu_strings['spend skills title']
spend_skills.description = menu_strings['spend skills description']
skill_info.title = menu_strings['skill info title']
skill_info.description = menu_strings['skill info description']
skill_info_detailed.title = menu_strings['skill info detailed title']
skill_info_detailed.description = menu_strings['skill info detailed description']
ability_menu.title = menu_strings['ability menu title']
shop_buy_category_menu.title = menu_strings['shop buy category menu title']
shop_buy_category_buy_menu.title = menu_strings['shop buy category buy menu title']
shop_buy_category_buy_menu.description = menu_strings['shop buy category buy menu description']
shop_buy_category_buy_real_menu.title = menu_strings['shop buy category buy real menu title']
shop_buy_category_buy_real_menu.description = menu_strings['shop buy category buy real menu description']
shop_sell_menu.title = menu_strings['shop sell menu title']
shop_info_category_menu.title = menu_strings['shop info category menu title']
shop_info_category_info_menu.title = menu_strings['shop info category info menu title']
shop_info_category_info_menu.description = menu_strings['shop info category info menu description']
shop_info_category_info_detailed_menu.title = menu_strings['shop info category info detailed menu title']
shop_info_category_info_detailed_menu.description = menu_strings['shop info category info detailed menu description']
shop_inventory_menu.title = menu_strings['shop inventory menu title']
bank_value_menu.title = menu_strings['bank value menu title']
quests_menu.title = menu_strings['quests menu title']
requirements_menu.title = menu_strings['requirements menu title']
requirements_menu.description = menu_strings['requirements menu description']
quest_description_menu.title = menu_strings['quest description menu title']
quest_description_menu.description = menu_strings['quest description menu description']
commands_menu.title = menu_strings['commands menu title']
mail_inbox_menu.title = menu_strings['mail inbox menu title']

for i in [1, 10, 100, 1000, 10000, 100000, 1000000]:
    bank_value_menu.append(PagedOption(i, i))


# ============================================================================
# >> MENU FILLER
# ============================================================================
main_menu.extend(
    [
        Text(menu_strings['main menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['main menu line 1'], class_menu),
        SimpleOption(2, menu_strings['main menu line 2'], skill_menu),
        SimpleOption(3, menu_strings['main menu line 3'], ability_menu),
        SimpleOption(4, menu_strings['main menu line 4'], shop_menu),
        SimpleOption(5, menu_strings['main menu line 5'], bank_menu),
        SimpleOption(6, menu_strings['main menu line 6'], quests_menu),
        Text(' '),
        SimpleOption(8, menu_strings['next'], main2_menu),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

main2_menu.extend(
    [
        Text(menu_strings['main menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['main menu line 7'], help_menu),
        SimpleOption(2, menu_strings['main menu line 8'], ascension_menu),
        SimpleOption(3, menu_strings['main menu line 9'], vessel_menu),
        # Text(' '),
        SimpleOption(4, menu_strings['main menu line 10'], mail_menu),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

class_menu.extend(
    [
        Text(menu_strings['class menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['class menu line 1'], change_class),
        SimpleOption(2, menu_strings['class menu line 2'], class_info),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

class_info.extend(
    [
        Text(menu_strings['class info title']),
        Text(' '),
        SimpleOption(1, menu_strings['angels'], ('angels', class_info_angels)),
        SimpleOption(2, menu_strings['demons'], ('demons', class_info_demons)),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], class_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

# for class_ in class_manager.values():
#     print(class_.name, class_.settings.config['class'])
#     if class_.settings.config['class'] == 'demon':
#         class_info_demons.append(PagedOption(class_.settings.strings.get('name', MENU_MISSING_TEXT), class_.settings.name))
#     else:
#         class_info_angels.append(PagedOption(class_.settings.strings.get('name', MENU_MISSING_TEXT), class_.settings.name))

class_info_detailed.extend(
    [
        Text(menu_strings['class info detailed title']),
        # Text(' '),
        Text(menu_strings['class info detailed description']),
        Text(menu_strings['class info detailed line 1']),
        Text(menu_strings['class info detailed line 2']),
        Text(menu_strings['class info detailed line 3']),
        Text(' '),
        SimpleOption(1, menu_strings['class info detailed line 4'], class_info_detailed_skills),
        SimpleOption(2, menu_strings['class info detailed line 5'], class_info_detailed_lore),
        SimpleOption(7, menu_strings['back']),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

skill_menu.extend(
    [
        Text(menu_strings['skill menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['skill menu line 1'], spend_skills),
        SimpleOption(2, menu_strings['skill menu line 2'], reset_skills),
        SimpleOption(3, menu_strings['skill menu line 3'], skill_info),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

reset_skills.extend(
    [
        Text(menu_strings['reset skills title']),
        Text(' '),
        Text(menu_strings['reset skills line 1']),
        Text(menu_strings['reset skills line 2']),
        SimpleOption(3, menu_strings['yes']),
        SimpleOption(4, menu_strings['no'], skill_menu),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], skill_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

# skill_info_detailed.extend(
#     [
#         Text(menu_strings['skill info detailed title']),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         SimpleOption(7, menu_strings['back'], skill_info),
#         Text(' '),
#         SimpleOption(9, menu_strings['close'], highlight=False),
#     ]
# )

shop_menu.extend(
    [
        Text(menu_strings['shop menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['shop menu line 1'], shop_buy_category_menu),
        SimpleOption(2, menu_strings['shop menu line 2'], shop_sell_menu),
        SimpleOption(3, menu_strings['shop menu line 3'], shop_info_category_menu),
        SimpleOption(4, menu_strings['shop menu line 4'], shop_inventory_menu),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

# shop_buy_category_menu.extend(
#     [
#         PagedOption(menu_strings[x], x, False, False) for x in items_data['categories']
#     ]
# )

# shop_buy_category_buy_real_menu.extend(
#     [
#         Text(menu_strings['shop buy category buy real menu title']),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         SimpleOption(7, menu_strings['back'], shop_buy_category_buy_menu),
#         Text(' '),
#         SimpleOption(9, menu_strings['close'], highlight=False),
#     ]
# )

# shop_info_category_menu.extend(
#     [
#         PagedOption(menu_strings[x], x, False, False) for x in items_data['categories']
#     ]
# )

for category in item_manager.categories:
    option = PagedOption(menu_strings[category], category)

    option.selectable = option.highlight = bool(list(item_manager.get_items_by_category(category)))

    shop_buy_category_menu.append(option)
    shop_info_category_menu.append(option)

# for category in items_data['categories']:
#     # TODO: Remove found_items after this is done (testing purposes)
#     option = PagedOption(menu_strings[category], category)
#     option.class_items = defaultdict(list)

#     for name, item in items_data['items'].items():
#         if item['category'] == category:
#             for allowed in ([item['allow']] if isinstance(item['allow'], str) else item['allow']):
#                 option.class_items[allowed].append(name)

#     option.selectable = option.highlight = bool(option.class_items)  # option.found_items = found

#     shop_buy_category_menu.append(option)
#     shop_info_category_menu.append(option)

bank_menu.extend(
    [
        Text(menu_strings['bank menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['bank menu line 1'], bank_menu),
        SimpleOption(2, menu_strings['bank menu line 2'], bank_menu),
        SimpleOption(3, menu_strings['bank menu line 3'], bank_menu, selectable=False, highlight=False),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

quest_menu.extend(
    [
        Text(menu_strings['quest menu title']),
        # Text(' '),
        Text(menu_strings['quest menu description']),
        SimpleOption(1, menu_strings['quest menu line 1'], requirements_menu),
        SimpleOption(2, menu_strings['quest menu line 2'], quest_description_menu),
        Text(menu_strings['quest menu line 3']),
        Text(menu_strings['quest menu line 4']),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], quests_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

ascension_menu.extend(
    [
        Text(menu_strings['ascension menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['ascension menu line 1'], ascend_menu),
        SimpleOption(2, menu_strings['ascension menu line 2'], ascension_info_menu),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main2_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

ascend_menu.extend(
    [
        Text(menu_strings['ascend menu title']),
        Text(' '),
        Text(menu_strings['ascend menu line 1']),
        Text(menu_strings['ascend menu line 2']),
        Text(menu_strings['ascend menu line 3']),
        SimpleOption(4, menu_strings['yes']),
        SimpleOption(5, menu_strings['no'], ascension_menu),
        Text(' '),
        SimpleOption(7, menu_strings['back'], ascension_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

ascension_info_menu.extend(
    [
        Text(menu_strings['ascension info menu title']),
        Text(' '),
        Text(menu_strings['ascension info menu line 1']),
        Text(menu_strings['ascension info menu line 2']),
        Text(menu_strings['ascension info menu line 3']),
        Text(menu_strings['ascension info menu line 4']),
        Text(menu_strings['ascension info menu line 5']),
        Text(menu_strings['ascension info menu line 6']),
        SimpleOption(7, menu_strings['back'], ascension_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

vessel_menu.extend(
    [
        Text(menu_strings['vessel menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['vessel menu line 1'], 0),
        SimpleOption(2, menu_strings['vessel menu line 2'], 1),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main2_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

help_menu.extend(
    [
        Text(menu_strings['help menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['help menu line 1'], commands_menu),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main2_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

for command in ('!menu', ):
    commands_menu.append(command)

# commands_menu.extend(
#     [
#         Text(menu_strings['commands menu title']),
#         Text(' '),
#         Text('!menu'),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         SimpleOption(7, menu_strings['back'], help_menu),
#         SimpleOption(8, menu_strings['next'], commands_menu1),
#         SimpleOption(9, menu_strings['close'], highlight=False),
#     ]
# )

# commands_menu1.extend(
#     [
#         Text(menu_strings['commands menu title']),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         SimpleOption(7, menu_strings['back'], commands_menu),
#         SimpleOption(8, menu_strings['next'], commands_menu2),
#         SimpleOption(9, menu_strings['close'], highlight=False),
#     ]
# )

# commands_menu2.extend(
#     [
#         Text(menu_strings['commands menu title']),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         Text(' '),
#         SimpleOption(7, menu_strings['back'], commands_menu1),
#         Text(' '),
#         SimpleOption(9, menu_strings['close'], highlight=False),
#     ]
# )

mail_menu.extend(
    [
        Text(menu_strings['mail menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['mail menu line 1'], mail_inbox_menu),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], main2_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

mail_view_menu.extend(
    [
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(1, menu_strings['mail view menu settings'], mail_view_settings_menu),
        SimpleOption(7, menu_strings['back'], mail_inbox_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

mail_view_settings_menu.extend(
    [
        Text(menu_strings['mail view settings menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['mail view settings menu line 1']),
        SimpleOption(2, menu_strings['mail view settings menu line 2'], mail_view_settings_verify_menu),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], mail_view_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

mail_view_settings_verify_menu.extend(
    [
        Text(menu_strings['mail view settings verify menu title']),
        Text(' '),
        SimpleOption(1, menu_strings['yes']),
        SimpleOption(2, menu_strings['no'], mail_view_settings_menu),
        Text(' '),
        Text(' '),
        Text(' '),
        Text(' '),
        SimpleOption(7, menu_strings['back'], mail_view_settings_menu),
        Text(' '),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ]
)

item_zone_menu.extend(
    [
        Text(menu_strings['item zone menu title']),
        Text(menu_strings['item zone menu line 1']),
        SimpleOption(1, menu_strings['item zone menu line 2']),
        SimpleOption(2, menu_strings['item zone menu line 3']),
        SimpleOption(3, menu_strings['item zone menu line 4']),
    ]
)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPluginClassLoad
def on_class_load(name, instance):
    if instance.settings.config['class'] == 'demon':
        # class_info_demons.append(PagedOption(instance.settings.strings.get('name', MENU_MISSING_TEXT), name))
        class_info_demons.append(PagedOption(instance.settings.strings['name'], name))
    else:
        # class_info_angels.append(PagedOption(instance.settings.strings.get('name', MENU_MISSING_TEXT), name))
        class_info_angels.append(PagedOption(instance.settings.strings['name'], name))


@OnPluginClassUnload
def on_class_unload(name, instance):
    menu = class_info_demons if instance.settings.config['class'] == 'demon' else class_info_angels

    for option in list(menu):
        if option.value == name:
            menu.remove(option)
            break
