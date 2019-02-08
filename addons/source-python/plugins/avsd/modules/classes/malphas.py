# ../avsd/modules/classes/malphas.py

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
#   Listeners
from listeners.tick import Delay
#   Players
from players.helpers import index_from_userid

# AvsD Imports
#   Area
from ...core.area.zone import SphereZone
from ...core.area.zone import zone_manager
#   Helpers
from ...core.helpers.particle import Particle
#   Listeners
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerStatsUpdatePre
from ...core.listeners import OnPlayerUpgradeSkill
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
class SacrificialPactZone(SphereZone):
    def on_enter_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if 'reductions' not in avsdplayer.data['sacrificial pact']:
            avsdplayer.data['sacrificial pact']['reductions'] = []

        if player.userid == self.owner.userid:
            value = self.data['reduction']
        else:
            value = self.data['allies_reduction']

        avsdplayer.data['sacrificial pact']['reductions'].append(value)
        avsdplayer.data['sacrificial pact']['reduction'] = max(avsdplayer.data['sacrificial pact']['reductions'])

    def on_exit_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if player.userid == self.owner.userid:
            value = self.data['reduction']
        else:
            value = self.data['allies_reduction']

        avsdplayer.data['sacrificial pact']['reductions'].remove(value)

        if avsdplayer.data['sacrificial pact']['reductions']:
            avsdplayer.data['sacrificial pact']['reduction'] = max(avsdplayer.data['sacrificial pact']['reductions'])
        else:
            del avsdplayer.data['sacrificial pact']['reduction']


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
_class_malphas_soul_armour = Particle('_Class_Malphas_Soul_Armour', lifetime=5)
_class_malphas_sacrificial_pact = Particle('_Class_Malphas_Sacrificial_Pact', lifetime=5)
_skill_soul_bolt_blue = Particle('_Skill_Soul_Bolt_Blue', lifetime=5)
_class_malphas_siege = Particle('_Class_Malphas_Siege', lifetime=5)


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def sacrificial_pact_give_health(avsdplayer, health):
    player = avsdplayer.player
    player.health = min(avsdplayer.stats['health'], player.health + health)


def demons_embrace_unstuck(avsdplayer):
    avsdplayer.state['stuck'] -= 1


def fortified_organs_decrease(avsdplayer, delay):
    avsdplayer.data['fortified organs']['niveau'] -= 1

    avsdplayer.data['fortified organs']['delays'].remove(delay)


def sphere_of_destruction_explode(attacker, team, origin, radius, min_closest_damage, max_closest_damage, furthest_damage):
    try:
        index = index_from_userid(attacker)
    except ValueError:
        index = 0

    for target in PlayerIter(['alive', 'ct' if team == 2 else 't']):
        distance = origin.get_distance_sqr(target.origin)

        if distance <= radius ** 2:
            if distance <= 50 ** 2:
                damage = randint(min_closest_damage, max_closest_damage)
            elif distance <= 350 ** 2:
                damage = furthest_damage
            else:
                continue

            AVSDPlayer.from_index(target.index).take_damage(damage, index, settings.name, 'sphere of destruction')


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player

        if not player.dead and player.team_index in (2, 3):
            skill = avsdplayer.skills['armour of souls']
            level = skill.level

            if level:
                _class_malphas_soul_armour.create(player.origin)


@Event('player_death')
def player_death(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    if avsdplayer.current_class == settings.name:
        delay = avsdplayer.data['sacrificial pact'].get('delayhealth')

        if delay is not None:
            if delay.running:
                delay.cancel()

        delay = avsdplayer.data['demons embrace'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        delays = avsdplayer.data['fortified organs'].get('delays')

        if delays is not None:
            for delay in delays.copy():
                if delay.running:
                    delay()


@Event('round_prestart')
def round_prestart(event):
    for _, avsdplayer in PlayerReadyIter():
        delay = avsdplayer.data['demons embrace'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        if avsdplayer.current_class == settings.name:
            delay = avsdplayer.data['sacrificial pact'].get('delay')

            if delay is not None:
                if delay.running:
                    delay()

            delay = avsdplayer.data['sacrificial pact'].get('delayhealth')

            if delay is not None:
                if delay.running:
                    delay.cancel()

            delays = avsdplayer.data['fortified organs'].get('delays')

            if delays is not None:
                for delay in delays.copy():
                    if delay.running:
                        delay()


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerDelete
def on_player_delete(avsdplayer):
    delay = avsdplayer.data['demons embrace'].get('delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    if avsdplayer.current_class == settings.name:
        delay = avsdplayer.data['sacrificial pact'].get('delay')

        if delay is not None:
            if delay.running:
                delay()

        delay = avsdplayer.data['sacrificial pact'].get('delayhealth')

        if delay is not None:
            if delay.running:
                delay.cancel()

        delays = avsdplayer.data['fortified organs'].get('delays')

        if delays is not None:
            for delay in delays:
                if delay.running:
                    delay.cancel()


@OnPlayerStatsUpdatePre
def on_player_stats_update_pre(avsdplayer, class_, initialize, data):
    if initialize:
        if class_.name == settings.name:
            skill = class_.skills['armour of souls']
            level = skill.level

            if level:
                min_health = skill['min_health']
                max_health = skill['max_health']
                min_armor = skill['min_armor']
                max_armor = skill['max_armor']
                min_hregen = skill['min_hregen']
                max_hregen = skill['max_hregen']

                health = (skill.level / skill.max) * (max_health - min_health) + min_health
                armor = (skill.level / skill.max) * (max_armor - min_armor) + min_armor
                hregen = (skill.level / skill.max) * (max_hregen - min_hregen) + min_hregen

                data['health'] = data.get('health', 0) + round(health)
                data['armor'] = data.get('armor', 0) + round(armor)
                data['hregen'] = data.get('hregen', 0) + hregen


@OnPlayerUpgradeSkill
def on_player_upgrade_skill(avsdplayer, skill, old_level, new_level):
    if avsdplayer.current_class == settings.name:
        if skill.name == 'armour of souls':
            data = avsdplayer.data

            min_health = skill['min_health']
            max_health = skill['max_health']
            min_armor = skill['min_armor']
            max_armor = skill['max_armor']
            min_hregen = skill['min_hregen']
            max_hregen = skill['max_hregen']

            # TODO: This is not 100% accurate
            health = ((new_level - old_level) / skill.max) * (max_health - min_health) + min_health
            armor = ((new_level - old_level) / skill.max) * (max_armor - min_armor) + min_armor
            hregen = ((new_level - old_level) / skill.max) * (max_hregen - min_hregen) + min_hregen

            data['health'] = data.get('health', 0) + round(health)
            data['armor'] = data.get('armor', 0) + round(armor)
            data['hregen'] = data.get('hregen', 0) + hregen


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class SacrificialPactAbility(Ability):
    name = 'sacrificial pact'

    def activate(self, avsdplayer, skill, player, now):
        min_sacrifice_health = skill['min_sacrifice_health']
        max_sacrifice_health = skill['max_sacrifice_health']

        sacrifice_health = round((skill.level / skill.max) * (max_sacrifice_health - min_sacrifice_health) + min_sacrifice_health)

        if player.health <= sacrifice_health:
            return

        player.health -= sacrifice_health

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        min_reduction = skill['min_reduction']
        max_reduction = skill['max_reduction']
        min_allies_reduction = skill['min_allies_reduction']
        max_allies_reduction = skill['max_allies_reduction']

        reduction = (skill.level / skill.max) * (max_reduction - min_reduction) + min_reduction
        allies_reduction = (skill.level / skill.max) * (max_allies_reduction - min_allies_reduction) + min_allies_reduction

        distance = skill['distance']
        origin = player.origin

        zone = SacrificialPactZone(avsdplayer, origin, distance, team=player.team_index, reduction=reduction, allies_reduction=allies_reduction)

        zone_manager.append(zone)

        avsdplayer.data[self.name]['delay'] = Delay(3, zone_manager.remove, args=(zone, ))
        avsdplayer.data[self.name]['delayhealth'] = Delay(3, sacrificial_pact_give_health, args=(avsdplayer, sacrifice_health))

        _class_malphas_sacrificial_pact.create(origin, parent=player)


@settings.ability
class SphereOfDestructionAbility(Ability):
    name = 'sphere of destruction'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        origin = player.get_view_coordinates()

        min_distance = skill['min_distance']
        max_distance = skill['max_distance']
        min_closest_damage_min = skill['min_closest_damage_min']
        min_closest_damage_max = skill['min_closest_damage_max']
        max_closest_damage_min = skill['max_closest_damage_min']
        max_closest_damage_max = skill['max_closest_damage_max']
        min_furthest_damage = skill['min_furthest_damage']
        max_furthest_damage = skill['max_furthest_damage']

        radius = (skill.level / skill.max) * (max_distance - min_distance) + min_distance
        min_closest_damage = (skill.level / skill.max) * (min_closest_damage_max - min_closest_damage_min) + min_closest_damage_min
        max_closest_damage = (skill.level / skill.max) * (max_closest_damage_max - max_closest_damage_min) + max_closest_damage_min
        furthest_damage = (skill.level / skill.max) * (max_furthest_damage - min_furthest_damage) + min_furthest_damage

        _class_malphas_siege.create(origin)

        # For item Artifact of Destruction
        pull_force = skill.stats.get('pull_force', 0) + 1

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            distance = origin.get_distance_sqr(target.origin)

            if distance <= radius ** 2:
                # TODO: Check if this is still valid
                target.base_velocity = (origin - target.origin) / (distance / radius) * (2 * pull_force)

        avsdplayer.data[self.name]['delay'] = Delay(4.5, sphere_of_destruction_explode, args=(avsdplayer.userid, player.team_index, origin, radius, round(min_closest_damage), round(max_closest_damage), round(furthest_damage)))


# ============================================================================
# >> HOOKS
# ============================================================================
# TODO: Check if this is where the Vector::DistTo crashes
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    now = time()

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            other = avsdvictim.player

            skill = avsdattacker.skills['demons embrace']
            level = skill.level

            if level:
                if avsdattacker.data['demons embrace'].get('cooldown', 0) <= now:
                    if avsdattacker.player.origin.get_distance_sqr(other.origin) <= skill['distance'] ** 2:
                        delay = avsdvictim.data['demons embrace'].get('delay')

                        if delay is None or not delay.running:
                            min_cooldown = skill['min_cooldown']
                            max_cooldown = skill['max_cooldown']

                            cooldown = (level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

                            avsdattacker.data['demons embrace']['cooldown'] = now + cooldown

                            avsdvictim.state['stuck'] += 1

                            avsdvictim.data['demons embrace']['delay'] = Delay(skill['duration'], demons_embrace_unstuck, args=(avsdvictim, ))

                            _skill_soul_bolt_blue.create(other.origin, parent=other)

            skill = avsdattacker.skills['piercing strike']
            level = skill.level

            if level:
                armor = other.armor

                if armor:
                    min_armor_removal = skill['min_armor_removal']
                    max_armor_removal = skill['max_armor_removal']

                    armor_removal = (skill.level / skill.max) * (max_armor_removal - min_armor_removal) + min_armor_removal

                    other.armor = max(round(armor - armor_removal), 0)

                # For item Soul Piercer
                min_damage = skill.stats.get('min_damage')
                max_damage = skill.stats.get('max_damage')

                if min_damage is not None and max_damage is not None:
                    info.damage += randint(min_damage, max_damage)

    if avsdvictim.ready:
        if avsdvictim.current_class == settings.name:
            skill = avsdvictim.skills['fortified organs']
            level = skill.level

            if level:
                niveau = avsdvictim.data['fortified organs'].get('niveau', 0)

                if niveau < 3:
                    niveau += 1
                    avsdvictim.data['fortified organs']['niveau'] = niveau

                    delay = Delay(skill['duration'], fortified_organs_decrease, args=(avsdvictim, ))
                    delay.args += (delay, )

                    if 'delays' not in avsdvictim.data['fortified organs']:
                        avsdvictim.data['fortified organs']['delays'] = []

                    avsdvictim.data['fortified organs']['delays'].append(delay)

                min_reduction = skill['min_reduction']
                max_reduction = skill['max_reduction']

                reduction = (skill.level / skill.max) * (max_reduction - min_reduction) + min_reduction

                info.damage -= info.damage * (niveau * reduction) / 100

        reduction = avsdvictim.data['sacrificial pact'].get('reduction')

        if reduction is not None:
            if reduction < info.damage:
                info.damage -= reduction
            else:
                return False
