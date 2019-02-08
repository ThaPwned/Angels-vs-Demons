# ../avsd/core/config/__init__.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Configobj
from configobj import ConfigObj
#   JSON
from json import load

# Source.Python Imports
#   Config
from config.manager import ConfigManager

# AvsD Imports
#   Constants
from ..constants.info import info
from ..constants.paths import CFG_PATH
#   Translations
# from ..translations import config_strings


# ============================================================================
# >> CONFIGURATION
# ============================================================================
# Create the configuration file
# with ConfigManager('{0}/config.cfg'.format(info.name), cvar_prefix='{0}_'.format(info.name)) as config:
with ConfigManager(f'{info.name}/config.cfg', cvar_prefix=f'{info.name}_') as config:
    cfg_kill_xp = config.cvar('kill_xp', '25')
    cfg_assist_kill_xp = config.cvar('assist_kill_xp', '15')
    cfg_melee_kill_xp = config.cvar('melee_kill_xp', '50')
    cfg_headshot_xp = config.cvar('headshot_xp', '40')
    cfg_bomb_plant_xp = config.cvar('bomb_plant_xp', '15')
    cfg_bomb_explode_xp = config.cvar('bomb_explode_xp', '25')
    cfg_bomb_defuse_xp = config.cvar('bomb_defuse_xp', '40')
    cfg_hostage_rescue_xp = config.cvar('hostage_rescue_xp', '20')
    cfg_sell_percentage = config.cvar('sell_percentage', '75')
    cfg_ascend_cash_requirement = config.cvar('ascend_cash_requirement', '500000')


experiences_data = ConfigObj(CFG_PATH / 'experiences.ini', unrepr=True)
# quests_data = ConfigObj(CFG_PATH / 'quests.ini', unrepr=True)
items_data = ConfigObj(CFG_PATH / 'items.ini', unrepr=True)

with open(CFG_PATH / 'quests.json') as f:
    quests_data = load(f)
