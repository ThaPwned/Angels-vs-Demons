# ../avsd/modules/classes/barachiel.py

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
from filters.weapons import WeaponClassIter
#   Listeners
from listeners.tick import Delay
#   Players
from players.entity import Player

# AvsD Imports
#   Helpers
from ...core.helpers.particle import Particle
#   Listeners
from ...core.listeners import OnPlayerAbilityPre
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerStatsUpdatePre
from ...core.listeners import OnPlayerSwitchClass
from ...core.listeners import OnPlayerUpgradeSkill
from ...core.listeners import OnTakeDamage
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer
from ...core.players.filters import PlayerIter
from ...core.players.filters import PlayerReadyIter


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
melee_weapons = [x.name for x in WeaponClassIter('melee')]
_class_barachiel_spiritual_bash = Particle('_Class_Barachiel_Spiritual_Bash')
_class_barachiel_glorified_vengeance = Particle('_Class_Barachiel_Glorified_Vengeance')
_class_barachiel_eye_of_divinity = Particle('Class_Barachiel_Eye_Of_Divinity')
_class_barachiel_sanctification = Particle('_Class_Barachiel_Sanctification')
_class_barachiel_sacred_heart = Particle('_Class_Barachiel_Sacred_Heart')
_class_barachiel_devout_barrier = Particle('_Class_Barachiel_Devout_Barrier')


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def sanctification_reset(avsdplayer, health, speed, steps):
    for avsdtarget in avsdplayer.data['sanctification']['targets']:
        player = avsdtarget.player

        player.health = max(1, player.health + health)
        player.speed -= speed

        avsdtarget.stats['health'] -= health
        avsdtarget.stats['speed'] -= speed
        avsdtarget.stats['flyspeed'] -= speed


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player

        if not player.dead and player.team_index in (2, 3):
            skill = avsdplayer.skills['sacred heart']
            level = skill.level

            if level:
                _class_barachiel_sacred_heart.create(player.origin, lifetime=5)


@Event('player_death')
def player_death(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    if avsdplayer.current_class == settings.name:
        skill = avsdplayer.skills['sanctification']
        level = skill.level

        if level:
            player = avsdplayer.player
            origin = player.origin

            distance = skill['distance']
            duration = skill['duration']
            steps = skill['steps']
            min_health = skill['min_health']
            max_health = skill['max_health']
            min_speed = skill['min_speed']
            max_speed = skill['max_speed']

            health = round((level / skill.max) * (max_health - min_health) + min_health)
            speed = (level / skill.max) * (max_speed - min_speed) + min_speed

            _class_barachiel_sanctification.create(origin, lifetime=5)

            targets = []

            for target, avsdtarget in PlayerReadyIter(['alive', 'ct' if player.team_index == 3 else 't']):
                if origin.get_distance_sqr(target.origin) <= distance ** 2:
                    avsdtarget.stats['health'] += health
                    avsdtarget.stats['speed'] += speed
                    avsdtarget.stats['flyspeed'] += speed

                    targets.append(avsdtarget)

            if targets:
                avsdplayer.data['sanctification']['health'] = health
                avsdplayer.data['sanctification']['speed'] = speed

                avsdplayer.data['sanctification']['delay'] = Delay(duration + 1.5, sanctification_reset, args=(avsdplayer, health, speed, steps))
                avsdplayer.data['sanctification']['targets'] = targets


@Event('round_prestart')
def round_prestart(event):
    for _, avsdplayer in PlayerIter():
        delay = avsdplayer.data['sanctification'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

                health = avsdplayer.data['sanctification']['health']
                speed = avsdplayer.data['sanctification']['speed']

                for avsdtarget in avsdplayer.data['sanctification']['targets']:
                    avsdtarget.stats['health'] -= health
                    avsdtarget.stats['speed'] -= speed
                    avsdtarget.stats['flyspeed'] -= speed


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerDelete
def on_player_delete(avsdplayer):
    for _, avsdplayer in PlayerIter():
        targets = avsdplayer.data['sanctification'].get('targets', [])

        if avsdplayer in targets:
            targets.remove(avsdplayer)

    if avsdplayer.current_class == settings.name:
        delay = avsdplayer.data['sanctification'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()


@OnPlayerAbilityPre
def on_player_pre_ability(avsdplayer, data):
    if avsdplayer.data['spiritual bash'].get('duration', 0) >= time():
        data['allow'] = False


@OnPlayerStatsUpdatePre
def on_player_stats_update_pre(avsdplayer, class_, initialize, data):
    if initialize:
        if class_.name == settings.name:
            skill = class_.skills['sacred heart']
            level = skill.level

            if level:
                health = skill['health']

                data['health'] = data.get('health', 0) + health * level


@OnPlayerSwitchClass
def on_player_switch_class(avsdplayer, old, new):
    if avsdplayer.data['sanctification'].get('active'):
        health = avsdplayer.data['sanctification']['health']
        speed = avsdplayer.data['sanctification']['speed']

        avsdplayer.stats['health'] += health
        avsdplayer.stats['speed'] += speed
        avsdplayer.stats['flyspeed'] += speed

        avsdplayer.data['sanctification']['active'] = 0

        delay = avsdplayer.data['sanctification'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()


@OnPlayerUpgradeSkill
def on_player_upgrade_skill(avsdplayer, skill, old_level, new_level):
    if avsdplayer.current_class == settings.name:
        if skill.name == 'sacred heart':
            health = skill['health']

            avsdplayer.data['health'] = avsdplayer.data.get('health', 0) + health * (new_level - old_level)


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class EyeOfDivinityAbility(Ability):
    name = 'eye of divinity'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']
        avsdplayer.data[self.name]['duration'] = now + skill['duration']

        _class_barachiel_eye_of_divinity.create(player.origin, lifetime=5, parent=player)


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            skill = avsdattacker.skills['spiritual bash']
            level = skill.level

            if level:
                now = time()

                if avsdattacker.data['spiritual bash'].get('cooldown', 0) <= now:
                    cooldown = skill['cooldown']
                    duration = skill['duration']

                    avsdattacker.data['spiritual bash']['cooldown'] = now + cooldown

                    avsdvictim.data['spiritual bash']['duration'] = now + duration

                    other = avsdvictim.player

                    _class_barachiel_spiritual_bash.create(other.origin, lifetime=5, parent=other)

            # For item Light's Spear
            if avsdvictim.data['spiritual bash'].get('duration', 0) >= now:
                damage = skill.stats.get('damage')

                if damage is not None:
                    info.damage += damage

    if avsdvictim.ready:
        if avsdvictim.current_class == settings.name:
            now = time()

            if avsdvictim.data['eye of divinity'].get('duration', 0) > now:
                player = Player(info.attacker)
                active_weapon = player.active_weapon

                if active_weapon.class_name in melee_weapons:
                    skill = avsdvictim.skills['eye of divinity']

                    min_damage = skill['min_damage']
                    max_damage = skill['max_damage']

                    damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage

                    info.damage *= damage

                    avsdvictim.data['eye of divinity']['duration'] = 0

            skill = avsdvictim.skills['devout barrier']
            level = skill.level

            if level:
                min_health = skill['min_health']
                max_health = skill['max_health']

                health = (level / skill.max) * (min_health - max_health) + max_health

                other = avsdvictim.player

                if other.health <= health:
                    reduction = skill['reduction']

                    info.damage *= reduction

                    if avsdvictim.data['devout barrier'].get('effect_cooldown', 0) <= now:
                        _class_barachiel_devout_barrier.create(other.origin, lifetime=5, parent=other)

                        avsdvictim.data['devout barrier']['effect_cooldown'] = now + 1

            skill = avsdvictim.skills['glorified vengeance']
            level = skill.level

            if level:
                now = time()

                if avsdvictim.data['glorified vengeance'].get('cooldown', 0) <= now:
                    avsdvictim.data['glorified vengeance']['cooldown'] = now + skill['cooldown']

                    min_damage_min = skill['min_damage_min']
                    min_damage_max = skill['min_damage_max']
                    max_damage_min = skill['max_damage_min']
                    max_damage_max = skill['max_damage_max']

                    min_damage = randint(min_damage_min, min_damage_max)
                    max_damage = randint(max_damage_min, max_damage_max)

                    damage = (level / skill.max) * (max_damage - min_damage) + min_damage

                    avsdattacker.take_delayed_damage(damage, avsdvictim.index, settings.name, 'glorified vengeance')

                    entity = avsdattacker.player

                    _class_barachiel_glorified_vengeance.create(entity.origin, lifetime=5, parent=entity)
