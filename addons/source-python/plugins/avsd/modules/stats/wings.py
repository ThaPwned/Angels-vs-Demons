# ../avsd/modules/stats/wings.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Configobj
from configobj import ConfigObj
#   Time
from time import time

# Source.Python Imports
#   Engines
from engines.precache import Model
from engines.trace import engine_trace
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
#   Entities
from entities import BaseEntityGenerator
from entities.entity import BaseEntity
from entities.entity import Entity
from entities.helpers import index_from_inthandle
# from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
#   Events
from events import Event
#   Filters
# from filters.entities import EntityIter
from filters.players import PlayerIter
#   Listeners
from listeners import OnLevelInit
from listeners import OnPlayerRunCommand
from listeners.tick import Delay
from listeners.tick import Repeat
# from listeners.tick import RepeatStatus
#   Mathlib
from mathlib import QAngle
from mathlib import Vector
#   Memory
from memory import make_object
#   Paths
from paths import GAME_PATH
#   Players
# from players import UserCmd
from players.constants import PlayerButtons
from players.constants import PlayerStates
# from players.entity import Player

# AvsD Imports
#   Helpers
from ...core.helpers.math import AngleVectors
from ...core.helpers.particle import Particle
#   Listeners
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerFlyUpdate
from ...core.listeners import OnPlayerFlyUpdatePost
from ...core.listeners import OnPlayerFlyUpdatePre
# from ...core.listeners import OnPlayerHudhintPre
from ...core.listeners import OnPlayerReady
from ...core.listeners import OnPlayerReset
from ...core.listeners import OnPlayerStatsUpdatePre
from ...core.listeners import OnPlayerStartTouch
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnPlayerUIBuffPre
from ...core.listeners import OnPlayerUIInfoPre
from ...core.listeners import OnPlayerUpgradeSkill
from ...core.listeners import OnPluginUnload
#   Modules
from ...core.modules.classes.manager import class_manager
#   Players
from ...core.players.entity import Player as AVSDPlayer
#   Translations
# from ...core.translations import menu_strings
from ...core.translations import ui_strings


# ============================================================================
# >> CLASSES
# ============================================================================
class FlyingProperty(object):
    def __get__(self, obj, type=None):
        return obj.data.get('_wings_is_flying', False)

    def __set__(self, obj, value):
        if not obj.ready:
            return

        if value:
            if not obj.stats['flighttime']:
                # print('no fly time')
                obj.data['_wings_no_fly_time_hudhint'] = time() + 3
                # obj.hinttext()
                return

            if obj.stats['flighttime'] - obj.data.get('_wings_fly_time', 0) < 0:
                if obj.player.ground_entity == -1:
                    # print('blah', obj.stats['flighttime'], obj.data.get('_wings_fly_time', 0))
                    obj.data['_wings_no_fly_time_hudhint'] = time() + 3
                    # obj.hinttext()
                    return

                # obj.data['_wings_fly_time'] = 0

        data = {'state':not obj.flying, 'allow':True}

        OnPlayerFlyUpdatePre.manager.notify(obj, data)

        if not data['allow']:
            return

        OnPlayerFlyUpdate.manager.notify(obj, value)

        player = obj.player

        if not obj.flying:
            if player.ground_entity != -1:
                origin = player.origin

                _general_fly.create(player.origin)

                origin[2] += 3

                ray = Ray(origin, origin, player.mins, player.maxs)

                trace = GameTrace()

                engine_trace.trace_ray(ray, ContentMasks.ALL, TraceFilterSimple(BaseEntityGenerator()), trace)

                if not trace.did_hit():
                    # player.teleport(origin=origin)
                    player.origin = origin

            player.base_velocity = Vector(0, 0, 50)

        player.jetpack = value

        obj.data['_wings_is_flying'] = value

        buffer_time = obj.data.pop('_wings_buffering', None)

        if buffer_time is not None:
            obj.data['_wings_fly_time'] = max(obj.data['_wings_fly_time'] - (time() - buffer_time) * 2.5, 0)

        # index = obj.data.get('_wings')
        inthandle = obj.data.get('_wings')

        # if index is not None:
        if inthandle is not None:
            # try:
            #     entity = BaseEntity(index)
            # except ValueError:
            #     pass
            # else:
                # _indexes[index] = not value

            try:
                index = index_from_inthandle(inthandle)
            except ValueError:
                pass
            else:
                entity = BaseEntity(index)

                if value:
                    entity.color = entity.color.with_alpha(255)

                    entity.set_key_value_int('disableshadows', 0)
                    entity.set_key_value_int('disablereceiveshadows', 0)
                else:
                    entity.color = entity.color.with_alpha(0)

                    entity.set_key_value_int('disableshadows', 1)
                    entity.set_key_value_int('disablereceiveshadows', 1)

        OnPlayerFlyUpdatePost.manager.notify(obj, value)

        if value:
            flighttime = obj.stats['flighttime'] - obj.data.get('_wings_fly_time', 0)
            obj.data['_wings_flight_delay'] = Delay(flighttime, stop_flying, args=(obj, flighttime))
            # obj.data['_wings_hinttext_repeat'] = Repeat(obj.hinttext)
            # obj.data['_wings_hinttext_repeat'].start(0.1)
        else:
            delay = obj.data['_wings_flight_delay']

            if delay.running:
                obj.data['_wings_fly_time'] = obj.stats['flighttime'] - (delay.exec_time - time())
                # obj.data['_wings_fly_time'] = obj.stats['flighttime'] - obj.data['_wings_flight_delay'].elapsed_time

                delay.cancel()

                # obj.data['_wings_hinttext_repeat'].stop()

        # obj.hinttext()


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
# _indexes = {}

_general_fly = Particle('_General_Fly', lifetime=5)

wings_info = ConfigObj(GAME_PATH / 'cfg/source-python/avsd/wings.ini')
wings_models = {x: Model(wings_info[x]['model']) for x in wings_info}

assert not hasattr(AVSDPlayer, 'flying')

AVSDPlayer.flying = FlyingProperty()


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    userid = event['userid']

    if not userid:
        return

    avsdplayer = AVSDPlayer.from_userid(userid)

    if not avsdplayer.ready:
        return

    on_player_ready(avsdplayer)

    if avsdplayer.flying:
        avsdplayer.flying = False


@Event('player_death')
def player_death(event):
    userid = event['userid']
    avsdplayer = AVSDPlayer.from_userid(userid)

    avsdplayer.data['_wings_is_flying'] = False

    # index = avsdplayer.data.pop('_wings', None)
    inthandle = avsdplayer.data.pop('_wings', None)

    # if index is not None:
    if inthandle is not None:
        # _indexes.pop(index, None)

        try:
            index = index_from_inthandle(inthandle)
        except ValueError:
            pass
        else:
            BaseEntity(index).remove()

        # try:
        #     entity = Entity(index)
        # except ValueError:
        #     pass
        # else:
        #     # if hasattr(entity, 'class_name') and entity.class_name == 'avsd_wings':
        #     #     if entity.target_name == str(userid):
        #     entity.remove()


@Event('round_prestart')
def round_prestart(event):
    for player in PlayerIter():
        avsdplayer = AVSDPlayer.from_index(player.index)

        if avsdplayer.flying:
            avsdplayer.flying = False


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnLevelInit
def on_level_init(map_name):
    for player in PlayerIter():
        avsdplayer = AVSDPlayer.from_index(player.index)

        avsdplayer.data.pop('_wings', None)

    # _indexes.clear()


@OnPlayerDelete
def on_player_delete(avsdplayer):
    delay = avsdplayer.data.get('_wings_flight_delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    # repeat = avsdplayer.data.get('_wings_hinttext_repeat')

    # if repeat is not None:
    #     if repeat.status == RepeatStatus.RUNNING:
    #         repeat.stop()

    delay = avsdplayer.data.get('_wings_spawn_delay')

    if delay is not None:
        if delay.running:
            delay.cancel()


# @OnPlayerHudhintPre
# def on_player_hudhint_pre(avsdplayer, class_, language, messages):
#     if avsdplayer.flying:
#         duration = avsdplayer.data['_wings_flight_delay'].args[1] - (avsdplayer.data['_wings_flight_delay'].exec_time - time())
#         # duration = avsdplayer.data['_wings_flight_delay'].args[1] - avsdplayer.data['_wings_flight_delay'].elapsed_time
#         flytime = duration + avsdplayer.data.get('_wings_fly_time', 0)

#         messages.append(menu_strings['hinttext flying'].get_string(language, value=round(avsdplayer.stats['flighttime'] - flytime, 1)))
#     elif avsdplayer.data.get('_wings_no_fly_time_hudhint', 0) >= time():
#         messages.append('No fly time')


@OnPlayerReady
def on_player_ready(avsdplayer, instant=False):
    if avsdplayer.current_class is None:
        return

    wings = avsdplayer.stats.get('wings')

    if wings is None:
        return

    player = avsdplayer.player

    if player.dead:
        return

    if player.team_index < 2:
        return

    delay = avsdplayer.data.get('_wings_spawn_delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    if instant:
        spawn_wings(avsdplayer, player, wings)
    else:
        avsdplayer.data['_wings_spawn_delay'] = Delay(0, spawn_wings, args=(avsdplayer, player, wings))


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    delay = avsdplayer.data.get('_wings_spawn_delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    on_player_ready(avsdplayer, True)

    if avsdplayer.flying:
        if not avsdplayer.stats['flighttime']:
            avsdplayer.flying = False
        elif avsdplayer.stats['flighttime'] - avsdplayer.data.get('_wings_fly_time', 0) < 0:
            print('blah', avsdplayer.stats['flighttime'], avsdplayer.data.get('_wings_fly_time', 0))


@OnPlayerUIBuffPre
def on_player_ui_buff_pre(avsdplayer, active_class, language, messages, now):
    # fly_time = avsdplayer.data.get('_wings_fly_time')

    # if fly_time:
    #     buffer_time = avsdplayer.data.get('_wings_buffering')

    #     if buffer_time is None:
    #         duration = avsdplayer.data['_wings_flight_delay'].args[1] - (avsdplayer.data['_wings_flight_delay'].exec_time - time())
    #         flytime = duration + avsdplayer.data.get('_wings_fly_time', 0)

    #         # messages.append(menu_strings['hinttext flying'].get_string(language, value=round(avsdplayer.stats['flighttime'] - flytime, 1)))
    #         messages.append(ui_strings['ui flying'].get_string(language, value=round(avsdplayer.stats['flighttime'] - flytime, 1)))
    #     else:
    #         buffering = (time() - buffer_time) * 2.5

    #         messages.append(ui_strings['ui flying'].get_string(language, value=round(min(avsdplayer.stats['flighttime'] - (avsdplayer.data['_wings_fly_time'] - buffering), avsdplayer.stats['flighttime']), 1)))

    #         if buffering > avsdplayer.data['_wings_fly_time']:
    #             avsdplayer.data['_wings_fly_time'] = 0
    #             avsdplayer.data['_wings_buffering'] = None

    flytime = avsdplayer.data.get('_wings_fly_time', 0)

    if avsdplayer.flying:
        duration = avsdplayer.data['_wings_flight_delay'].args[1] - (avsdplayer.data['_wings_flight_delay'].exec_time - time())
        flytime += duration

        # messages.append(menu_strings['hinttext flying'].get_string(language, value=round(avsdplayer.stats['flighttime'] - flytime, 1)))
        # abs() required here (see: https://en.wikipedia.org/wiki/Signed_zero)
        messages.append(ui_strings['ui flying'].get_string(language, value=abs(round(avsdplayer.stats['flighttime'] - flytime, 1))))
    else:
        if flytime:
            buffer_time = avsdplayer.data.get('_wings_buffering')

            if buffer_time is None:
                # abs() required here (see: https://en.wikipedia.org/wiki/Signed_zero)
                messages.append(ui_strings['ui flying'].get_string(language, value=abs(round(avsdplayer.stats['flighttime'] - flytime, 1))))
            else:
                buffering = (time() - buffer_time) * 2.5

                # abs() required here (see: https://en.wikipedia.org/wiki/Signed_zero)
                messages.append(ui_strings['ui flying'].get_string(language, value=abs(round(min(avsdplayer.stats['flighttime'] - (flytime - buffering), avsdplayer.stats['flighttime']), 1))))

                if buffering > flytime:
                    avsdplayer.data['_wings_fly_time'] = 0


@OnPlayerUIInfoPre
def on_player_ui_info_pre(avsdplayer, active_class, language, messages, now):
    if avsdplayer.data.get('_wings_no_fly_time_hudhint', 0) >= time():
        messages.append('No fly time')


@OnPluginUnload
def on_plugin_unload():
    for player in PlayerIter('alive'):
        player.jetpack = False

    # for entity in EntityIter():
    #     if entity.index in _indexes:
    #         entity.remove()

    # _indexes.clear()


@OnPlayerReset
def on_player_reset(avsdplayer):
    # skill_name = '{0} wings'.format('Angelic' if avsdplayer.active_class.settings.config['class'] == 'angel' else 'Demonic')
    skill = avsdplayer.skills['wings']
    level = skill.level

    if level:
        flyspeed = skill['flyspeed']
        flighttime = skill['flighttime']

        stats = avsdplayer.stats

        stats['flyspeed'] = stats.get('flyspeed', 0) - flyspeed * level
        stats['flighttime'] = stats.get('flighttime', 0) - flighttime * level


@OnPlayerStatsUpdatePre
def on_player_stats_update_pre(avsdplayer, class_, initialize, data):
    if initialize:
        # skill_name = '{0} wings'.format('Angelic' if class_.settings.config['class'] == 'angel' else 'Demonic')
        skill = class_.skills['wings']
        level = skill.level

        if level:
            flyspeed = skill['flyspeed']
            flighttime = skill['flighttime']

            data['flyspeed'] = data.get('flyspeed', 0) + flyspeed * level + skill.stats['flyspeed']
            data['flighttime'] = data.get('flighttime', 0) + flighttime * level + skill.stats['flighttime']


@OnPlayerUpgradeSkill
def on_player_upgrade_skill(avsdplayer, skill, old_level, new_level):
    # if skill.name in ('Angelic wings', 'Demonic wings'):
    if skill.name == 'wings':
        flyspeed = skill['flyspeed']
        flighttime = skill['flighttime']

        stats = avsdplayer.stats

        stats['flyspeed'] = stats.get('flyspeed', 0) + flyspeed * (new_level - old_level)
        stats['flighttime'] = stats.get('flighttime', 0) + flighttime * (new_level - old_level)


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def spawn_wings(avsdplayer, player, wings):
    instance = class_manager[avsdplayer.current_class]

    wing_model = instance.settings.config['wings_model']

    if not isinstance(wing_model, str):
        wing_model = wing_model[wings - 1]

    data = wings_info[wing_model]

    origin = player.origin
    angles = player.angles

    offset = Vector(*[float(x) for x in data['position']])
    angles += QAngle(*[float(x) for x in data['angles']])

    forward, right, up = AngleVectors(angles)

    origin[0] += right[0] * offset[0] + forward[0] * offset[1] + up[0] * offset[2]
    origin[1] += right[1] * offset[0] + forward[1] * offset[1] + up[1] * offset[2]
    origin[2] += right[2] * offset[0] + forward[2] * offset[1] + up[2] * offset[2]

    origin.z += 52

    entity = Entity.create('prop_dynamic_override')
    entity.model = wings_models[wing_model]

    entity.origin = origin
    entity.angles = angles

    entity.spawn()

    entity.set_key_value_int('disableshadows', 1)
    entity.set_key_value_int('disablereceiveshadows', 1)

    entity.set_parent(player, player.lookup_attachment('facemask'))

    entity.color = entity.color.with_alpha(255 if avsdplayer.flying else 0)

    # index = avsdplayer.data.get('_wings')
    inthandle = avsdplayer.data.get('_wings')

    if inthandle is not None:
        # _indexes.pop(index, None)

        try:
            index = index_from_inthandle(inthandle)
        except ValueError:
            pass
        else:
            BaseEntity(index).remove()

        # try:
        #     tmp = Entity(index)
        # except ValueError:
        #     pass
        # else:
        #     tmp.remove()

    # avsdplayer.data['_wings'] = entity.index
    avsdplayer.data['_wings'] = entity.inthandle

    # _indexes[entity.index] = True


def stop_flying(avsdplayer, flighttime):
    duration = flighttime - (avsdplayer.data['_wings_flight_delay'].exec_time - time())
    # duration = flighttime - avsdplayer.data['_wings_flight_delay'].elapsed_time
    flytime = avsdplayer.data['_wings_fly_time'] = duration + avsdplayer.data.get('_wings_fly_time', 0)

    if flytime >= avsdplayer.stats['flighttime']:
        avsdplayer.flying = False

        # avsdplayer.data['_wings_hinttext_repeat'].stop()
    else:
        duration = avsdplayer.stats['flighttime'] - flytime
        avsdplayer.data['_wings_flight_delay'] = Delay(duration, stop_flying, args=(avsdplayer, duration))


# ============================================================================
# >> HOOKS
# ============================================================================
@OnPlayerRunCommand
def on_player_run_command(player, usercmd):
    if not player.dead and not player.steamid == 'BOT':
        if usercmd.buttons & PlayerButtons.USE and not player.buttons & PlayerButtons.USE:
            avsdplayer = AVSDPlayer.from_index(player.index)

            # Dyncall
            player.delay(0, setattr, args=(avsdplayer, 'flying', not avsdplayer.flying))
            # avsdplayer.flying = not avsdplayer.flying


@OnPlayerStartTouch
def on_player_start_touch(avsdplayer, other, grounded):
    if grounded:
        # if avsdplayer.data.get('_wings_fly_time'):
        #     avsdplayer.data['_wings_fly_time'] = 0

        if not avsdplayer.flying and avsdplayer.data.get('_wings_fly_time') and not avsdplayer.data.get('_wings_buffering'):
            avsdplayer.data['_wings_buffering'] = time()

# @EntityPreHook(EntityCondition.is_player, 'start_touch')
# def start_touch(stack):
#     entity = make_object(Entity, stack[0])

#     if entity.is_player():
#         if entity.flags & PlayerStates.ONGROUND or entity.ground_entity != -1:
#             avsdplayer = AVSDPlayer.from_index(entity.index)

#             if avsdplayer.ready:
#                 if avsdplayer.data.get('_wings_fly_time'):
#                     avsdplayer.data['_wings_fly_time'] = 0


# # TODO: Optimize this as much as possible
# # @EntityPreHook(EntityCondition.equals_entity_classname('prop_dynamic_override'), 'set_transmit')
# def pre_set_transmit(stack):
#     # TODO: Maybe just use the pointer here?
#     if _indexes.get(index_from_pointer(stack[0]), False):
#         return False


# ============================================================================
# >> REPEATS
# ============================================================================
@Repeat
def check_player_on_ground():
    for player in PlayerIter('alive'):
        if player.ground_entity != -1 and player.flags & PlayerStates.ONGROUND:
            avsdplayer = AVSDPlayer.from_index(player.index)

            if not avsdplayer.flying and avsdplayer.data.get('_wings_fly_time') and not avsdplayer.data.get('_wings_buffering'):
                avsdplayer.data['_wings_buffering'] = time()
check_player_on_ground.start(0.1)


# ============================================================================
# >> RE-ADJUSTING OF WINGS
# ============================================================================
from collections import defaultdict
from commands import CommandReturn
from commands.typed import TypedSayCommand
from entities.helpers import index_from_edict
from menus import PagedMenu
from menus import PagedOption
from messages import SayText2
from players.bots import bot_manager
from players.bots import BotCmd
from players.entity import Player

_players = defaultdict(dict)


main_menu = PagedMenu()
axis_menu = PagedMenu()
values_menu = PagedMenu()

axis_menu.parent_menu = main_menu
values_menu.parent_menu = axis_menu

main_menu.title = 'Wings Adjustment'
main_menu.description = 'Choose a wing model'
axis_menu.title = 'Wings Adjustment'
axis_menu.description = 'Choose the axis to change'
values_menu.title = 'Wings Adjustment'
# values_menu.description = 'Choose how much to shift the values'

for name in wings_info:
    main_menu.append(PagedOption(name, name))

for name, key, index in (('x', 'position', 0), ('y', 'position', 1), ('z', 'position', 2), ('pitch', 'angles', 0), ('yaw', 'angles', 1), ('roll', 'angles', 2)):
    axis_menu.append(PagedOption(name, (name, key, index)))

for value in (0.1, -0.1, 1, -1, 10, -10):
    values_menu.append(PagedOption(value, value))


@TypedSayCommand('avsd_edit')
def avsd_edit_command(command):
    # bot_edict = bot_manager.create_bot('AvsD Test Bot')

    # if bot_edict is None:
    #     return

    # controller = bot_manager.get_bot_controller(bot_edict)

    # if controller is None:
    #     return

    # bot = _players[command.index]['bot'] = Player(index_from_edict(bot_edict))
    # _players[command.index]['controller'] = controller

    main_menu.send(command.index)

    avsdplayer = AVSDPlayer.from_index(command.index)

    avsdplayer.data['_wings_is_flying'] = False

    inthandle = avsdplayer.data.pop('_wings', None)

    if inthandle is not None:
        try:
            index = index_from_inthandle(inthandle)
        except ValueError:
            pass
        else:
            BaseEntity(index).remove()

    # bot.team_index = avsdplayer.player.team_index
    # bot.spawn(force=True)

    # bot.godmode = True

    return CommandReturn.BLOCK


@main_menu.register_select_callback
def main_menu_select(menu, client, option):
    _players[client]['model'] = option.value

    avsdplayer = AVSDPlayer.from_index(client)

    avsdplayer.data['_wings_is_flying'] = False

    inthandle = avsdplayer.data.pop('_wings', None)

    if inthandle is not None:
        try:
            index = index_from_inthandle(inthandle)
        except ValueError:
            pass
        else:
            BaseEntity(index).remove()

    data = wings_info[option.value]

    entity = spawn_wings2(avsdplayer.player, data, wings_models[option.value])

    avsdplayer.data['_wings'] = entity.inthandle

    return axis_menu


@axis_menu.register_select_callback
def axis_menu_select(menu, client, option):
    _players[client]['axis'] = option.value[0]
    _players[client]['key'] = option.value[1]
    _players[client]['index'] = option.value[2]
    return values_menu


@values_menu.register_select_callback
def values_menu_select(menu, client, option):
    avsdplayer = AVSDPlayer.from_index(client)

    inthandle = avsdplayer.data.get('_wings')

    if inthandle is None:
        SayText2('No wings found.').send(client)
        return

    try:
        index = index_from_inthandle(inthandle)
    except ValueError:
        SayText2('No wings found.').send(client)
        return
    else:
        entity = Entity(index)

    data = _players[client]

    wings_info[data['model']][data['key']][data['index']] = round(option.value + float(wings_info[data['model']][data['key']][data['index']]), 1)

    wings_info.write()

    update_position(avsdplayer.player, wings_info[data['model']], entity)

    return values_menu


@values_menu.register_build_callback
def values_menu_build(menu, client):
    data = _players[client]
    menu.description = 'Value: {0}'.format(wings_info[data['model']][data['key']][data['index']])


@main_menu.register_close_callback
@axis_menu.register_close_callback
@values_menu.register_close_callback
def menu_close(menu, client):
    # _players[client]['controller'].remove_all_items(True)
    # _players[client]['bot'].kick()

    del _players[client]

    avsdplayer = AVSDPlayer.from_index(client)
    inthandle = avsdplayer.data.get('_wings')

    if inthandle is not None:
        try:
            index = index_from_inthandle(inthandle)
        except ValueError:
            pass
        else:
            BaseEntity(index).remove()

    wings = avsdplayer.stats.get('wings')

    if wings is None:
        return

    instance = class_manager[avsdplayer.current_class]

    wing_model = instance.settings.config['wings_model']

    if not isinstance(wing_model, str):
        wing_model = wing_model[wings - 1]

    data = wings_info[wing_model]

    entity = spawn_wings2(avsdplayer.player, data, wings_models[wing_model])
    entity.color = entity.color.with_alpha(0)

    avsdplayer.data['_wings'] = entity.inthandle


def spawn_wings2(player, data, model):
    entity = Entity.create('prop_dynamic_override')
    entity.model = model

    update_position(player, data, entity)

    entity.spawn()

    entity.set_key_value_int('disableshadows', 1)
    entity.set_key_value_int('disablereceiveshadows', 1)

    entity.set_parent(player, player.lookup_attachment('facemask'))

    return entity


def update_position(player, data, entity):
    origin = player.playerinfo.origin
    angles = player.playerinfo.angles

    # print(angles)

    offset = Vector(*[float(x) for x in data['position']])
    angles += QAngle(*[float(x) for x in data['angles']])

    forward, right, up = AngleVectors(angles)

    origin[0] += right[0] * offset[0] + forward[0] * offset[1] + up[0] * offset[2]
    origin[1] += right[1] * offset[0] + forward[1] * offset[1] + up[1] * offset[2]
    origin[2] += right[2] * offset[0] + forward[2] * offset[1] + up[2] * offset[2]

    origin.z += 52

    entity.clear_parent()

    entity.origin = origin
    entity.angles = angles

    # entity.teleport(origin=origin, angle=angles)

    entity.set_parent(player, player.lookup_attachment('facemask'))


@OnPluginUnload
def on_unload():
    for index in _players:
        avsdplayer = AVSDPlayer.from_index(index)
        inthandle = avsdplayer.data.get('_wings')

        if inthandle is not None:
            try:
                index = index_from_inthandle(inthandle)
            except ValueError:
                pass
            else:
                BaseEntity(index).remove()

        # _players[index]['controller'].remove_all_items(True)
        # _players[index]['bot'].kick()


# @OnPlayerDelete
# def on_delete(avsdplayer):
#     data = _players.pop(avsdplayer.index, None)

#     if data is not None:
#         data['controller'].remove_all_items(True)
#         data['bot'].kick()


@OnPlayerFlyUpdatePre
def pre_fly(avsdplayer, data):
    if data['state']:
        if avsdplayer.index in _players:
            data['allow'] = False
