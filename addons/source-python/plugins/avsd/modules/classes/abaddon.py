# ../avsd/modules/classes/abaddon.py

# ============================================================================
# >> IMPORTS
# ============================================================================
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
#   Listeners
from listeners import OnLevelInit
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Players
from players.entity import Player
from players.helpers import index_from_userid

# AvsD Imports
#   Helpers
from ...core.helpers.particle import Particle
from ...core.helpers.skillshot import Skillshot
#   Listeners
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnPlayerUIBuffPre
from ...core.listeners import OnPlayerUIDebuffPre
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
class LocustSwarmSkillshot(Skillshot):
    particle = Particle('_Class_Abaddon_Locust_Swarm_Skillshot')

    def on_start_touch(self, other):
        if other.class_name == 'player':
            if other.team_index != self.data['team']:
                avsdplayer = AVSDPlayer.from_index(other.index)

                repeat = avsdplayer.data['locust swarm'].get('repeat')

                if repeat is not None:
                    if repeat.status == RepeatStatus.RUNNING:
                        repeat.stop()

                particle = avsdplayer.data['locust swarm'].get('particle')

                if particle is not None:
                    particle.remove()

                avsdplayer.data['locust swarm']['particle'] = _class_abaddon_locust_swarm.create(other.origin, lifetime=self.data['interval'] * self.data['counter'], parent=other)

                repeat = avsdplayer.data['locust swarm']['repeat'] = Repeat(deal_damage, args=(avsdplayer.userid, self.owner.userid, self.data['interval_damage'], None, 2))
                repeat.start(self.data['interval'], self.data['counter'])

        return True


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
_class_abaddon_locust_swarm = Particle('_Class_Abaddon_Locust_Swarm')
_class_abaddon_pestilence = Particle('_Class_Abaddon_Pestilence')
_class_abaddon_fields_of_scarabs = Particle('_Class_Abaddon_Fields_of_Scarabs')
_class_abaddon_abscesses = Particle('_Class_Abaddon_Abscesses')
_class_abaddon_death = Particle('_Class_Abaddon_Death')


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_death')
def player_death(event):
    on_player_delete(AVSDPlayer.from_userid(event['userid']))


@Event('round_prestart')
def round_prestart(event):
    for _, avsdplayer in PlayerReadyIter():
        on_player_delete(avsdplayer)

        if avsdplayer.current_class == settings.name:
            avsdplayer.data['locust swarm'].pop('effect_index', None)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnLevelInit
def on_level_init(map_name):
    for _, avsdplayer in PlayerReadyIter('all'):
        on_player_delete(avsdplayer)


@OnPlayerDelete
def on_player_delete(avsdplayer):
    for name in ['locust swarm', 'pestilence', 'abscesses']:
        repeat = avsdplayer.data[name].get('repeat')

        if repeat is not None:
            if repeat.status == RepeatStatus.RUNNING:
                repeat.stop()

    if avsdplayer.current_class == settings.name:
        repeat = avsdplayer.data['fields of scarabs'].get('repeat')

        if repeat is not None:
            if repeat.status == RepeatStatus.RUNNING:
                repeat.stop()


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if old == settings.name:
        repeat = avsdplayer.data['fields of scarabs'].get('repeat')

        if repeat is not None:
            if repeat.status == RepeatStatus.RUNNING:
                repeat.stop()


@OnPlayerUIBuffPre
def on_player_buff_pre(avsdplayer, class_, language, messages, now):
    if class_.name == settings.name:
        repeat = avsdplayer.data['fields of scarabs'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            # TODO: Is it a bug that I have to subtract 1?
            messages.append(settings.strings['ui fields of scarabs'].get_string(language, value=repeat.total_time_remaining - 1))


@OnPlayerUIDebuffPre
def on_player_debuff_pre(avsdplayer, class_, language, messages, now):
    for name in ['locust swarm', 'pestilence', 'abscesses']:
        repeat = avsdplayer.data[name].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            # TODO: Is it a bug that I have to subtract 1?
            # messages.append(settings.strings[f'ui {name.lower()}'].get_string(language, value=repeat.total_time_remaining - 1))
            messages.append(settings.strings[f'ui {name}'].get_string(language, value=repeat.total_time_remaining - 1))


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def deal_damage(name, userid, attacker, damage, minhealth=None, boost=None, armor=None):
    player = Player.from_userid(userid)

    if boost:
        if minhealth is not None:
            if player.health < minhealth:
                damage *= boost
        else:
            damage *= boost

    if armor is not None:
        curarmor = player.armor

        if curarmor:
            player.armor = max(0, curarmor - armor)

    try:
        attacker = index_from_userid(attacker)
    except ValueError:
        attacker = 0
    else:
        avsdplayer = AVSDPlayer.from_index(attacker)

        if avsdplayer.ready:
            if avsdplayer.current_class == settings.name:
                skill = avsdplayer.skills['death']
                level = skill.level

                if level:
                    min_health = skill['min_health']
                    max_health = skill['max_health']

                    health = (level / skill.max) * (max_health - min_health) + min_health

                    if avsdplayer.player.health <= health:
                        damage += health

                        _class_abaddon_death.create(player.origin, lifetime=5)

    if damage is not None:
        AVSDPlayer.from_index(player.index).take_damage(damage, attacker, settings.name, name)


def deal_aoe_damage(userid, damage, radius):
    index = index_from_userid(userid)
    player = Player(index)
    origin = player.origin

    for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
        if target.origin.get_distance_sqr(origin) <= radius ** 2:
            AVSDPlayer.from_index(target.index).take_damage(damage, index, settings.name, 'fields of scarabs')


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class LocustSwarmAbility(Ability):
    name = 'locust swarm'

    def activate(self, avsdplayer, skill, player, now):
        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

        avsdplayer.data[self.name]['cooldown'] = now + cooldown

        LocustSwarmSkillshot(avsdplayer, team=player.team_index, attacker=avsdplayer.userid, interval_damage=skill['interval_damage'], interval=skill['interval'], counter=skill['counter'])


@settings.ability
class FieldsOfScarabAbility(Ability):
    name = 'fields of scarabs'

    def activate(self, avsdplayer, skill, player, now):
        min_cooldown = skill['min_cooldown']
        max_cooldown = skill['max_cooldown']

        cooldown = (skill.level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

        avsdplayer.data[self.name]['cooldown'] = now + cooldown

        damage = skill['interval_damage']
        radius = skill['radius']
        counter = skill['counter']
        interval = skill['interval']

        repeat = avsdplayer.data[self.name].get('repeat')

        if repeat is not None:
            if repeat.status == RepeatStatus.RUNNING:
                repeat.stop()

        repeat = avsdplayer.data[self.name]['repeat'] = Repeat(deal_aoe_damage, args=(avsdplayer.userid, damage, radius))
        repeat.start(interval, counter)

        _class_abaddon_fields_of_scarabs.create(player.origin, lifetime=2, parent=player)


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            for name in ['locust swarm', 'pestilence', 'abscesses']:
                skill = avsdattacker.skills[name]
                level = skill.level

                if level:
                    repeat = avsdvictim.data[name].get('repeat')

                    if repeat is None or repeat.status != RepeatStatus.RUNNING:
                        other = avsdvictim.player
                        args = (name, other.userid, avsdattacker.userid, skill['interval_damage'])

                        if name == 'locust swarm':
                            particle = avsdvictim.data['locust swarm'].get('particle')

                            if particle is not None:
                                particle.remove()

                            avsdvictim.data['locust swarm']['particle'] = _class_abaddon_locust_swarm.create(other.origin, lifetime=2, parent=other)

                            avsdvictim.take_delayed_damage(skill['initial_damage'], avsdattacker.index, settings.name, 'locust swarm')
                        elif name == 'pestilence':
                            args += (skill['damage_boost_minhealth'], skill['damage_boost_multiplier'])

                            _class_abaddon_pestilence.create(other.origin, lifetime=2, parent=other)
                        else:
                            args += (None, None, skill['interval_armor'])

                            _class_abaddon_abscesses.create(other.origin, lifetime=2, parent=other)

                        repeat = avsdvictim.data[name]['repeat'] = Repeat(deal_damage, args=args)
                        repeat.start(skill['interval'], skill['counter'])

    if avsdvictim.ready:
        if avsdvictim.current_class == settings.name:
            skill = avsdvictim.skills['scarab shield']
            level = skill.level

            if level:
                multiplier = skill['reduction_multiplier']

                info.damage *= multiplier

                min_damage = skill['min_damage']
                max_damage = skill['max_damage']

                damage = round((level / skill.max) * (max_damage - min_damage) + min_damage)

                avsdvictim.take_delayed_damage(damage, avsdattacker.index, settings.name, 'scarab shield')
