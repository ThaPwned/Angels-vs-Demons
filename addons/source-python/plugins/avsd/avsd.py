# ../avsd/avsd.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Random
from random import choice
# from random import random
#   Time
from time import sleep
#   Warning
from warnings import warn

# Source.Python Imports
#   Commands
from commands import CommandReturn
from commands.typed import TypedClientCommand
from commands.typed import TypedSayCommand
#   Core
from core import GAME_NAME
#   CVars
from cvars import cvar
#   Engines
from engines.server import global_vars
#   Entities
from entities.entity import Entity
from entities.entity import BaseEntity
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
#   Events
from events import Event
#   Filters
from filters.weapons import WeaponClassIter
#   Listeners
from listeners import OnLevelInit
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Memory
from memory import make_object
#   Messages
from messages import SayText2
#   Players
from players.constants import PlayerStates
from players.entity import Player as SPPlayer
from players.helpers import get_client_language
#   Stringtables
from stringtables.downloads import Downloadables
#   Weapons
from weapons.restrictions import WeaponRestrictionHandler

# AvsD Imports
#   Config
from .core.config import cfg_assist_kill_xp
from .core.config import cfg_headshot_xp
from .core.config import cfg_kill_xp
from .core.config import cfg_melee_kill_xp
from .core.config import experiences_data
#   Constants
from .core.constants import MAX_CASH
from .core.constants import MENU_MISSING_TEXT
#   Database
from .core.database.manager import database_manager
from .core.database.thread import _repeat
from .core.database.thread import _thread
#   Emulate
from .core.emulate import emulate_manager
#   Items
from .core.items import item_manager
#   Listeners
from .core.listeners import OnPlayerDelete
from .core.listeners import OnPlayerReady
from .core.listeners import OnPlayerStartTouch
from .core.listeners import OnPlayerSwitchClass
from .core.listeners import OnPlayerSwitchClassPost
from .core.listeners import OnPlayerUICooldownPre
from .core.listeners import OnPluginUnload
#   Listeners
from .core.menus.menus import main_menu
#   Modules
from .core.modules.classes.manager import class_manager
from .core.modules.items.manager import items_manager
from .core.modules.stats.manager import stats_manager
#   Players
from .core.players.entity import Player
from .core.players.filters import PlayerIter
from .core.players.filters import PlayerReadyIter
#   Quests
from .core.quests import quest_manager
#   Translations
from .core.translations import chat_strings
from .core.translations import ui_strings


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
downloadables = Downloadables()
weapon_restrict_manager = WeaponRestrictionHandler()
restricted_weapons = [x.name for x in WeaponClassIter('all', ['melee', 'grenade', 'objective'])]
melee_weapons = [x.basename for x in WeaponClassIter('melee')]

# MONKEY PATCH
melee_weapons.append('knife_default_ct')
# MONKEY PATCH

bot_stop_cvar = cvar.find_var('bot_stop')
mp_maxmoney_cvar = cvar.find_var('mp_maxmoney')

if mp_maxmoney_cvar is not None:
    mp_maxmoney_cvar.set_int(MAX_CASH)

MAX_LEVEL = max([int(x) for x in experiences_data['required']]) + 1

spawn_deposit_message = SayText2(chat_strings['spawn deposit'])
not_ready_message = SayText2(chat_strings['not ready'])
maximum_deposit_message = SayText2(chat_strings['maximum deposit'])
maximum_withdraw_message = SayText2(chat_strings['maximum withdraw'])
deposit_error_message = SayText2(chat_strings['deposit error'])
withdraw_error_message = SayText2(chat_strings['withdraw error'])

QUEST_KILL = quest_manager.get_requirements('kill')
QUEST_KILL_ENEMY = quest_manager.get_dynamic_requirements('kill')
QUEST_PLAY_TIME = quest_manager.get_requirements('play_time')
QUEST_VISIT_MAP = quest_manager.get_dynamic_requirements('visit_map')

if GAME_NAME == 'csgo':
    downloadables.add_directory('materials/decals')
    downloadables.add_directory('materials/effects')
    downloadables.add_directory('materials/impact')
    downloadables.add_directory('materials/overlays')
    downloadables.add_directory('materials/particle')
    downloadables.add_directory('materials/particle_debris_burst')
    downloadables.add_directory('materials/particle_flares')
    downloadables.add_directory('materials/smoke')
    downloadables.add_directory('materials/sprites')
    downloadables.add_directory('materials/swarm')
    downloadables.add_directory('materials/vgui')
    downloadables.add_directory('materials/water_splash')

downloadables.add_directory('particles')

# downloadables.add_directory('materials/models')
downloadables.add_directory('materials/models/custom_prop/pw_wings')
downloadables.add_directory('materials/models/shop')
downloadables.add_directory('models/custom_prop/pw_wings')
downloadables.add_directory('models/shop')


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def load():
    database_manager.connect()

    class_manager.load_all()
    items_manager.load_all()
    stats_manager.load_all()

    for _, player in PlayerIter():
        Player(player.uniqueid)

    if not bot_stop_cvar.get_int():
        emulate_manager.start()


def unload():
    database_manager._unloading = True

    for item in list(item_manager._spawned_items):
        item.remove()

    for avsdplayer in Player._players.values():
        OnPlayerDelete.manager.notify(avsdplayer)

    for _, avsdplayer in PlayerReadyIter():
        avsdplayer.save()

    database_manager.cleanup()

    OnPluginUnload.manager.notify()

    class_manager.unload_all()
    stats_manager.unload_all()

    emulate_manager.stop()

    database_manager.close()

    # I live life dangerously
    while _repeat.status == RepeatStatus.RUNNING:
        _thread._tick()
        sleep(0.01)


def restrict_weapons(player):
    weapon_restrict_manager.add_player_restrictions(player, *restricted_weapons)

    for weapon in player.weapons(not_filters=['melee', 'grenade', 'objective']):
        # player.drop_weapon(weapon.pointer, None, None)
        player.drop_weapon(weapon)


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('round_prestart')
def round_prestart(event):
    for item in list(item_manager._spawned_items):
        item.remove()


@Event('player_spawn')
def player_spawn(event):
    userid = event['userid']
    avsdplayer = Player.from_userid(userid)

    cash = avsdplayer.data.pop('_cash', None)

    if cash is not None:
        spawn_deposit_message.send(avsdplayer.index, cash=cash)

    player = avsdplayer.player

    if not player.dead and player.team_index in (2, 3):
        if avsdplayer.ready:
            if avsdplayer.active_class.settings.config['knife_only']:
                restrict_weapons(player)

            for state, value in avsdplayer.state.items():
                if value:
                    warn(f"State '{state}' got a value of {value} when it should be 0 for userid {userid}")


@Event('player_death')
def player_death(event):
    userid = event['userid']
    avsdvictim = Player.from_userid(userid)

    if avsdvictim._is_bot:
        if avsdvictim.ready:
            allowed = avsdvictim.allowed_classes

            allowed.remove(avsdvictim.current_class)

            avsdvictim.current_class = choice(allowed)

    attacker = event['attacker']

    if not attacker:
        return

    if userid == attacker:
        return

    player = avsdvictim.player

    if not event.is_empty('assister'):
        assister = event['assister']

        if assister:
            avsdplayer2 = Player.from_userid(assister)

            if avsdplayer2.ready:
                value = cfg_assist_kill_xp.get_int()

                if value:
                    if avsdvictim._is_bot:
                        value = round(value / 2)

                    avsdplayer2.xp += value

                    if not avsdplayer2._is_bot:
                        avsdplayer2.hudinfo.add_message(ui_strings['ui killing assist'].get_string(get_client_language(avsdplayer2.index), name=player.name, value=value))

    avsdattacker = Player.from_userid(attacker)

    if not avsdattacker.ready:
        return

    enemy_team = player.team_index

    if enemy_team == avsdattacker.player.team_index:
        return

    language = get_client_language(avsdattacker.index)

    value = cfg_kill_xp.get_int()

    # TODO: Just to check if there's some missing melee weapons
    # print(event['weapon'], event['weapon'] in melee_weapons)

    if event['weapon'] in melee_weapons:
        value += cfg_melee_kill_xp.get_int()
        message = ui_strings['ui killing melee'].get_string(language, name=player.name, value=value)
    elif event['headshot']:
        value += cfg_headshot_xp.get_int()
        message = ui_strings['ui killing headshot'].get_string(language, name=player.name, value=value)
    else:
        message = ui_strings['ui killing'].get_string(language, name=player.name, value=value)

    if value:
        if avsdvictim._is_bot:
            value = round(value / 2)

        avsdattacker.xp += value

        if not avsdattacker._is_bot:
            avsdattacker.hudinfo.add_message(message)

    QUEST_KILL.increase(avsdattacker)
    QUEST_KILL_ENEMY(enemy=enemy_team).increase(avsdattacker)

    # TODO: Bots don't do anything with items yet, so it'd just waste space on the storage drive
    if avsdattacker._is_bot:
        return

    # if not randrange(0, 300):
    # if 0.003 >= random():
    item = item_manager.generate(class_=avsdattacker.current_class)
    item.spawn(avsdattacker, player.origin)


@Event('player_team')
def player_team(event):
    if not event['disconnect']:
        userid = event['userid']
        avsdplayer = Player.from_userid(userid)

        if avsdplayer.ready:
            # Can't use avsdplayer.current_class here
            new_class_name = {2:avsdplayer._current_demon_class, 3:avsdplayer._current_angel_class}.get(event['team'])

            old_class_name = avsdplayer._current_class

            if old_class_name != new_class_name:
                OnPlayerSwitchClass.manager.notify(avsdplayer, old_class_name, new_class_name)

                avsdplayer._current_class = new_class_name

                OnPlayerSwitchClassPost.manager.notify(avsdplayer, old_class_name, new_class_name)

                from listeners.tick import Delay
                Delay(0.2, avsdplayer.update_clan_tag)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnLevelInit
def on_level_init(map_name):
    requirements = QUEST_VISIT_MAP(map=map_name)

    for _, player in PlayerReadyIter():
        requirements.increase(player)


@OnPlayerReady
def on_player_ready(avsdplayer):
    QUEST_VISIT_MAP(map=global_vars.map_name).increase(avsdplayer)

    player = avsdplayer.player

    if not player.dead and player.team_index in (2, 3):
        if avsdplayer.active_class.settings.config['knife_only']:
            restrict_weapons(player)


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if new is not None:
        new = class_manager[new]

        if avsdplayer._is_bot:
            avsdplayer.active_class._upgrade_skills()

    if old is None:
        if new is not None and new.settings.config['knife_only']:
            player = avsdplayer.player

            if not player.dead and player.team_index in (2, 3):
                restrict_weapons(player)
    else:
        old = class_manager[old]

        if old.settings.config['knife_only']:
            if new is None or not new.settings.config['knife_only']:
                weapon_restrict_manager.remove_player_restrictions(avsdplayer.player, *restricted_weapons)
        else:
            if new is not None and new.settings.config['knife_only']:
                player = avsdplayer.player

                if not player.dead and player.team_index in (2, 3):
                    restrict_weapons(player)


@OnPlayerUICooldownPre
def on_player_ui_cooldown_pre(avsdplayer, active_class, language, messages, now):
    settings = active_class.settings

    if settings._abilities:
        for name in sorted(settings._abilities, key=lambda x: settings._abilities[x]._index):
            cooldown = active_class.skills[name].cooldown

            if cooldown > now:
                # messages.append(ui_strings['ui cooldown'].get_string(language, name=settings.strings.get(name.lower(), MENU_MISSING_TEXT).get_string(language), cooldown=cooldown - now))
                messages.append(ui_strings['ui cooldown'].get_string(language, name=settings.strings[name].get_string(language), cooldown=cooldown - now))
            elif cooldown + 3 > now:
                # messages.append(ui_strings['ui cooldown ready'].get_string(language, name=settings.strings.get(name.lower(), MENU_MISSING_TEXT).get_string(language)))
                messages.append(ui_strings['ui cooldown ready'].get_string(language, name=settings.strings[name].get_string(language)))


# ============================================================================
# >> COMMANDS
# ============================================================================
@TypedClientCommand('ability')
def ability_command(command, ability:int):
    avsdplayer = Player.from_index(command.index)

    if not avsdplayer.player.dead:
        active_class = avsdplayer.active_class

        if active_class is not None:
            ability -= 1

            for name, ability in active_class.settings._abilities.items():
                if ability._index == ability:
                    active_class.skills[name]()

                    break

    return CommandReturn.BLOCK


@TypedSayCommand('menu')
def say_command_menu(command):
    if Player.from_index(command.index).ready:
        main_menu.send(command.index)
    else:
        not_ready_message.send(command.index)

    return CommandReturn.BLOCK


@TypedSayCommand('!deposit')
def say_deposit(command, value:int):
    avsdplayer = Player.from_index(command.index)
    player = avsdplayer.player

    if value > player.cash:
        maximum_deposit_message.send(command.index, cash=player.cash)
    else:
        player.cash -= value
        avsdplayer.cash += value

    return CommandReturn.BLOCK


@TypedSayCommand('!withdraw')
def say_withdraw(command, value:int):
    avsdplayer = Player.from_index(command.index)
    player = avsdplayer.player

    if value > avsdplayer.cash:
        maximum_withdraw_message.send(command.index, cash=avsdplayer.cash)
    elif player.cash + value > MAX_CASH:
        maximum_withdraw_message.send(command.index, cash=MAX_CASH - player.cash)
    else:
        player.cash += value
        avsdplayer.cash -= value

    return CommandReturn.BLOCK


# ============================================================================
# >> HOOKS
# ============================================================================
@EntityPreHook(EntityCondition.is_player, 'add_account')
def on_pre_add_account(stack):
    player = make_object(SPPlayer, stack[0])

    if player.cash + stack[1] > MAX_CASH:
        avsdplayer = Player.from_index(player.index)

        if avsdplayer.ready:
            cash = player.cash + stack[1] - MAX_CASH

            if '_cash' not in avsdplayer.data:
                avsdplayer.data['_cash'] = 0

            avsdplayer.data['_cash'] += cash

            avsdplayer.cash += cash

            stack[1] -= cash


@EntityPreHook(EntityCondition.is_player, 'start_touch')
def on_start_touch(stack):
    entity = make_object(BaseEntity, stack[0])

    if entity.is_player():
        avsdplayer = Player.from_index(entity.index)

        if avsdplayer.ready:
            other = None  # TODO: No reason to expose this yet: make_object(Entity, stack[0])
            grounded = False

            if entity.ground_entity != -1:
                if Entity(entity.index).flags & PlayerStates.ONGROUND:
                    grounded = True

            OnPlayerStartTouch.manager.notify(avsdplayer, other, grounded)


# ============================================================================
# >> REPEATS
# ============================================================================
@Repeat
def quest_play_time():
    for _, avsdplayer in PlayerReadyIter(not_filters=['un', 'spec']):
        QUEST_PLAY_TIME.increase(avsdplayer)
quest_play_time.start(60)


@Repeat
def save_data_repeat():
    for _, avsdplayer in PlayerReadyIter():
        avsdplayer.save()

    database_manager.cleanup()
save_data_repeat.start(60 * 5)


@Repeat
def messages():
    for _, avsdplayer in PlayerReadyIter('human', ['un', 'spec']):
        avsdplayer.hudinfo.show()
messages.start(0.1)
