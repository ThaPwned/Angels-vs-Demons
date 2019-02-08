# ../avsd/modules/classes/ariel.py

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
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Players
from players.helpers import index_from_userid

# AvsD Imports
#   Area
from ...core.area.zone import SphereZone
from ...core.area.zone import zone_manager
#   Helpers
from ...core.helpers.particle import Particle
from ...core.helpers.skillshot import Skillshot
#   Listeners
from ...core.listeners import OnPlayerAttackPost
from ...core.listeners import OnPlayerAttackPre
from ...core.listeners import OnPlayerUIDebuffPre
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerFlyUpdatePre
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer
from ...core.players.filters import PlayerReadyIter


# ============================================================================
# >> CLASSES
# ============================================================================
class PurifyingBoltSkillshot(Skillshot):
    particle = Particle('_Class_Ariel_Purifying_Bolt')

    def on_start_touch(self, other):
        if other.class_name == 'player':
            if other.team_index == self.data['team']:
                avsdplayer = AVSDPlayer.from_index(other.index)

                prepare_erosion(avsdplayer, self.owner, time())

                avsdplayer.take_delayed_damage(self.data['damage'], self.owner.index, settings.name, 'purifying bolt')

        zone = PurifyingBoltZone(self.owner, self.entity.origin, self.data['zone_radius'], **self.data)

        zone_manager.append(zone)

        Delay(self.data['duration'], zone_manager.remove, args=(zone, ))

        return True


class ZephyrSphereSkillshot(Skillshot):
    particle = Particle('_Class_Ariel_Zephyr_Sphere')

    def on_automatically_removed(self):
        self.owner.data['zephyr sphere'].pop('projectile', None)

    def on_start_touch(self, other):
        if other.class_name == 'player':
            if other.team_index != self.data['team']:
                avsdplayer = AVSDPlayer.from_index(other.index)

                prepare_erosion(avsdplayer, self.owner, time())

                avsdplayer.take_delayed_damage(self.data['damage'], self.owner.index, settings.name, 'zephyr sphere')

        self.owner.data['zephyr sphere'].pop('projectile', None)

        return True


class IcyBindingZone(SphereZone):
    def on_enter_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if 'attackers' not in avsdplayer.data['icy binding']:
            avsdplayer.data['icy binding']['attackers'] = {}

        avsdplayer.data['icy binding']['attackers'][self.data['attacker']] = self.data['slow']

        attacker = max(avsdplayer.data['icy binding']['attackers'], key=avsdplayer.data['icy binding']['attackers'].get)
        max_ = avsdplayer.data['icy binding']['attackers'][attacker]
        slowed = avsdplayer.data['icy binding'].get('slowed', 0)

        if max_ > slowed:
            player.speed -= max_ - slowed

            avsdplayer.stats['speed'] -= max_ - slowed
            avsdplayer.stats['flyspeed'] -= max_ - slowed

            avsdplayer.data['icy binding']['slowed'] = max_

    def on_exit_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        del avsdplayer.data['icy binding']['attackers'][self.data['attacker']]

        slowed = avsdplayer.data['icy binding']['slowed']

        if avsdplayer.data['icy binding']['attackers']:
            attacker = max(avsdplayer.data['icy binding']['attackers'], key=avsdplayer.data['icy binding']['attackers'].get)
            max_ = avsdplayer.data['icy binding']['attackers'][attacker]

            if max_ < slowed:
                player.speed += slowed - max_

                avsdplayer.stats['speed'] += slowed - max_
                avsdplayer.stats['flyspeed'] += slowed - max_

                avsdplayer.data['icy binding']['slowed'] = max_
        else:
            player.speed += slowed

            avsdplayer.stats['speed'] += slowed
            avsdplayer.stats['flyspeed'] += slowed

            del avsdplayer.data['icy binding']['slowed']


class PurifyingBoltZone(SphereZone):
    def on_enter_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if 'active' not in avsdplayer.data['purifying bolt']:
            avsdplayer.data['purifying bolt']['active'] = []

        avsdplayer.data['purifying bolt']['active'].append(self.data['attacker'])

        if hasattr(avsdplayer, 'flying') and avsdplayer.flying:
            avsdplayer.flying = False

    def on_exit_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        avsdplayer.data['purifying bolt']['active'].remove(self.data['attacker'])


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
melee_weapons = [x.name for x in WeaponClassIter('melee')]
_class_ariel_magical_eruption = Particle('_Class_Ariel_Magical_Eruption')
_class_ariel_amplify_magic = Particle('_Class_Ariel_Amplify_Magic')
_class_ariel_tempest = Particle('_Class_Ariel_Tempest')
_class_ariel_icy_binding = Particle('_Class_Ariel_Icy_Binding')
_class_ariel_icy_binding_target = Particle('_Class_Ariel_Icy_Binding_Target')
_class_ariel_erosion = Particle('_Class_Ariel_Erosion', offsets=[0, 0, 20])


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def icy_binding_remove_zone(zone, explode_damage, freeze_timer):
    zone_manager.remove(zone)

    for index in zone.entities:
        avsdplayer = AVSDPlayer.from_index(index)

        if 'attackers' in avsdplayer.data['icy binding']:
            if zone.data['attacker'] in avsdplayer.data['icy binding']['attackers']:
                player = avsdplayer.player

                del avsdplayer.data['icy binding']['attackers'][zone.data['attacker']]

                avsdplayer.take_damage(explode_damage, zone.data['attacker'], settings.name, 'icy binding')

                slowed = avsdplayer.data['icy binding']['slowed']

                if avsdplayer.data['icy binding']['attackers']:
                    attacker = max(avsdplayer.data['icy binding']['attackers'], key=avsdplayer.data['icy binding']['attackers'].get)
                    max_ = avsdplayer.data['icy binding']['attackers'][attacker]

                    if max_ < slowed:
                        player.speed += slowed - max_

                        avsdplayer.stats['speed'] += slowed - max_
                        avsdplayer.stats['flyspeed'] += slowed - max_
                else:
                    player.speed += slowed

                    avsdplayer.stats['speed'] += slowed
                    avsdplayer.stats['flyspeed'] += slowed

                    del avsdplayer.data['icy binding']['slowed']

                _class_ariel_icy_binding_target.create(player.origin, lifetime=5, parent=player)

                delay = avsdplayer.data['icy binding'].get('unfreeze')

                if delay is None or not delay.running:
                    # player.stuck = True
                    avsdplayer.state['stuck'] += 1
                else:
                    if delay.running:
                        delay.cancel()

                avsdplayer.data['icy binding']['unfreeze'] = Delay(freeze_timer, unfreeze_timer, args=(avsdplayer.userid, ))


def unfreeze_timer(userid):
    try:
        avsdplayer = AVSDPlayer.from_userid(userid)
    except ValueError:
        pass
    else:
        avsdplayer.state['stuck'] -= 1


def prepare_erosion(avsdtarget, avsdplayer, now):
    # if not isinstance(avsdplayer, AVSDPlayer):
    #     avsdplayer = AVSDPlayer.from_index(avsdplayer)

    if avsdplayer.current_class == settings.name:
        skill = avsdplayer.skills['erosion']
    else:
        skill = avsdplayer.classes[settings.name].skills['erosion']

    level = skill.level

    if level:
        if avsdtarget.data['erosion'].get('cooldown', 0) < now:
            min_damage = skill['min_damage']
            max_damage = skill['max_damage']

            damage = (level / skill.max) * (max_damage - min_damage) + min_damage

            repeat = avsdtarget.data['erosion']['repeat'] = Repeat(activate_erosion, args=(avsdtarget.userid, avsdplayer.userid, damage))
            repeat.start(1, skill['count'])

            avsdtarget.data['erosion']['cooldown'] = now + skill['cooldown']

            player = avsdtarget.player

            _class_ariel_erosion.create(player.origin, lifetime=5, parent=player)


def activate_erosion(victim, attacker, damage):
    try:
        index = index_from_userid(victim)
    except ValueError:
        from warnings import warn
        warn('Stop repeat')
    else:
        try:
            attacker = index_from_userid(attacker)
        except ValueError:
            attacker = 0

        AVSDPlayer.from_index(index).take_damage(damage, attacker, settings.name, 'erosion')


def _dyncall_magical_eruption(avsdplayer):
    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player
        origin = player.get_view_coordinates()

        if origin is not None:
            skill = avsdplayer.passives['magical eruption']
            min_damage = skill['min_damage']
            max_damage = skill['max_damage']
            distance = skill['distance']
            attacker = player.index
            now = time()

            _class_ariel_magical_eruption.create(origin, lifetime=5)

            skill = avsdplayer.skills['spellweaving']
            level = skill.level

            if level:
                min_chance = skill['min_chance']
                max_chance = skill['max_chance']

                chance = (level / skill.max) * (max_chance - min_chance) + min_chance

            for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
                if origin.get_distance_sqr(target.origin) <= distance ** 2:
                    avsdtarget = AVSDPlayer.from_index(target.index)

                    if avsdtarget.data['amplify magic'].get('duration', 0) >= now:
                        damage = randint(round(min_damage * 1.5), round(max_damage * 1.5))
                    else:
                        damage = randint(min_damage, max_damage)

                    if level:
                        if randint(0, 100) < chance:
                            damage *= skill['damage_multiplier']

                    prepare_erosion(avsdtarget, avsdplayer, now)

                    avsdtarget.take_delayed_damage(damage, attacker, settings.name, 'magical eruption')


def _dyncall_amplify_magic(avsdplayer, now):
    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player
        origin = player.get_view_coordinates()

        if origin is not None:
            skill = avsdplayer.passives['amplify magic']

            duration = now + skill['duration']
            distance = skill['distance']

            _class_ariel_amplify_magic.create(origin, lifetime=5)

            for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
                if origin.get_distance_sqr(target.origin) <= distance ** 2:
                    avsdtarget = AVSDPlayer.from_index(target.index)

                    if avsdtarget.data['amplify magic'].get('duration', 0) < duration:
                        avsdtarget.data['amplify magic']['duration'] = duration

                        prepare_erosion(avsdtarget, avsdplayer, now)

            avsdplayer.data['amplify magic']['cooldown'] = now + skill['cooldown']


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_death')
def player_death(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    delay = avsdplayer.data['icy binding'].get('unfreeze')

    if delay is not None:
        if delay.running:
            delay()

    repeat = avsdplayer.data['erosion'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()


@Event('round_prestart')
def round_prestart(event):
    for _, avsdplayer in PlayerReadyIter():
        delay = avsdplayer.data['icy binding'].get('unfreeze')

        if delay is not None:
            if delay.running:
                delay()


# ============================================================================
# >> LISTENERS
# ============================================================================
# TODO: Check if this is where the Vector::DistTo crashes
@OnPlayerAttackPost
def on_player_attack_post(avsdplayer, player, weapon, is_attack1):
    if avsdplayer.current_class == settings.name:
        if weapon.class_name in melee_weapons:
            if is_attack1:
                player.delay(0, _dyncall_magical_eruption, args=(avsdplayer, ))
            else:
                now = time()

                if avsdplayer.data['amplify magic'].get('cooldown', 0) <= now:
                    player.delay(0, _dyncall_amplify_magic, args=(avsdplayer, now))


@OnPlayerAttackPre
def on_player_attack_pre(avsdplayer, player, weapon, is_attack1, data):
    if avsdplayer.current_class == settings.name:
        if weapon.class_name in melee_weapons:
            skill = avsdplayer.skills['spellweaving']
            level = skill.level

            if level:
                data['rate'] += skill['rate']


@OnPlayerUIDebuffPre
def on_player_ui_debuff_pre(avsdplayer, class_, language, messages, now):
    duration = avsdplayer.data['amplify magic'].get('duration', 0)

    if duration >= now:
        messages.append('amplify magic: {0:.1f}'.format(duration - now))


@OnPlayerDelete
def on_player_delete(avsdplayer):
    delay = avsdplayer.data['icy binding'].get('delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    delay = avsdplayer.data['icy binding'].get('unfreeze')

    if delay is not None:
        if delay.running:
            delay.cancel()

    repeat = avsdplayer.data['erosion'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()


@OnPlayerFlyUpdatePre
def on_player_pre_fly_update(avsdplayer, data):
    if data['state']:
        if avsdplayer.data['purifying bolt'].get('active'):
            data['allow'] = False


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class TempestAbility(Ability):
    name = 'tempest'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        index = player.index
        origin = player.origin
        radius = skill['radius']
        max_distance_max_damage = skill['max_distance_max_damage']
        max_distance_min_damage = skill['max_distance_min_damage']
        min_distance_max_damage = skill['min_distance_max_damage']
        min_distance_min_damage = skill['min_distance_min_damage']

        min_damage = (skill.level / skill.max) * (max_distance_max_damage - max_distance_min_damage) + max_distance_min_damage
        max_damage = (skill.level / skill.max) * (min_distance_max_damage - min_distance_min_damage) + min_distance_min_damage

        total_damage = (max_damage - min_damage) + min_damage

        _class_ariel_tempest.create(origin, lifetime=5)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            distance = origin.get_distance_sqr(target.origin)

            if distance <= radius ** 2:
                # TODO: Check if this is still valid
                damage = (1 - distance / radius) * total_damage

                avsdtarget = AVSDPlayer.from_index(target.index)

                if avsdtarget.data['amplify magic'].get('duration', 0) >= now:
                    damage *= 1.5

                avsdtarget.take_damage(damage, index, settings.name, self.name)

                target.base_velocity = (target.origin - origin) / (distance / radius) * 4

                prepare_erosion(avsdtarget, avsdplayer, now)


@settings.ability
class IcyBindingAbility(Ability):
    name = 'icy binding'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        radius = skill['radius']
        initial_damage = skill['initial_damage']
        speed = skill['speed']

        zone = IcyBindingZone(avsdplayer, origin, radius, slow=speed, team=5 - player.team_index, attacker=player.index)

        zone_manager.append(zone)

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']
        avsdplayer.data[self.name]['zone'] = zone

        _class_ariel_icy_binding.create(origin, lifetime=5)

        for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
            if origin.get_distance_sqr(target.origin) <= radius ** 2:
                avsdtarget = AVSDPlayer.from_index(target.index)
                avsdtarget.take_damage(initial_damage, player.index, settings.name, self.name)

                prepare_erosion(avsdtarget, avsdplayer, now)

        avsdplayer.data[self.name]['delay'] = Delay(skill['explode_timer'], icy_binding_remove_zone, args=(zone, skill['explode_damage'], skill['freeze_timer']))


@settings.ability
class PurifyingBoltAbility(Ability):
    name = 'purifying bolt'

    def activate(self, avsdplayer, skill, player, now):
        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        PurifyingBoltSkillshot(avsdplayer, duration=skill['duration'], zone_radius=skill['radius'], damage=skill['damage'], team=5 - player.team_index, attacker=avsdplayer.userid)


@settings.ability
class ZephyrSphereAbility(Ability):
    name = 'zephyr sphere'

    def activate(self, avsdplayer, skill, player, now):
        projectile = avsdplayer.data[self.name].pop('projectile', None)

        if projectile is not None:
            try:
                entity = projectile.entity
            except ValueError:
                pass
            else:
                origin = player.origin
                target = entity.origin

                target -= origin
                target *= skill['multiplier']

                player.teleport(velocity=target)

            projectile.remove()

            return

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        avsdplayer.data[self.name]['projectile'] = ZephyrSphereSkillshot(avsdplayer, damage=randint(skill['min_damage'], skill['max_damage']), team=player.team_index, attacker=avsdplayer.userid)

    def get_cooldown(self, avsdplayer):
        return 0 if avsdplayer.data[self.name].get('projectile') is not None else super().get_cooldown(avsdplayer)
