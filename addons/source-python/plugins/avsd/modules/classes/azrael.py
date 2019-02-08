# ../avsd/modules/classes/azrael.py

# http://forums.eventscripts.com/viewtopic.php?f=95&t=42545
# https://forums.alliedmods.net/showthread.php?p=973411#post973411

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Time
from time import time

# Source.Python Imports
#   Colors
from colors import Color
#   Engines
from engines.server import global_vars
#   Entities
from entities import CheckTransmitInfo
from entities.helpers import index_from_edict
from entities.helpers import index_from_pointer
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
from filters.weapons import WeaponClassIter
#   Listeners
from listeners import ButtonStatus
from listeners import OnButtonStateChanged
from listeners import get_button_combination_status
from listeners.tick import Delay
#   Mathlib
from mathlib import QAngle
# from mathlib import Vector
#   Memory
from memory import make_object
#   Players
from players.constants import PlayerButtons
from players.constants import PlayerStates
from players.helpers import userid_from_index

# AvsD Imports
#   Helpers
# from ...core.helpers.math import AngleVectors
from ...core.helpers.math import ConeChecker
from ...core.helpers.particle import Particle
#   Listeners
from ...core.listeners import OnPlayerAttackPost
from ...core.listeners import OnPlayerAttackPre
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerFlyUpdatePre
from ...core.listeners import OnPlayerStatReceivePre
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnTakeDamage
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
DASH_COLOR = Color(35, 35, 35, 60)
settings = Settings(__name__)
melee_weapons = [x.name for x in WeaponClassIter('melee')]
_invisible = set()
_class_azrael_fog = Particle('_Class_Azrael_Fog')
_class_azrael_slash = Particle('_Class_Azrael_Slash')
_class_azrael_circular_slash = Particle('_Class_Azrael_Circular_Slash')
_class_azrael_grasp = Particle('_Class_Azrael_Grasp')
_class_azrael_grasp_range = Particle('_Class_Azrael_Grasp_Range')
_class_azrael_shadow_dash = Particle('_Class_Azrael_Shadow_Dash')
_class_azrael_death_pulse = Particle('_Class_Azrael_Death_Pulse')
_class_azrael_sigil = Particle('_Class_Azrael_Sigil')
_class_azrael_phantom_form = Particle('_Class_Azrael_Phantom_Form')


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def enable_wings(avsdplayer):
    avsdplayer.data['chains of the damned']['active'] = False


def set_shadow_dash_color(avsdplayer, color):
    avsdplayer.player.color = color

    del avsdplayer.data['shadow dash']['delay2']


def set_shadow_dash_cooldown(avsdplayer, cooldown):
    avsdplayer.data['chains of the damned']['cooldown'] = time() + cooldown


def _dyncall_slash(avsdplayer, player):
    if avsdplayer.current_class == settings.name:
        # eye_angle = angles = player.eye_angle
        angles = QAngle(*player.eye_angle)

        angles[1] += 180

        skill = avsdplayer.passives['slash']

        radius = skill['radius']
        damage = skill['damage']

        # origin = player.eye_location
        # forward = Vector(*AngleVectors(eye_angle)[0])

        cone = ConeChecker(player, radius)

        _class_azrael_slash.create(player.origin, angles=angles, lifetime=5)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            if cone.has_within(target.eye_location):
                AVSDPlayer.from_index(target.index).take_damage(damage, player.index, settings.name, 'slash')

            # target_origin = target.eye_location

            # if origin.get_distance_sqr(target_origin) <= radius ** 2:
            #     segment = target_origin - origin
            #     segment.normalize()

            #     if forward.dot(segment) < -0.8:
            #         AVSDPlayer.from_index(target.index).take_damage(damage, player.index, settings.name, 'slash')


def _dyncall_circular_slash(avsdplayer, player):
    if avsdplayer.current_class == settings.name:
        angles = QAngle(*player.eye_angle)

        angles[1] += 180

        skill = avsdplayer.passives['circular slash']

        radius = skill['radius']
        damage = skill['damage']

        origin = player.origin

        _class_azrael_circular_slash.create(origin, angles=angles, lifetime=5)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            if origin.get_distance_sqr(target.origin) <= radius ** 2:
                AVSDPlayer.from_index(target.index).take_damage(damage, player.index, settings.name, 'circular slash')


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_death')
def player_death(event):
    userid = event['userid']
    avsdplayer = AVSDPlayer.from_userid(userid)

    if avsdplayer.current_class == settings.name:
        if avsdplayer.data['phantom form'].get('active'):
            avsdplayer.data['phantom form']['active'] = False

            avsdplayer.stats['speed'] -= avsdplayer.data['phantom form']['speed']
            avsdplayer.stats['flyspeed'] -= avsdplayer.data['phantom form']['speed']
            avsdplayer.stats['gravity'] += avsdplayer.data['phantom form']['gravity']

            player = avsdplayer.player

            player.color = player.color.with_alpha(255)
            player.speed -= avsdplayer.data['phantom form']['speed']
            player.gravity += avsdplayer.data['phantom form']['gravity']

            avsdplayer.data['phantom form']['particle'].remove()

            _invisible.discard(userid)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnButtonStateChanged
def on_button_state_changed(player, old_buttons, new_buttons):
    if get_button_combination_status(old_buttons, new_buttons, PlayerButtons.JUMP) == ButtonStatus.PRESSED:
        avsdplayer = AVSDPlayer.from_index(player.index)

        if avsdplayer.ready:
            if avsdplayer.current_class == settings.name:
                skill = avsdplayer.skills['double jump']
                level = skill.level

                if level:
                    now = time()

                    if avsdplayer.data['double jump'].get('cooldown', 0) <= now:
                        flags = player.flags
                        velocity = player.velocity

                        if not flags & PlayerStates.ONGROUND:
                            min_cooldown = skill['min_cooldown']
                            max_cooldown = skill['max_cooldown']

                            cooldown = (level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

                            avsdplayer.data['double jump']['cooldown'] = now + cooldown

                        velocity *= skill['force']

                        velocity[2] += skill['base_z_force']
                        player.base_velocity = velocity


# TODO: Check if this is where the Vector::DistTo crashes
@OnPlayerAttackPost
def on_player_attack_post(avsdplayer, player, weapon, is_attack1):
    if avsdplayer.current_class == settings.name:
        if is_attack1:
            player.delay(0, _dyncall_slash, args=(avsdplayer, player))
        else:
            player.delay(0, _dyncall_circular_slash, args=(avsdplayer, player))


@OnPlayerAttackPre
def on_player_attack_pre(avsdplayer, player, weapon, is_attack1, data):
    if avsdplayer.current_class == settings.name:
        if weapon.class_name in melee_weapons:
            skill = avsdplayer.skills['scythe mastery']
            level = skill.level

            if level:
                min_rate = skill['min_rate']
                max_rate = skill['max_rate']

                rate = (level / skill.max) * (max_rate - min_rate) + min_rate

                data['rate'] += rate

            if avsdplayer.data['phantom form'].get('active'):
                data['rate'] += avsdplayer.data['phantom form']['rate']


@OnPlayerDelete
def on_player_delete(avsdplayer):
    delay = avsdplayer.data['chains of the damned'].get('delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    if avsdplayer.current_class == settings.name:
        delay = avsdplayer.data['shadow dash'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

        delay = avsdplayer.data['shadow dash'].get('delay2')

        if delay is not None:
            if delay.running:
                delay.cancel()

        _invisible.discard(avsdplayer.userid)


@OnPlayerFlyUpdatePre
def on_player_pre_fly_update(avsdplayer, data):
    if data['state']:
        if avsdplayer.data['chains of the damned'].get('duration', 0) >= time():
            data['allow'] = False


@OnPlayerStatReceivePre
def on_player_pre_stat_Receive(avsdplayer, stat, data):
    if stat in ('aregen', 'hregen'):
        if avsdplayer.data['phantom form'].get('active'):
            # For item Spectre's Cloak
            skill = avsdplayer.skills['phantom form']
            max_regen = skill.stats.get(f'max_{stat}')

            if max_regen is None:
                data['value'] = 0
            else:
                data['value'] = min(data['value'], max_regen)


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if old == settings.name:
        if avsdplayer.data['phantom form'].get('active'):
            avsdplayer.data['phantom form']['active'] = False

            avsdplayer.stats['speed'] -= avsdplayer.data['phantom form']['speed']
            avsdplayer.stats['flyspeed'] -= avsdplayer.data['phantom form']['speed']
            avsdplayer.stats['gravity'] += avsdplayer.data['phantom form']['gravity']

            player = avsdplayer.player

            if not player.dead:
                player.color = player.color.with_alpha(255)
                player.speed -= avsdplayer.data['phantom form']['speed']
                player.gravity += avsdplayer.data['phantom form']['gravity']

                avsdplayer.data['phantom form']['particle'].remove()

                _invisible.discard(avsdplayer.userid)


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class ChainsOfTheDamnedAbility(Ability):
    name = 'chains of the damned'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        _class_azrael_grasp_range.create(origin, lifetime=5)

        radius = skill['radius']
        duration = skill['duration']
        immunity = skill['immunity']
        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

        avsdplayer.data[self.name]['cooldown'] = now + cooldown

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            target_origin = target.origin

            if origin.get_distance_sqr(target_origin) <= radius ** 2:
                avsdtarget = AVSDPlayer.from_index(target.index)

                if avsdtarget.data[self.name].get('duration', 0) < now:
                    _class_azrael_grasp.create(target_origin, lifetime=5)

                    if hasattr(avsdtarget, 'flying') and avsdtarget.flying:
                        avsdtarget.flying = False

                    avsdtarget.data[self.name]['duration'] = now + duration
                    avsdtarget.data[self.name]['immunity'] = now + immunity

                    delay = avsdtarget.data[self.name].get('delay')

                    if delay is not None:
                        if delay.running:
                            delay.cancel()

                    avsdtarget.data[self.name]['delay'] = Delay(duration, enable_wings, args=(avsdtarget, ))


@settings.ability
class ShadowDashAbility(Ability):
    name = 'shadow dash'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']
        min_range = skill['min_range']
        max_range = skill['max_range']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown
        range_ = (skill.level / skill.max) * (max_range - min_range) + min_range

        player_origin = player.origin

        _class_azrael_shadow_dash.create(player_origin, lifetime=5)

        vector = origin - player_origin
        vector.normalize()
        vector *= range_ * 3

        player.teleport(velocity=vector)

        if not avsdplayer.data['phantom form'].get('active'):
            delay = avsdplayer.data[self.name].get('delay2')

            if delay is None:
                color = player.color
            else:
                color = delay.args[1]

                if delay.running:
                    delay.cancel()

            player.color = DASH_COLOR

            avsdplayer.data[self.name]['delay2'] = Delay(0.3, set_shadow_dash_color, args=(avsdplayer, color))

        if avsdplayer.data[self.name].get('count'):
            delay = avsdplayer.data[self.name]['delay']

            if delay.running:
                delay.cancel()

            avsdplayer.data[self.name]['count'] = 0

            avsdplayer.data[self.name]['cooldown'] = now + cooldown
        else:
            avsdplayer.data[self.name]['count'] = 1

            avsdplayer.data[self.name]['delay'] = Delay(skill['sequence'], set_shadow_dash_cooldown, args=(avsdplayer, cooldown))


@settings.ability
class DeathPulseAbility(Ability):
    name = 'death pulse'

    def activate(self, avsdplayer, skill, player, now):
        radius = skill['radius']
        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']
        min_damage = skill['min_damage']
        max_damage = skill['max_damage']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown
        damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage

        if avsdplayer.data['phantom form'].get('active'):
            cooldown -= avsdplayer.skills['phantom form']['death_pulse_cooldown_reduction']

        avsdplayer.data[self.name]['cooldown'] = now + cooldown

        origin = player.origin

        _class_azrael_death_pulse.create(origin, lifetime=5)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            if origin.get_distance_sqr(target.origin) <= radius ** 2:
                AVSDPlayer.from_index(target.index).take_damage(damage, player.index, settings.name, self.name)


@settings.ability
class PhantomFormAbility(Ability):
    name = 'phantom form'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        avsdplayer.data[self.name]['active'] = not avsdplayer.data[self.name].get('active')

        origin = player.origin

        _class_azrael_sigil.create(origin, lifetime=5)

        if avsdplayer.data[self.name]['active']:
            min_speed = skill['min_speed']
            max_speed = skill['max_speed']
            min_gravity = skill['min_gravity']
            max_gravity = skill['max_gravity']
            min_rate = skill['min_rate']
            max_rate = skill['max_rate']

            speed = (skill.level / skill.max) * (max_speed - min_speed) + min_speed
            gravity = (skill.level / skill.max) * (max_gravity - min_gravity) + min_gravity
            rate = (skill.level / skill.max) * (max_rate - min_rate) + min_rate

            avsdplayer.data[self.name]['speed'] = speed
            avsdplayer.data[self.name]['gravity'] = gravity
            avsdplayer.data[self.name]['rate'] = rate
            avsdplayer.data[self.name]['reduction'] = skill['damage_taken_reduction']

            avsdplayer.stats['speed'] += speed
            avsdplayer.stats['flyspeed'] += speed
            avsdplayer.stats['gravity'] -= gravity

            player.color = player.color.with_alpha(0)
            player.speed += speed
            player.gravity = avsdplayer.stats['gravity']

            player.gravity -= gravity

            origin[2] += 20

            avsdplayer.data[self.name]['particle'] = _class_azrael_phantom_form.create(origin, parent=player)

            _invisible.add(avsdplayer.userid)
        else:
            avsdplayer.stats['speed'] -= avsdplayer.data[self.name]['speed']
            avsdplayer.stats['flyspeed'] -= avsdplayer.data[self.name]['speed']
            avsdplayer.stats['gravity'] += avsdplayer.data[self.name]['gravity']

            player.color = player.color.with_alpha(255)
            player.speed -= avsdplayer.data[self.name]['speed']
            player.gravity += avsdplayer.data[self.name]['gravity']

            avsdplayer.data[self.name]['particle'].remove()

            _invisible.discard(avsdplayer.userid)


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        if avsdvictim.data['chains of the damned'].get('immunity', 0) >= time():
            info.damage = 0

        return

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            skill = avsdattacker.passives['damage']

            info.damage *= skill['multiplier']

            skill = avsdattacker.skills['scythe mastery']
            level = skill.level

            if level:
                player = avsdattacker.player

                if player.buttons & PlayerButtons.ATTACK:
                    min_left = skill['min_left']
                    max_left = skill['max_left']

                    damage = (level / skill.max) * (max_left - min_left) + min_left

                    info.damage += damage
                elif player.buttons & PlayerButtons.ATTACK2:
                    min_right = skill['min_right']
                    max_right = skill['max_right']

                    damage = (level / skill.max) * (max_right - min_right) + min_right

                    info.damage += damage

    if avsdvictim.data['phantom form'].get('active'):
        info.damage *= avsdvictim.data['phantom form']['reduction']


# TODO: Optimize this as much as possible
# @EntityPreHook(EntityCondition.is_player, 'set_transmit')
def pre_set_transmit(stack):
    index = index_from_pointer(stack[0])
    if 0 < index <= global_vars.max_clients:
        if userid_from_index(index) in _invisible:
            other = index_from_edict(make_object(CheckTransmitInfo, stack[1]).client)

            if index != other:
                return False
