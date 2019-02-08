# ../avsd/modules/classes/michael.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Random
from random import randint
#   Time
from time import time

# Source.Python Imports
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
from filters.weapons import WeaponClassIter
#   Listeners
from listeners.tick import Delay
#   Mathlib
from mathlib import Vector

# AvsD Imports
#   Area
from ...core.area.zone import SquareZone
from ...core.area.zone import zone_manager
#   Helpers
from ...core.helpers.particle import Particle
from ...core.helpers.skillshot import Skillshot
#   Listeners
from ...core.listeners import OnPlayerAttackPre
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerStatReceivePre
from ...core.listeners import OnTakeDamage
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer
from ...core.players.filters import PlayerReadyIter


# ============================================================================
# >> CLASSES
# ============================================================================
class SphereOfLightSkillshot(Skillshot):
    particle = Particle('_Class_Michael_Sphere_Of_Light')

    def on_start_touch(self, other):
        if other.class_name == 'player':
            if other.team_index != self.data['team']:
                avsdplayer = AVSDPlayer.from_index(other.index)
                now = time()

                if avsdplayer.data['sphere of light'].get('duration', 0) < now:
                    avsdplayer.data['sphere of light']['duration'] = now + self.data['duration']

                    avsdplayer.data['sphere of light']['armor'] = other.armor

                    other.armor = 0

                    avsdplayer.data['sphere of light']['delay'] = Delay(self.data['duration'], gain_armor, args=(avsdplayer, ))
        else:
            return True


class HolyGroundZone(SquareZone):
    def on_enter_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if 'rates' not in avsdplayer.data['holy ground']:
            avsdplayer.data['holy ground']['rates'] = []

        if player.userid == self.owner.userid:
            value = self.data['rate']
        else:
            value = self.data['allies_rate']

        avsdplayer.data['holy ground']['rates'].append(value)
        avsdplayer.data['holy ground']['rate'] = max(avsdplayer.data['holy ground']['rates'])

    def on_exit_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if player.userid == self.owner.userid:
            value = self.data['rate']
        else:
            value = self.data['allies_rate']

        avsdplayer.data['holy ground']['rates'].remove(value)

        if avsdplayer.data['holy ground']['rates']:
            avsdplayer.data['holy ground']['rate'] = max(avsdplayer.data['holy ground']['rates'])
        else:
            del avsdplayer.data['holy ground']['rate']


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
_class_michael_judgement = Particle('_Class_Michael_Judgement', lifetime=5)
_class_michael_commence_attack = Particle('_Class_Michael_Commence_Attack', lifetime=5)
_class_michael_righteousness = Particle('_Class_Michael_Righteousness_copy', lifetime=5)
_class_michael_holy_ground = Particle('_Class_Michael_Holy_Ground', lifetime=5)
_class_divine_punishment = Particle('_Class_Divine_Punishment_copy', lifetime=5)
weapons = [weapon.name for weapon in list(WeaponClassIter('primary')) + list(WeaponClassIter('secondary'))]
semi_weapons = [weapon.name for weapon in WeaponClassIter('pistol')]


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def gain_armor(avsdplayer):
    avsdplayer.player.armor = min(avsdplayer.stats['armor'], avsdplayer.data['sphere of light']['armor'])


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_death')
def player_death(event):
    on_player_delete(AVSDPlayer.from_userid(event['userid']))


@Event('round_prestart')
def round_start(event):
    for _, avsdplayer in PlayerReadyIter():
        on_player_delete(avsdplayer)

        delay = avsdplayer.data['holy ground'].get('delay')

        if delay is not None:
            if delay.running:
                delay()


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerAttackPre
def on_player_attack_pre(avsdplayer, player, weapon, is_attack1, data):
    rate = avsdplayer.data['holy ground'].get('rate')

    if rate is not None:
        data['rate'] += rate


@OnPlayerDelete
def on_player_delete(avsdplayer):
    delay = avsdplayer.data['sphere of light'].get('delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    delay = avsdplayer.data['holy ground'].get('delay')

    if delay is not None:
        if delay.running:
            delay()


@OnPlayerStatReceivePre
def on_player_pre_stat_Receive(avsdplayer, stat, data):
    if stat == 'aregen':
        if avsdplayer.data['sphere of light'].get('duration', 0) >= time():
            data['value'] = 0


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class SphereOfLightAbility(Ability):
    name = 'sphere of light'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        SphereOfLightSkillshot(avsdplayer, duration=skill['duration'], team=player.team_index)


@settings.ability
class HolyGroundAbility(Ability):
    name = 'holy ground'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        min_rate = skill['min_rate']
        max_rate = skill['max_rate']
        min_allies_rate = skill['min_allies_rate']
        max_allies_rate = skill['max_allies_rate']

        rate = (skill.level / skill.max) * (max_rate - min_rate) + min_rate
        allies_rate = (skill.level / skill.max) * (max_allies_rate - min_allies_rate) + min_allies_rate

        corner = skill['corner']
        origin = player.origin

        mins = origin + Vector(-corner, -corner, -corner)
        maxs = origin + Vector(corner, corner, corner)

        zone = HolyGroundZone(avsdplayer, mins, maxs, team=player.team_index, rate=rate, allies_rate=allies_rate)

        zone_manager.append(zone)

        avsdplayer.data[self.name]['delay'] = Delay(skill['duration'], zone_manager.remove, args=(zone, ))

        _class_michael_holy_ground.create(origin)


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    now = time()

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            skill = avsdattacker.skills['judgement']
            level = skill.level

            if level:
                if avsdattacker.data['judgement'].get('cooldown', 0) <= now:
                    if avsdvictim.data['judgement'].get('duration', 0) <= now:
                        min_chance = skill['min_chance']
                        max_chance = skill['max_chance']

                        chance = (level / skill.max) * (max_chance - min_chance) + min_chance

                        if randint(0, 100) < chance:
                            avsdattacker.data['judgement']['cooldown'] = now + skill['cooldown']

                            avsdvictim.data['judgement']['attacker'] = avsdattacker.userid
                            avsdvictim.data['judgement']['duration'] = now + skill['duration']
                            avsdvictim.data['judgement']['damage'] = (level / skill.max) * (skill['max_damage'] - skill['min_damage']) + skill['min_damage']

                            _class_michael_judgement.create(avsdvictim.player.origin, parent=avsdvictim.player)

            skill = avsdattacker.skills['commence attack']
            level = skill.level

            if level:
                if avsdattacker.data['commence attack'].get('cooldown', 0) <= now:
                    min_chance = skill['min_chance']
                    max_chance = skill['max_chance']

                    chance = (level / skill.max) * (max_chance - min_chance) + min_chance

                    if randint(0, 100) < chance:
                        min_cooldown = skill['min_cooldown']
                        max_cooldown = skill['max_cooldown']

                        cooldown = (level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

                        avsdattacker.data['commence attack']['cooldown'] = now + cooldown

                        count = len(PlayerIter(['alive', 't' if avsdattacker.player.team_index == 2 else 'ct']))

                        info.damage += skill['initial_damage'] + skill['extra_damage'] * (count - 1)

                        _class_michael_commence_attack.create(avsdattacker.player.origin, parent=avsdattacker.player)

            skill = avsdattacker.skills['divine punishment']
            level = skill.level

            if level:
                if avsdattacker.data['divine punishment'].get('cooldown', 0) <= now:
                    if avsdvictim.player.health <= skill['health_requirement']:
                        min_cooldown = skill['min_cooldown']
                        max_cooldown = skill['max_cooldown']

                        cooldown = (level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

                        avsdattacker.data['divine punishment']['cooldown'] = now + cooldown

                        info.damage += skill['damage']

                        _class_divine_punishment.create(avsdvictim.player.origin)

            if avsdvictim.data['judgement'].get('duration', 0) > now:
                if avsdattacker.data['righteousness'].get('active'):
                    avsdattacker.data['righteousness']['active'] = False

                    skill = avsdattacker.skills['righteousness']

                    info.damage += skill['damage']

    if avsdvictim.ready:
        if avsdvictim.current_class == settings.name:
            skill = avsdvictim.skills['righteousness']
            level = skill.level

            if level:
                if avsdvictim.data['righteousness'].get('cooldown', 0) <= now:
                    min_cooldown = skill['min_cooldown']
                    max_cooldown = skill['max_cooldown']

                    cooldown = (level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

                    avsdvictim.data['righteousness']['cooldown'] = now + cooldown
                    avsdvictim.data['righteousness']['active'] = True

                    _class_michael_righteousness.create(avsdvictim.player.origin, parent=avsdvictim.player)

            # For item Ethereal Breastplate
            reduction = avsdvictim.skills['sphere of light'].stats.get('reduction')

            if reduction is not None:
                if avsdattacker.data['sphere of light'].get('duration', 0) >= now:
                    info.damage = max(info.damage - reduction, 1)

        if avsdvictim.data['judgement'].get('duration', 0) > now:
            damage = avsdvictim.data['judgement']['damage']

            if avsdvictim.data['judgement']['attacker'] != avsdattacker.userid:
                damage *= 0.5

            info.damage += damage
