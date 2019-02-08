# ../avsd/modules/classes/lucifer.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Enum
from enum import IntEnum
#   Random
from random import choice
from random import randint
#   Time
from time import time

# Source.Python Imports
#   CVars
from cvars import cvar
#   Engines
from engines.trace import ContentMasks
from engines.trace import engine_trace
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
#   Entities
from entities.constants import MoveType
from entities.entity import Entity
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
from filters.weapons import WeaponClassIter
#   Listeners
from listeners.tick import Delay
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Mathlib
from mathlib import NULL_VECTOR
from mathlib import Vector
#   Memory
from memory import make_object
#   Menus
from menus import SimpleMenu
from menus import SimpleOption
from menus import Text
#   Messages
from messages import Shake
#   Players
from players.constants import PlayerButtons
from players.constants import PlayerStates
from players.entity import Player
from players.helpers import index_from_userid

# AvsD Imports
#   Area
from ...core.area.aura import Aura
from ...core.area.aura import aura_manager
from ...core.area.zone import SphereZone
from ...core.area.zone import SquareZone
from ...core.area.zone import zone_manager
#   Helpers
# from ...core.helpers.math import AngleVectors
from ...core.helpers.math import ConeChecker
from ...core.helpers.particle import Particle
from ...core.helpers.skillshot import Skillshot
#   Listeners
from ...core.listeners import OnPlayerAttackPost
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerFlyUpdatePre
from ...core.listeners import OnPlayerReset
from ...core.listeners import OnPlayerStartTouch
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnPlayerUIBuffPre
from ...core.listeners import OnPluginUnload
from ...core.listeners import OnTakeDamage
#   Menus
from ...core.menus import ability_menu
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer
from ...core.players.filters import PlayerIter as AVSDPlayerIter
#   Translations
from ...core.translations import menu_strings


# ============================================================================
# >> CLASSES
# ============================================================================
class Pyrokenisis(IntEnum):
    HELLFIRE = 0
    FIREBOLT = 1
    FIRE_NOVA = 2
    FIRESTORM = 3
    FLAME_WALL = 4
    SCORCHED_GROUND = 5
    FLAME_TORNADO = 6


class HellfireAura(Aura):
    owner_particle = Particle('_Class_Lucifer_Pyrokenisis_Hellfire')
    update_interval = 0.5

    def on_enter_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if Pyrokenisis.HELLFIRE not in avsdtarget.data['pyrokenisis']:
            avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE] = {}

        if 'targets' not in avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE]:
            avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE]['targets'] = []

        avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE]['targets'].append(self)

        if len(avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE]['targets']) == 1:
            self.on_update_aura(target)

    def on_update_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE].get('targets'):
            if avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE]['targets'][0] == self:
                damage = self.data['damage']

                if self.owner.data['challenge'].get('active', False):
                    damage += self.owner.data['challenge']['hellfire_damage']

                avsdtarget.take_damage(damage, self.owner.index, settings.name, 'Pyrokenisis_Hellfire Aura')

    def on_exit_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        avsdtarget.data['pyrokenisis'][Pyrokenisis.HELLFIRE]['targets'].remove(self)


class FireboltSkillshot(Skillshot):
    particle = Particle('_Class_Lucifer_Pyrokenisis_Firebolt')

    def on_start_touch(self, other):
        if other.class_name == 'player':
            if other.team_index != self.data['team']:
                avsdplayer = AVSDPlayer.from_index(other.index)

                avsdplayer.take_delayed_damage(self.data['initial_damage'], self.owner.index, settings.name, 'Firebolt')

                if Pyrokenisis.FIREBOLT not in avsdplayer.data['pyrokenisis']:
                    avsdplayer.data['pyrokenisis'][Pyrokenisis.FIREBOLT] = {}

                repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FIREBOLT]['repeat'] = Repeat(deal_damage, args=(avsdplayer.userid, self.owner.userid, self.data['damage']))
                repeat.args += (repeat, )
                repeat.start(1, 2)

        return True


class FlameWallZone(SquareZone):
    zone_particle = Particle('_Class_Lucifer_Pyrokenisis_Wall')

    def on_enter_zone(self, player):
        avsdtarget = AVSDPlayer.from_index(player.index)

        if Pyrokenisis.FLAME_WALL not in avsdtarget.data['pyrokenisis']:
            avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_WALL] = {}

        if 'targets' not in avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_WALL]:
            avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_WALL]['targets'] = []

        if self not in avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_WALL]['targets']:
            avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_WALL]['targets'].append(self)

            avsdtarget.take_damage(self.data['damage'], self.owner.index, settings.name, 'Pyrokenisis_Flame Wall')

    def on_remove_zone(self):
        for index in self.entities:
            avsdtarget = AVSDPlayer.from_index(index)

            avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_WALL]['targets'].remove(self)


class ScorchedGroundZone(SphereZone):
    zone_particle = Particle('_Class_Lucifer_Pyrokenisis_Scorched_Ground')

    def on_enter_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if Pyrokenisis.SCORCHED_GROUND not in avsdplayer.data['pyrokenisis']:
            avsdplayer.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND] = {}

        if 'grounds' not in avsdplayer.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]:
            avsdplayer.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]['grounds'] = []

        if self not in avsdplayer.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]['grounds']:
            avsdplayer.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]['grounds'].append(self)

            self.on_update_zone(player)

    def on_update_zone(self, player):
        avsdtarget = AVSDPlayer.from_index(player.index)

        if Pyrokenisis.SCORCHED_GROUND in avsdtarget.data['pyrokenisis'] and 'grounds' in avsdtarget.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]:
            if avsdtarget.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]['grounds'][0] == self:
                avsdtarget.take_damage(randint(self.data['min_damage'], self.data['max_damage']), index_from_userid(self.data['attacker']), settings.name, 'Pyrokenisis_Scorched Ground')

    def on_exit_zone(self, player):
        avsdtarget = AVSDPlayer.from_index(player.index)

        avsdtarget.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]['grounds'].remove(self)


class ChallengeZone(SphereZone):
    zone_particle = Particle('_Class_Lucifer_Challenge')

    def on_enter_zone(self, player):
        if player.index == self.owner.index:
            self.owner.data['challenge']['active'] = True

            self.on_update_zone(player)

    def on_update_zone(self, player):
        if player.index == self.owner.index:
            self.owner.data['challenge']['active'] = True
            skill = self.owner.skills['challenge']
            percentage = skill.level / skill.max

            left_click_min = skill['left_click_min']
            left_click_max = skill['left_click_max']
            right_click_min = skill['right_click_min']
            right_click_max = skill['right_click_max']
            pulsating_fire_min = skill['pulsating_fire_min']
            pulsating_fire_max = skill['pulsating_fire_max']
            hellfire_damage_min = skill['pyrokenisis_hellfire_damage_min']
            hellfire_damage_max = skill['pyrokenisis_hellfire_damage_max']
            firebolt_initial_damage_min = skill['pyrokenisis_firebolt_initial_damage_min']
            firebolt_initial_damage_max = skill['pyrokenisis_firebolt_initial_damage_max']
            firebolt_damage_min = skill['pyrokenisis_firebolt_damage_min']
            firebolt_damage_max = skill['pyrokenisis_firebolt_damage_max']
            fire_nova_inner = skill['pyrokenisis_fire_nova_inner']
            fire_nova_medium = skill['pyrokenisis_fire_nova_medium']
            fire_nova_outer = skill['pyrokenisis_fire_nova_outer']
            firestorm_min_damage_min = skill['pyrokenisis_firestorm_min_damage_min']
            firestorm_max_damage_min = skill['pyrokenisis_firestorm_max_damage_min']
            firestorm_min_damage_max = skill['pyrokenisis_firestorm_min_damage_max']
            firestorm_max_damage_max = skill['pyrokenisis_firestorm_max_damage_max']
            flame_wall_damage_min = skill['pyrokenisis_flame_wall_damage_min']
            flame_wall_damage_max = skill['pyrokenisis_flame_wall_damage_max']
            scorched_ground_min_damage_min = skill['pyrokenisis_scorched_ground_min_damage_min']
            scorched_ground_max_damage_min = skill['pyrokenisis_scorched_ground_max_damage_min']
            scorched_ground_min_damage_max = skill['pyrokenisis_scorched_ground_min_damage_max']
            scorched_ground_max_damage_max = skill['pyrokenisis_scorched_ground_max_damage_max']

            left_click = percentage * (left_click_max - left_click_min) + left_click_min
            right_click = percentage * (right_click_max - right_click_min) + right_click_min
            pulsating_fire = percentage * (pulsating_fire_max - pulsating_fire_min) + pulsating_fire_min
            hellfire_damage = percentage * (hellfire_damage_max - hellfire_damage_min) + hellfire_damage_min
            firebolt_initial_damage = percentage * (firebolt_initial_damage_max - firebolt_initial_damage_min) + firebolt_initial_damage_min
            firebolt_damage = percentage * (firebolt_damage_max - firebolt_damage_min) + firebolt_damage_min
            firestorm_min_damage = percentage * (firestorm_max_damage_min - firestorm_min_damage_min) + firestorm_min_damage_min
            firestorm_max_damage = percentage * (firestorm_max_damage_max - firestorm_min_damage_max) + firestorm_min_damage_max
            flame_wall_damage = percentage * (flame_wall_damage_max - flame_wall_damage_min) + flame_wall_damage_min
            scorched_ground_min_damage = percentage * (scorched_ground_max_damage_min - scorched_ground_min_damage_min) + scorched_ground_min_damage_min
            scorched_ground_max_damage = percentage * (scorched_ground_max_damage_max - scorched_ground_min_damage_max) + scorched_ground_min_damage_max

            self.owner.data['challenge']['left_click'] = left_click
            self.owner.data['challenge']['right_click'] = right_click
            self.owner.data['challenge']['pulsating_fire'] = pulsating_fire
            self.owner.data['challenge']['hellfire_damage'] = hellfire_damage
            self.owner.data['challenge']['firebolt_initial_damage'] = firebolt_initial_damage
            self.owner.data['challenge']['firebolt_damage'] = firebolt_damage
            self.owner.data['challenge']['fire_nova_inner'] = fire_nova_inner
            self.owner.data['challenge']['fire_nova_medium'] = fire_nova_medium
            self.owner.data['challenge']['fire_nova_outer'] = fire_nova_outer
            self.owner.data['challenge']['firestorm_min_damage'] = round(firestorm_min_damage)
            self.owner.data['challenge']['firestorm_max_damage'] = round(firestorm_max_damage)
            self.owner.data['challenge']['flame_wall_damage'] = flame_wall_damage
            self.owner.data['challenge']['scorched_ground_min_damage'] = scorched_ground_min_damage
            self.owner.data['challenge']['scorched_ground_max_damage'] = scorched_ground_max_damage

    def on_exit_zone(self, player):
        if player.index == self.owner.index:
            self.owner.data['challenge']['active'] = False

    def on_remove_zone(self):
        self.owner.data['challenge']['active'] = False


class UnholyAura(Aura):
    owner_particle = Particle('_Class_Lucifer_Unholy_Aura')

    def on_update_aura(self, target):
        AVSDPlayer.from_index(target.index).take_damage(self.data['damage'], self.owner.index, settings.name, 'pyrokenisis_unholy aura')


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
melee_weapons = [x.name for x in WeaponClassIter('melee')]
_class_lucifer_pulsating_fire = [Particle('_Class_Lucifer_Pulsating_Fire_1', lifetime=5), Particle('_Class_Lucifer_Pulsating_Fire_2', lifetime=5)]
_class_lucifer_pyrokenisis_nova = Particle('_Class_Lucifer_Pyrokenisis_Nova', lifetime=5)
_class_lucifer_pyrokenisis_firestorm = Particle('_Class_Lucifer_Pyrokenisis_Firestorm', lifetime=5)
_class_lucifer_pyrokenisis_flametornado = Particle('_Class_Lucifer_Pyrokenisis_Flametornado', lifetime=7)
_class_lucifer_decendant = Particle('_Class_Lucifer_Decendant', lifetime=5)
_class_lucifer_embers_grasp = Particle('_Class_Lucifer_Embers_Grasp', lifetime=5)

menu = SimpleMenu(
    [
        Text(settings.strings['menu title']),
        ' ',
        SimpleOption(1, settings.strings['menu line 1'], Pyrokenisis.HELLFIRE),
        SimpleOption(2, settings.strings['menu line 2'], Pyrokenisis.FIREBOLT),
        SimpleOption(3, settings.strings['menu line 3'], Pyrokenisis.FIRE_NOVA),
        SimpleOption(4, settings.strings['menu line 4'], Pyrokenisis.FIRESTORM),
        SimpleOption(5, settings.strings['menu line 5'], Pyrokenisis.FLAME_WALL),
        SimpleOption(6, settings.strings['menu line 6'], Pyrokenisis.SCORCHED_GROUND),
        SimpleOption(7, settings.strings['menu line 7'], Pyrokenisis.FLAME_TORNADO),
        SimpleOption(8, menu_strings['back'], ability_menu),
        SimpleOption(9, menu_strings['close'], highlight=False),
    ])

_gotuw = set()

sv_clamp_unsafe_velocities = cvar.find_var('sv_clamp_unsafe_velocities')

if sv_clamp_unsafe_velocities.get_int():
    from warnings import warn
    warn("Lucifer's Heaven's Descendant might not work correctly. Disable 'sv_clamp_unsafe_velocities' for it to function properly.")


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_death')
def player_death(event):
    userid = event['userid']
    avsdplayer = AVSDPlayer.from_userid(userid)

    if Pyrokenisis.FIREBOLT in avsdplayer.data['pyrokenisis']:
        repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FIREBOLT].get('repeat')

        if repeat is not None:
            if repeat.status == RepeatStatus.RUNNING:
                repeat.stop()

    if Pyrokenisis.HELLFIRE in avsdplayer.data['pyrokenisis']:
        delay = avsdplayer.data['pyrokenisis'][Pyrokenisis.HELLFIRE].get('delay')

        if delay is not None:
            if delay.running:
                delay()

    if avsdplayer.current_class == settings.name:
        delay = avsdplayer.data['unholy aura'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        delay = avsdplayer.data['grasp of the underworld'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        if avsdplayer.data['grasp of the underworld'].get('active'):
            avsdplayer.state['stuck'] -= 1

            avsdplayer.data['grasp of the underworld']['active'] = False

            player = avsdplayer.player

            player.color = player.color.with_alpha(255)

            # _gotuw.discard(player.index)
            _gotuw.discard(avsdplayer)


@Event('round_prestart')
def round_prestart(event):
    for _, avsdplayer in AVSDPlayerIter('alive'):
        delay = avsdplayer.data['grasp of the underworld'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        on_player_delete(avsdplayer)

        if Pyrokenisis.FLAME_WALL in avsdplayer.data['pyrokenisis']:
            delay = avsdplayer.data['pyrokenisis'][Pyrokenisis.FLAME_WALL].get('delay')

            if delay is not None:
                if delay.running:
                    delay()

        delay = avsdplayer.data['unholy aura'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        if avsdplayer.data['grasp of the underworld'].get('active'):
            avsdplayer.state['stuck'] -= 1

            avsdplayer.data['grasp of the underworld']['active'] = False

            player = avsdplayer.player

            player.color = player.color.with_alpha(255)

            # _gotuw.discard(player.index)
            _gotuw.discard(avsdplayer)


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def firestorm_deal_damage(avsdplayer, distance, min_damage, max_damage, repeat):
    try:
        player = avsdplayer.player
    except ValueError:
        from warnings import warn
        warn('Repeat should have been stopped')
        repeat.stop()
    else:
        attacker = player.index
        # origin = player.eye_location
        # eye_angle = player.eye_angle

        if avsdplayer.data['challenge'].get('active', False):
            min_damage += avsdplayer.data['challenge']['firestorm_min_damage']
            max_damage += avsdplayer.data['challenge']['firestorm_max_damage']

        # forward = Vector(*AngleVectors(eye_angle)[0])

        cone = ConeChecker(player, distance)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            if cone.has_within(target.eye_location):
                AVSDPlayer.from_index(target.index).take_damage(randint(min_damage, max_damage), attacker, settings.name, 'pyrokenisis_firestorm')

            # target_origin = target.eye_location

            # if origin.get_distance_sqr(target_origin) <= distance ** 2:
            #     segment = target_origin - origin
            #     segment.normalize()

            #     if forward.dot(segment) >= 0.8:


def flame_tornado_pully(attacker, team, origin, radius, damage):
    for target in PlayerIter(['alive', 'ct' if team == 2 else 't']):
        distance = origin.get_distance_sqr(target.origin)

        if distance <= radius ** 2:
            # TODO: Check if this is still valid
            target.base_velocity = (origin - target.origin) / (distance / radius) * 2

            avsdtarget = AVSDPlayer.from_index(target.index)

            if Pyrokenisis.FLAME_TORNADO not in avsdtarget.data['pyrokenisis']:
                avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_TORNADO] = {}

            repeat = avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_TORNADO].get('damage_repeat')

            if repeat is not None:
                if repeat.status == RepeatStatus.RUNNING:
                    continue

            repeat = avsdtarget.data['pyrokenisis'][Pyrokenisis.FLAME_TORNADO]['damage_repeat'] = Repeat(deal_damage, args=(avsdtarget.userid, attacker, damage))
            repeat.args += (repeat, )
            repeat.start(0.5, 8)


def deal_damage(victim, attacker, damage, repeat):
    try:
        player = Player.from_userid(victim)
    except ValueError:
        from warnings import warn
        warn('Repeat should have been stopped')
        repeat.stop()
    else:
        if not player.dead:
            try:
                attacker = index_from_userid(attacker)
            except ValueError:
                attacker = 0

            AVSDPlayer.from_index(player.index).take_damage(damage, attacker, settings.name, 'pyrokenisis_flame tornado')


def heavens_descendant_push(userid, target_origin):
    player = Player.from_userid(userid)

    origin = player.origin

    diff = target_origin - origin
    length = diff.length
    diff.normalize()
    diff *= length / 1.5

    player.base_velocity = diff


def grasp_of_the_underworld_unfreeze(avsdtarget):
    avsdtarget.state['stuck'] -= 1


def _dyncall_pulsating_fire(avsdplayer, player):
    if avsdplayer.current_class == settings.name:
        skill = avsdplayer.skills['pulsating fire']
        level = skill.level

        if level:
            distance = skill['distance']
            min_damage = skill['min_damage']
            max_damage = skill['max_damage']

            damage = (level / skill.max) * (max_damage - min_damage) + min_damage

            if avsdplayer.data['challenge'].get('active', False):
                damage *= 1 + avsdplayer.data['challenge']['pulsating_fire']

            origin = player.origin

            choice(_class_lucifer_pulsating_fire).create(origin)

            for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
                if origin.get_distance_sqr(target.origin) <= distance ** 2:
                    AVSDPlayer.from_index(target.index).take_damage(damage, player.index, settings.name, 'pulsating fire')


# ============================================================================
# >> LISTENERS
# ============================================================================
# TODO: Check if this is where the Vector::DistTo crashes
@OnPlayerAttackPost
def on_player_attack_post(avsdplayer, player, weapon, is_attack1):
    if avsdplayer.current_class == settings.name:
        if weapon.class_name in melee_weapons:
            player.delay(0, _dyncall_pulsating_fire, args=(avsdplayer, player))


@OnPlayerDelete
def on_player_delete(avsdplayer):
    if Pyrokenisis.FIREBOLT in avsdplayer.data['pyrokenisis']:
        repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FIREBOLT].get('repeat')

        if repeat is not None:
            if repeat.status == RepeatStatus.RUNNING:
                repeat.stop()

    on_player_reset(avsdplayer)


@OnPlayerFlyUpdatePre
def on_player_fly_update_pre(avsdplayer, data):
    if avsdplayer.current_class == settings.name:
        # if avsdplayer.index in _gotuw or avsdplayer.data['grasp of the underworld'].get('active'):
        if avsdplayer in _gotuw or avsdplayer.data['grasp of the underworld'].get('active'):
            data['allow'] = False
        elif avsdplayer.data['heavens descendant'].get('active'):
            data['allow'] = False


@OnPlayerReset
def on_player_reset(avsdplayer):
    if avsdplayer.current_class == settings.name:
        if Pyrokenisis.HELLFIRE in avsdplayer.data['pyrokenisis']:
            delay = avsdplayer.data['pyrokenisis'][Pyrokenisis.HELLFIRE].get('delay')

            if delay is not None:
                if delay.running:
                    delay()

        if Pyrokenisis.FIRESTORM in avsdplayer.data['pyrokenisis']:
            repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FIRESTORM].get('repeat')

            if repeat is not None:
                if repeat.status == RepeatStatus.RUNNING:
                    repeat.stop()

        delay = avsdplayer.data['heavens descendant'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

        avsdplayer.data['heavens descendant']['active'] = False

        delay = avsdplayer.data['unholy aura'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        delay = avsdplayer.data['grasp of the underworld'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

        delay = avsdplayer.data['challenge'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        _gotuw.discard(avsdplayer)


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if old == settings.name:
        if Pyrokenisis.HELLFIRE in avsdplayer.data['pyrokenisis']:
            delay = avsdplayer.data['pyrokenisis'][Pyrokenisis.HELLFIRE].get('delay')

            if delay is not None:
                if delay.running:
                    delay()

        if Pyrokenisis.FIRESTORM in avsdplayer.data['pyrokenisis']:
            repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FIRESTORM].get('repeat')

            if repeat is not None:
                if repeat.status == RepeatStatus.RUNNING:
                    repeat.stop()

        delay = avsdplayer.data['heavens descendant'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

        avsdplayer.data['heavens descendant']['active'] = False

        delay = avsdplayer.data['unholy aura'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        delay = avsdplayer.data['grasp of the underworld'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

        delay = avsdplayer.data['challenge'].get('delay')

        if delay is not None:
            if delay.running:
                delay()


@OnPlayerUIBuffPre
def on_player_buff_pre(avsdplayer, class_, language, messages, now):
    if class_.name == settings.name:
        if avsdplayer.data['challenge'].get('active'):
            messages.append(settings.strings['ui challenge'].get_string(language))


@OnPluginUnload
def on_plugin_unload():
    for player, avsdplayer in AVSDPlayerIter():
        on_player_delete(avsdplayer)

        if Pyrokenisis.HELLFIRE in avsdplayer.data['pyrokenisis']:
            delay = avsdplayer.data['pyrokenisis'][Pyrokenisis.HELLFIRE].get('delay')

            if delay is not None:
                if delay.running:
                    delay()

        if Pyrokenisis.FLAME_WALL in avsdplayer.data['pyrokenisis']:
            delay = avsdplayer.data['pyrokenisis'][Pyrokenisis.FLAME_WALL].get('delay')

            if delay is not None:
                if delay.running:
                    delay()

        if avsdplayer.data['grasp of the underworld'].get('active'):
            player.color = player.color.with_alpha(255)


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class PyrokenisisAbility(Ability):
    name = 'pyrokenisis'

    def activate(self, avsdplayer, skill, player, now):
        if avsdplayer._is_bot:
            return

        if ability_menu.is_active_menu(player.index):
            ability_menu.close(player.index)

        if menu.is_active_menu(player.index):
            menu.close(player.index)
        else:
            menu.send(player.index)


@settings.ability
class ChallengeAbility(Ability):
    name = 'challenge'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        distance = skill['distance']
        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

        avsdplayer.data[self.name]['cooldown'] = now + cooldown

        zone = ChallengeZone(avsdplayer, origin, distance)

        zone_manager.append(zone)

        avsdplayer.data[self.name]['delay'] = Delay(10, zone_manager.remove, args=(zone, ))


@settings.ability
class HeavensDescendantAbility(Ability):
    name = 'heavens descendant'

    def activate(self, avsdplayer, skill, player, now):
        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

        avsdplayer.data[self.name]['cooldown'] = now + cooldown

        origin = player.origin
        view_vector = player.view_vector

        view_vector[2] = 0
        view_vector *= 200

        behind = origin - view_vector

        behind[2] += 500

        ray = Ray(origin, behind)
        trace = GameTrace()

        engine_trace.trace_ray(ray, ContentMasks.ALL, TraceFilterSimple(PlayerIter()), trace)

        if trace.did_hit():
            behind = trace.end_position

        if avsdplayer.flying:
            avsdplayer.flying = False

        player.base_velocity = (behind - origin) / 1.5

        avsdplayer.data[self.name]['delay'] = Delay(0.2, heavens_descendant_push, args=(avsdplayer.userid, player.get_view_coordinates()))
        avsdplayer.data[self.name]['active'] = True


@settings.ability
class GraspOfTheUnderworldAbility(Ability):
    name = 'grasp of the underworld'

    def activate(self, avsdplayer, skill, player, now):
        if avsdplayer.data[self.name].get('active'):
            avsdplayer.state['stuck'] -= 1

            avsdplayer.data[self.name]['active'] = False

            avsdplayer.data[self.name]['cooldown'] = now + skill['grasp_cooldown']

            player.color = player.color.with_alpha(255)
            player.set_property_vector('m_vecAbsVelocity', NULL_VECTOR)
            player.move_type = MoveType.WALK

            # _gotuw.discard(player.index)
            _gotuw.discard(avsdplayer)

            return

        distance = skill['root_distance']

        target_origin = player.get_view_coordinates()

        _class_lucifer_embers_grasp.create(target_origin)

        targets = []

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            if target.origin.get_distance_sqr(target_origin) < distance ** 2:
                targets.append(target)

        if targets:
            target = choice(targets)

            avsdtarget = AVSDPlayer.from_index(target.index)

            delay = avsdtarget.data[self.name].get('delay')

            if delay is not None and delay.running:
                delay.cancel()
            else:
                avsdtarget.state['stuck'] += 1

            avsdtarget.data[self.name]['delay'] = Delay(2, grasp_of_the_underworld_unfreeze, args=(avsdtarget, ))

            avsdplayer.data[self.name]['cooldown'] = now + skill['root_cooldown']
        else:
            if avsdplayer.flying:
                avsdplayer.flying = False

            player.move_type = MoveType.FLY

            origin = player.eye_location

            # _gotuw.add(player.index)
            _gotuw.add(avsdplayer)

            player.set_property_vector('m_vecAbsVelocity', target_origin - origin)

    def get_cooldown(self, avsdplayer):
        return 0 if avsdplayer.data[self.name].get('active') else super().get_cooldown(avsdplayer)


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        if avsdvictim.current_class == settings.name:
            info.damage = 0

        return

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            player = Player(info.attacker)

            skill = avsdattacker.passives['damage']

            info.damage *= skill['multiplier']

            if avsdattacker.data['challenge'].get('active', False):
                if player.buttons & PlayerButtons.ATTACK:
                    info.damage = avsdattacker.data['challenge']['left_click']
                elif player.buttons & PlayerButtons.ATTACK2:
                    info.damage = avsdattacker.data['challenge']['right_click']

            active_weapon = player.active_weapon

            if active_weapon.class_name in melee_weapons:
                # For item Armour of Vengefulness
                reduction = skill.stats.get('reduction')

                if reduction is not None:
                    avsdattacker.data['damage']['duration'] = now + 2

                skill = avsdattacker.skills['unholy aura']
                level = skill.level

                if level:
                    now = time()

                    if avsdattacker.data['unholy aura'].get('cooldown', 0) <= now:
                        cooldown = skill['cooldown']

                        avsdattacker.data['unholy aura']['cooldown'] = now + cooldown

                        min_damage = skill['min_damage']
                        max_damage = skill['max_damage']

                        damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage

                        aura = UnholyAura(avsdattacker, skill['distance'], team=player.team_index, damage=damage)

                        aura_manager.append(aura)

                        avsdattacker.data['unholy aura']['delay'] = Delay(10, aura_manager.remove, args=(aura, ))

    # For item Armour of Vengefulness
    if avsdvictim.ready:
        if avsdvictim.current_class == settings.name:
            if avsdvictim.data['damage'].get('duration', 0) >= now:
                reduction = avsdvictim.passives['damage'].get('reduction')

                if reduction is not None:
                    info.damage = max(info.damage - reduction, 5)


@OnPlayerStartTouch
def on_player_start_touch(avsdplayer, other, grounded):
    if grounded:
        # if avsdplayer.index in _gotuw:
        if avsdplayer in _gotuw:
            avsdplayer.data['grasp of the underworld']['active'] = True

            avsdplayer.state['stuck'] += 1

            entity = Entity(avsdplayer.index)
            entity.color = entity.color.with_alpha(34)

            # _gotuw.discard(avsdplayer.index)
            _gotuw.discard(avsdplayer)
    else:
        if avsdplayer.data['heavens descendant'].get('active'):
            assert avsdplayer.current_class == settings.name

            delay = avsdplayer.data['heavens descendant']['delay']

            if delay.running:
                delay.cancel()

            avsdplayer.data['heavens descendant']['active'] = False

            skill = avsdplayer.skills['heavens descendant']

            distance = skill['distance']
            min_damage = skill['min_damage']
            max_damage = skill['max_damage']
            min_shake = skill['min_shake']
            max_shake = skill['max_shake']

            damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage
            shake = (skill.level / skill.max) * (max_shake - min_shake) + min_shake

            attacker = avsdplayer.index
            entity = Entity(attacker)
            origin = entity.origin

            for target in PlayerIter(['alive', 'ct' if entity.team_index == 2 else 't']):
                if target.origin.get_distance_sqr(origin) < distance ** 2:
                    AVSDPlayer.from_index(target.index).take_delayed_damage(damage, attacker, settings.name, 'heavens descendant')

                    Shake(amplitude=shake, duration=0.5).send(target.index)

            _class_lucifer_decendant.create(origin)


# # TODO: Check if this is where the Vector::DistTo crashes
# @EntityPreHook(EntityCondition.is_player, 'start_touch')
# def start_touch(stack):
#     entity = make_object(Entity, stack[0])

#     if entity.is_player():
#         if entity.flags & PlayerStates.ONGROUND or entity.ground_entity != -1:
#             avsdplayer = AVSDPlayer.from_index(entity.index)

#             if avsdplayer.ready:
#                 if avsdplayer.data['heavens descendant'].get('active'):
#                     assert avsdplayer.current_class == settings.name

#                     delay = avsdplayer.data['heavens descendant']['delay']

#                     if delay.running:
#                         delay.cancel()

#                     avsdplayer.data['heavens descendant']['active'] = False

#                     skill = avsdplayer.skills['heavens descendant']

#                     distance = skill['distance']
#                     min_damage = skill['min_damage']
#                     max_damage = skill['max_damage']
#                     min_shake = skill['min_shake']
#                     max_shake = skill['max_shake']

#                     damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage
#                     shake = (skill.level / skill.max) * (max_shake - min_shake) + min_shake

#                     attacker = entity.index
#                     origin = entity.origin

#                     for target in PlayerIter(['alive', 'ct' if entity.team_index == 2 else 't']):
#                         if target.origin.get_distance_sqr(origin) < distance ** 2:
#                             AVSDPlayer.from_index(target.index).take_delayed_damage(damage, attacker, settings.name, 'heavens descendant')

#                             Shake(amplitude=shake, duration=0.5).send(target.index)

#                     _class_lucifer_decendant.create(origin)

#         if entity.index in _gotuw:
#             avsdplayer = AVSDPlayer.from_index(entity.index)

#             if avsdplayer.ready:
#                 avsdplayer.data['grasp of the underworld']['active'] = True

#                 avsdplayer.state['stuck'] += 1

#                 entity.color = entity.color.with_alpha(34)

#                 _gotuw.discard(entity.index)


# ============================================================================
# >> MENUS
# ============================================================================
@menu.register_select_callback
def menu_select(menu, client, option):
    if option.choice_index == 8:
        return option.value

    ability = option.value

    avsdplayer = AVSDPlayer.from_index(client)

    assert avsdplayer.current_class == settings.name

    skill = avsdplayer.skills['pyrokenisis']

    if ability not in avsdplayer.data['pyrokenisis']:
        avsdplayer.data['pyrokenisis'][ability] = {}

    if ability == Pyrokenisis.HELLFIRE:
        min_damage = skill['hellfire_min_damage']
        max_damage = skill['hellfire_max_damage']

        damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage

        aura = HellfireAura(avsdplayer, skill['hellfire_distance'], team=5 - avsdplayer.player.team_index, damage=damage)

        aura_manager.append(aura)

        avsdplayer.data['pyrokenisis'][Pyrokenisis.HELLFIRE]['delay'] = Delay(3, aura_manager.remove, args=(aura, ))

        cooldown = skill['hellfire_cooldown']
    elif ability == Pyrokenisis.FIREBOLT:
        initial_damage = skill['firebolt_initial_damage']
        min_damage = skill['firebolt_min_damage']
        max_damage = skill['firebolt_max_damage']

        damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage

        if avsdplayer.data['challenge'].get('active', False):
            initial_damage += avsdplayer.data['challenge']['firebolt_initial_damage']
            damage += avsdplayer.data['challenge']['firebolt_damage']

        player = avsdplayer.player

        FireboltSkillshot(avsdplayer, team=player.team_index, attacker=avsdplayer.userid, initial_damage=initial_damage, damage=damage)

        cooldown = skill['firebolt_cooldown']
    elif ability == Pyrokenisis.FIRE_NOVA:
        inner_distance = skill['fire_nova_inner_distance']
        medium_distance = skill['fire_nova_medium_distance']
        outer_distance = skill['fire_nova_outer_distance']
        inner_damage = skill['fire_nova_inner_damage']
        medium_damage = skill['fire_nova_medium_damage']
        outer_damage = skill['fire_nova_outer_damage']

        if avsdplayer.data['challenge'].get('active', False):
            inner_damage += avsdplayer.data['challenge']['fire_nova_inner']
            medium_damage += avsdplayer.data['challenge']['fire_nova_medium']
            outer_damage += avsdplayer.data['challenge']['fire_nova_outer']

        player = avsdplayer.player

        origin = player.origin

        _class_lucifer_pyrokenisis_nova.create(origin)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            distance = target.origin.get_distance_sqr(origin)

            if distance <= inner_distance ** 2:
                AVSDPlayer.from_index(target.index).take_damage(inner_distance, client, settings.name, 'pyrokenisis_fire nova')
            elif distance <= medium_distance ** 2:
                AVSDPlayer.from_index(target.index).take_damage(medium_distance, client, settings.name, 'pyrokenisis_fire nova')
            elif distance <= outer_distance ** 2:
                AVSDPlayer.from_index(target.index).take_damage(outer_distance, client, settings.name, 'pyrokenisis_fire nova')

        cooldown = skill['fire_nova_cooldown']
    elif ability == Pyrokenisis.FIRESTORM:
        distance = skill['firestorm_distance']
        min_damage_min = skill['firestorm_min_damage_min']
        min_damage_max = skill['firestorm_min_damage_max']
        max_damage_min = skill['firestorm_max_damage_min']
        max_damage_max = skill['firestorm_max_damage_max']

        min_damage = (skill.level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
        max_damage = (skill.level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min

        player = avsdplayer.player

        repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FIRESTORM]['repeat'] = Repeat(firestorm_deal_damage, args=(avsdplayer, distance, round(min_damage), round(max_damage)))
        repeat.args += (repeat, )
        repeat.start(1, 3)

        cooldown = skill['firestorm_cooldown']
    elif ability == Pyrokenisis.FLAME_WALL:
        min_damage = skill['flame_wall_min_damage']
        max_damage = skill['flame_wall_max_damage']

        damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage

        if avsdplayer.data['challenge'].get('active', False):
            damage += avsdplayer.data['challenge']['flame_wall_damage']

        player = avsdplayer.player
        origin = player.get_view_coordinates()

        mins = origin + Vector(-20, -75, 0)
        maxs = origin + Vector(20, 75, 60)

        zone = FlameWallZone(avsdplayer, mins, maxs, team=5 - player.team_index, attacker=avsdplayer.userid, damage=damage)

        zone_manager.append(zone)

        avsdplayer.data['pyrokenisis'][Pyrokenisis.FLAME_WALL]['delay'] = Delay(5, zone_manager.remove, args=(zone, ))

        cooldown = skill['flame_wall_cooldown']
    elif ability == Pyrokenisis.SCORCHED_GROUND:
        distance = skill['scorched_ground_distance']
        min_damage_min = skill['scorched_ground_min_damage_min']
        min_damage_max = skill['scorched_ground_min_damage_max']
        max_damage_min = skill['scorched_ground_max_damage_min']
        max_damage_max = skill['scorched_ground_max_damage_max']

        min_damage = (skill.level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
        max_damage = (skill.level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min

        if avsdplayer.data['challenge'].get('active', False):
            min_damage += avsdplayer.data['challenge']['scorched_ground_min_damage']
            max_damage += avsdplayer.data['challenge']['scorched_ground_max_damage']

        player = avsdplayer.player
        origin = player.origin

        zone = ScorchedGroundZone(avsdplayer, origin, distance, team=5 - player.team_index, attacker=avsdplayer.userid, min_damage=round(min_damage), max_damage=round(max_damage))

        zone_manager.append(zone)

        avsdplayer.data['pyrokenisis'][Pyrokenisis.SCORCHED_GROUND]['delay'] = Delay(7, zone_manager.remove, args=(zone, ))

        cooldown = skill['scorched_ground_cooldown']
    else:
        distance = skill['flame_tornado_distance']
        damage = skill['flame_tornado_damage']

        player = avsdplayer.player
        origin = player.get_view_coordinates()

        _class_lucifer_pyrokenisis_flametornado.create(origin)

        origin[2] += 180

        repeat = avsdplayer.data['pyrokenisis'][Pyrokenisis.FLAME_TORNADO]['repeat'] = Repeat(flame_tornado_pully, args=(avsdplayer.userid, player.team_index, origin, distance, damage))
        repeat.start(0.5, 7)

        flame_tornado_pully(avsdplayer.userid, player.team_index, origin, distance, damage)

        cooldown = skill['flame_tornado_cooldown']

    avsdplayer.data['pyrokenisis']['cooldown'] = cooldown

    if isinstance(option.value, Pyrokenisis):
        return menu


@menu.register_build_callback
def menu_build(menu, client):
    avsdplayer = AVSDPlayer.from_index(client)

    assert avsdplayer.current_class == settings.name

    current_level = avsdplayer.skills['pyrokenisis'].level

    for i, level in enumerate([1, 1, 10, 15, 20, 25, 30], 2):
        menu[i].selectable = menu[i].highlight = current_level >= level
