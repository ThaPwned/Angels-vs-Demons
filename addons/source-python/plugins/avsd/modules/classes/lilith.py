# ../avsd/modules/classes/lilith.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Random
from random import choice
from random import randint
#   Time
from time import time

# Source.Python Imports
#   Engines
from engines.trace import engine_trace
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
from filters.weapons import WeaponClassIter
#   Listeners
from listeners.tick import Delay
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Messages
from messages import Shake
#   Players
from players.entity import Player
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
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerReset
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnPlayerUIBuffPre
from ...core.listeners import OnPlayerUICooldownPre
from ...core.listeners import OnPlayerUIInfoPre
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer
from ...core.players.filters import PlayerReadyIter
#   Translations
from ...core.translations import ui_strings


# ============================================================================
# >> CLASSES
# ============================================================================
class OrbOfSoulsSkillshot(Skillshot):
    particle = Particle('_Skill_Soul_Blast')

    def on_automatically_removed(self):
        self.owner.data['orb of souls'].pop('projectile', None)

    def on_start_touch(self, other):
        if other.class_name == 'player':
            if other.team_index != self.data['team']:
                avsdvictim = AVSDPlayer.from_index(other.index)

                prepare_vile_sorcery(avsdvictim, self.owner, time())

                health = self.owner.stats['health']
                player = self.owner.player

                if player.health < health:
                    player.health = min(health, player.health + self.data['lifesteal'])

                avsdvictim.take_delayed_damage(self.data['damage'], self.owner.index, settings.name, 'orb of souls')
            elif other.index == self.owner.index:
                return False

        self.owner.data['orb of souls'].pop('projectile', None)

        return True


class CorrosiveBloodCloudZone(SphereZone):
    zone_particle = Particle('_Class_Lilith_Blood_Clouds')

    def on_enter_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if 'attackers' not in avsdplayer.data['corrosive blood cloud']:
            avsdplayer.data['corrosive blood cloud']['attackers'] = {}

        avsdplayer.data['corrosive blood cloud']['attackers'][self.data['attacker']] = {'min_damage':self.data['min_damage'], 'max_damage':self.data['max_damage']}

        repeat = avsdplayer.data['corrosive blood cloud'].get('repeat')

        if repeat is None or repeat.status != RepeatStatus.RUNNING:
            repeat = avsdplayer.data['corrosive blood cloud']['repeat'] = Repeat(corrosive_blood_cloud_damage, args=(avsdplayer.userid, self.data['attacker'], self.data['min_damage'], self.data['max_damage']))
            repeat.start(0.5, 20)

        if 'slowdown' not in avsdplayer.data['corrosive blood cloud']:
            avsdattacker = AVSDPlayer.from_index(self.data['attacker'])

            if avsdattacker.current_class == settings.name:
                slow = avsdattacker.data['dark ritual'].get('corrosive_blood_cloud_slow')

                if slow is not None:
                    slowdown = player.speed * slow

                    player.speed -= slowdown

                    avsdplayer.stats['speed'] -= slowdown
                    avsdplayer.stats['flyspeed'] -= slowdown

                    avsdplayer.data['corrosive blood cloud']['slowdown'] = slowdown

    def on_exit_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        del avsdplayer.data['corrosive blood cloud']['attackers'][self.data['attacker']]

        avsdplayer.data['corrosive blood cloud']['repeat'].stop()

        if avsdplayer.data['corrosive blood cloud']['attackers']:
            attackers = avsdplayer.data['corrosive blood cloud']['attackers']
            attacker = choice(list(attackers.keys()))
            data = attackers[attacker]

            repeat = avsdplayer.data['corrosive blood cloud'].get('repeat')

            if repeat is not None:
                assert repeat.status != RepeatStatus.RUNNING

            repeat = avsdplayer.data['corrosive blood cloud']['repeat'] = Repeat(corrosive_blood_cloud_damage, args=(avsdplayer.userid, attacker, data['min_damage'], data['max_damage']))
            repeat.start(0.5, 20)
        else:
            if 'slowdown' in avsdplayer.data['corrosive blood cloud']:
                slowdown = avsdplayer.data['corrosive blood cloud'].pop('slowdown')

                player.speed += slowdown

                avsdplayer.stats['speed'] += slowdown
                avsdplayer.stats['flyspeed'] += slowdown

    def on_client_disconnect(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)
        repeat = avsdplayer.data['corrosive blood cloud'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()


class DarkRitualZone(SphereZone):
    zone_particle = Particle('Class_Lilith_Sacrificial_Pact_Core')

    def on_enter_zone(self, player):
        if player.index == self.owner.index:
            avsdplayer = self.owner

            skill = avsdplayer.skills['dark ritual']

            min_netherbolt_damage_percentage = skill['min_netherbolt_damage_percentage']
            max_netherbolt_damage_percentage = skill['max_netherbolt_damage_percentage']
            min_blood_aura_health_regen = skill['min_blood_aura_health_regen']
            max_blood_aura_health_regen = skill['max_blood_aura_health_regen']
            meteor_damage_multiplier = skill['meteor_damage_multiplier']
            corrosive_blood_cloud_slow = skill['corrosive_blood_cloud_slow']
            vile_sorcery_count = skill['vile_sorcery_count']

            netherbolt_damage_percentage = (skill.level / skill.max) * (max_netherbolt_damage_percentage - min_netherbolt_damage_percentage) + min_netherbolt_damage_percentage
            blood_aura_health_regen = (skill.level / skill.max) * (max_blood_aura_health_regen - min_blood_aura_health_regen) + min_blood_aura_health_regen

            avsdplayer.data['dark ritual']['netherbolt_damage_percentage'] = netherbolt_damage_percentage / 100 + 1
            avsdplayer.data['dark ritual']['blood_aura_health_regen'] = blood_aura_health_regen
            avsdplayer.data['dark ritual']['meteor_damage_multiplier'] = meteor_damage_multiplier
            avsdplayer.data['dark ritual']['corrosive_blood_cloud_slow'] = corrosive_blood_cloud_slow
            avsdplayer.data['dark ritual']['vile_sorcery_count'] = vile_sorcery_count

            avsdplayer.stats['hregen'] += blood_aura_health_regen

    def on_exit_zone(self, player):
        if player.index == self.owner.index:
            avsdplayer = self.owner

            del avsdplayer.data['dark ritual']['netherbolt_damage_percentage']
            del avsdplayer.data['dark ritual']['meteor_damage_multiplier']
            del avsdplayer.data['dark ritual']['corrosive_blood_cloud_slow']
            del avsdplayer.data['dark ritual']['vile_sorcery_count']

            avsdplayer.stats['hregen'] -= avsdplayer.data['dark ritual'].pop('blood_aura_health_regen')


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
melee_weapons = [x.name for x in WeaponClassIter('melee')]
_class_lilith_netherbolt = Particle('_Class_Lilith_Netherbolt')
_class_lilith_aura = Particle('_Class_Lilith_Aura')
_class_lilith_meteor = Particle('_Class_Lilith_Meteor')
_class_lilith_blood_sprout = Particle('_Class_Lilith_Blood_Sprout')
_class_lilith_skulls = Particle('_Class_Lilith_Skulls')


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def meteor_explode(origin, team, attacker, distance, min_damage, max_damage):
    try:
        attacker_index = index_from_userid(attacker)
    except ValueError:
        attacker_index = 0
    else:
        avsdplayer = AVSDPlayer.from_userid(attacker)

    now = time()

    for player in PlayerIter(['alive', 't' if team == 3 else 'ct']):
        if origin.get_distance_sqr(player.origin) <= distance ** 2:
            AVSDPlayer.from_index(player.index).take_damage(randint(min_damage, max_damage), attacker_index, settings.name, 'meteor')

            if attacker_index:
                prepare_vile_sorcery(AVSDPlayer.from_index(player.index), avsdplayer, now)

            Shake(amplitude=20, duration=3).send(player.index)


def corrosive_blood_cloud_remove_zone(zone):
    zone_manager.remove(zone)

    for index in zone.entities:
        player = Player(index)

        if zone.data['team'] != player.team_index:
            avsdplayer = AVSDPlayer.from_index(player.index)

            del avsdplayer.data['corrosive blood cloud']['attackers'][zone.data['attacker']]

            avsdplayer.data['corrosive blood cloud']['repeat'].stop()

            if avsdplayer.data['corrosive blood cloud']['attackers']:
                attackers = avsdplayer.data['corrosive blood cloud']['attackers']
                attacker = choice(list(attackers.keys()))
                data = attackers[attacker]

                repeat = avsdplayer.data['corrosive blood cloud'].get('repeat')

                if repeat is not None:
                    assert repeat.status != RepeatStatus.RUNNING

                repeat = avsdplayer.data['corrosive blood cloud']['repeat'] = Repeat(corrosive_blood_cloud_damage, args=(avsdplayer.userid, attacker, data['min_damage'], data['max_damage']))
                repeat.start(0.5, 20)
            else:
                if 'slowdown' in avsdplayer.data['corrosive blood cloud']:
                    slowdown = avsdplayer.data['corrosive blood cloud'].pop('slowdown')

                    player.speed += slowdown

                    avsdplayer.stats['speed'] += slowdown
                    avsdplayer.stats['flyspeed'] += slowdown


def corrosive_blood_cloud_damage(victim, attacker, min_damage, max_damage):
    avsdtarget = AVSDPlayer.from_userid(victim)

    avsdtarget.take_damage(randint(min_damage, max_damage), attacker, settings.name, 'corrosive blood cloud')

    prepare_vile_sorcery(avsdtarget, attacker, time())


def prepare_vile_sorcery(avsdtarget, avsdplayer, now):
    if not isinstance(avsdplayer, AVSDPlayer):
        avsdplayer = AVSDPlayer.from_index(avsdplayer)

    if avsdplayer.current_class == settings.name:
        skill = avsdplayer.skills['vile sorcery']
    else:
        skill = avsdplayer.classes[settings.name].skills['vile sorcery']

    level = skill.level

    if level:
        if avsdtarget.data['vile sorcery'].get('cooldown', 0) < now:
            avsdtarget.data['vile sorcery']['cooldown'] = now + skill['cooldown']

            min_damage_min = skill['min_damage_min']
            min_damage_max = skill['min_damage_max']
            max_damage_min = skill['max_damage_min']
            max_damage_max = skill['max_damage_max']

            min_damage = (level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
            max_damage = (level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min

            duration = skill['duration']

            duration += avsdplayer.data['dark ritual'].get('vile_sorcery_count', 0)

            repeat = avsdtarget.data['vile sorcery'].get('repeat')

            if repeat is not None and repeat.status == RepeatStatus.RUNNING:
                raise RuntimeError()

            repeat = avsdtarget.data['vile sorcery']['repeat'] = Repeat(activate_vile_sorcery, args=(avsdtarget.userid, avsdplayer.userid, round(min_damage), round(max_damage)))
            repeat.start(1, duration)

            player = avsdtarget.player

            _class_lilith_blood_sprout.create(player.origin, parent=player, lifetime=5)


def activate_vile_sorcery(victim, attacker, min_damage, max_damage):
    try:
        attacker = index_from_userid(attacker)
    except ValueError:
        pass
    else:
        AVSDPlayer.from_userid(victim).take_damage(randint(min_damage, max_damage), attacker, settings.name, 'vile sorcery')


def _dyncall_netherbolt(avsdplayer):
    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player
        origin = player.get_view_coordinates()

        if origin is not None:
            _class_lilith_netherbolt.create(origin, lifetime=5)

            skill = avsdplayer.passives['netherbolt']
            min_damage = skill['min_damage']
            max_damage = skill['max_damage']
            distance = skill['distance']
            index = player.index
            now = time()

            count = avsdplayer.data['skull collection'].get('count')

            if count is not None:
                min_damage += count
                max_damage += count

            count = avsdplayer.data['dark ritual'].get('netherbolt_damage_percentage')

            if count is not None:
                min_damage = round(min_damage * count)
                max_damage = round(max_damage * count)

            did_hit = False

            for target in PlayerIter(['alive', 'ct' if player.team_index == 2 else 't']):
                if origin.get_distance_sqr(target.origin) <= distance ** 2:
                    AVSDPlayer.from_index(target.index).take_damage(randint(min_damage, max_damage), index, settings.name, 'netherbolt')

                    prepare_vile_sorcery(AVSDPlayer.from_index(target.index), avsdplayer, now)

                    did_hit = True

            if did_hit:
                if 'particle' in avsdplayer.data['blood aura']:
                    health = avsdplayer.stats['health']

                    if player.health < health:
                        min_lifesteal = skill['min_lifesteal']
                        max_lifesteal = skill['max_lifesteal']

                        lifesteal = randint(min_lifesteal, max_lifesteal)

                        player.health = min(health, player.health + lifesteal)


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    userid = event['userid']
    avsdplayer = AVSDPlayer.from_userid(userid)

    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player

        if not player.dead and player.team_index in (2, 3):
            avsdplayer.data['blood aura'].pop('particle', None)


@Event('player_death')
def player_death(event):
    attacker = event['attacker']

    if attacker:
        avsdplayer = AVSDPlayer.from_userid(attacker)

        if avsdplayer.current_class == settings.name:
            skill = avsdplayer.skills['skull collection']
            level = skill.level

            if level:
                if 'count' not in avsdplayer.data['skull collection']:
                    avsdplayer.data['skull collection']['count'] = 0

                min_skulls = skill['min_skulls']
                max_skulls = skill['max_skulls']

                skulls = (skill.level / skill.max) * (max_skulls - min_skulls) + min_skulls

                if round(skulls) > avsdplayer.data['skull collection']['count']:
                    avsdplayer.data['skull collection']['count'] += 1

                    player = avsdplayer.player

                    _class_lilith_skulls.create(player.origin, parent=player, lifetime=5)

            # For item Caster of Corrosion
            chance = avsdplayer.skills['corrosive blood cloud'].stats.get('chance')

            if chance is not None:
                if chance >= randint(100):
                    pass
                    # distance = skill['distance']

                    # min_damage_min = skill['min_damage_min']
                    # min_damage_max = skill['min_damage_max']
                    # max_damage_min = skill['max_damage_min']
                    # max_damage_max = skill['max_damage_max']

                    # min_damage = (skill.level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
                    # max_damage = (skill.level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min

                    # zone = CorrosiveBloodCloudZone(avsdplayer, origin, distance, team=5 - player.team_index, attacker=player.index, min_damage=round(min_damage), max_damage=round(max_damage))

                    # zone_manager.append(zone)

                    # avsdplayer.data[self.name]['zone'] = zone
                    # avsdplayer.data[self.name]['delay'] = Delay(skill['duration'], corrosive_blood_cloud_remove_zone, args=(zone, ))

    avsdtarget = AVSDPlayer.from_userid(event['userid'])

    repeat = avsdtarget.data['vile sorcery'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

    repeat = avsdtarget.data['corrosive blood cloud'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

    if avsdtarget.current_class == settings.name:
        particle = avsdtarget.data['blood aura'].pop('particle', None)

        if particle is not None:
            particle.remove()

            slow = avsdtarget.data['blood aura']['slow']

            avsdtarget.stats['speed'] += slow
            avsdtarget.stats['flyspeed'] += slow

        # if 'particle' in avsdtarget.data['blood aura']:
        #     slow = avsdtarget.data['blood aura']['slow']

        #     avsdtarget.stats['speed'] += slow
        #     avsdtarget.stats['flyspeed'] += slow

        #     particle = avsdtarget.data['blood aura'].pop('particle', None)

        #     if particle is not None:
        #         particle.remove()


@Event('round_prestart')
def round_prestart(event):
    for player, avsdplayer in PlayerReadyIter():
        avsdplayer.data['orb of souls'].pop('index', None)

        if avsdplayer.current_class == settings.name:
            particle = avsdplayer.data['blood aura'].pop('particle', None)

            # if 'particle' in avsdplayer.data['blood aura']:
            if particle is not None:
                particle.remove()

                slow = avsdplayer.data['blood aura']['slow']

                player.speed += slow

                avsdplayer.stats['speed'] += slow
                avsdplayer.stats['flyspeed'] += slow

                # particle = avsdplayer.data['blood aura'].pop('particle', None)

                # if particle is not None:
                #     particle.remove()

        repeat = avsdplayer.data['vile sorcery'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()


# ============================================================================
# >> LISTENERS
# ============================================================================
# TODO: Check if this is where the Vector::DistTo crashes
@OnPlayerAttackPost
def on_player_attack_post(avsdplayer, player, weapon, is_attack1):
    if avsdplayer.current_class == settings.name:
        if weapon.class_name in melee_weapons:
            if is_attack1:
                player.delay(0, _dyncall_netherbolt, args=(avsdplayer, ))
            else:
                # TODO: Add this to a hudhint to make it easier to know when it's possible to toggle it
                now = time()

                if avsdplayer.data['blood aura'].get('cooldown', 0) <= now:
                    skill = avsdplayer.passives['blood aura']

                    avsdplayer.data['blood aura']['cooldown'] = now + skill['cooldown']

                    if 'particle' in avsdplayer.data['blood aura']:
                        slow = avsdplayer.data['blood aura']['slow']

                        player.speed += slow

                        avsdplayer.stats['speed'] += slow
                        avsdplayer.stats['flyspeed'] += slow

                        particle = avsdplayer.data['blood aura'].pop('particle', None)

                        if particle is not None:
                            particle.remove()
                    else:
                        slow = player.speed * 0.8

                        avsdplayer.data['blood aura']['slow'] = slow

                        player.speed -= slow

                        avsdplayer.stats['speed'] -= slow
                        avsdplayer.stats['flyspeed'] -= slow

                        avsdplayer.data['blood aura']['particle'] = _class_lilith_aura.create(player.origin, parent=player)


@OnPlayerDelete
def on_player_delete(avsdplayer):
    repeat = avsdplayer.data['vile sorcery'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

    # if avsdplayer.current_class == settings.name:
    repeat = avsdplayer.data['corrosive blood cloud'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()


@OnPlayerReset
def on_player_reset(avsdplayer):
    if avsdplayer.current_class == settings.name:
        skill = avsdplayer.skills['skull collection']
        level = skill.level

        if level:
            avsdplayer.data['skull collection'].pop('count', None)


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if old == settings.name:
        particle = avsdplayer.data['blood aura'].pop('particle', None)

        if particle is not None:
            particle.remove()

            slow = avsdplayer.data['blood aura']['slow']

            avsdplayer.player.speed += slow

            avsdplayer.stats['speed'] += slow
            avsdplayer.stats['flyspeed'] += slow


@OnPlayerUIBuffPre
def on_player_ui_buff_pre(avsdplayer, class_, language, messages, now):
    if avsdplayer.current_class == settings.name:
        count = avsdplayer.data['skull collection'].get('count')

        # TODO: Probably better to just check "if count"?
        if count is not None and count:
            messages.append(settings.strings['ui skull collection'].get_string(language, count=count))

        if 'particle' in avsdplayer.data['blood aura']:
            messages.append(settings.strings['ui blood aura'].get_string(language))


@OnPlayerUICooldownPre
def on_player_ui_cooldown_pre(avsdplayer, class_, language, messages, now):
    if avsdplayer.current_class == settings.name:
        cooldown = avsdplayer.data['blood aura'].get('cooldown', 0)

        if cooldown > now:
            messages.append(ui_strings['ui cooldown'].get_string(language, name=settings.strings['blood aura'].get_string(language), cooldown=cooldown - now))
        elif cooldown + 3 > now:
            messages.append(ui_strings['ui cooldown ready'].get_string(language, name=settings.strings['blood aura'].get_string(language)))


@OnPlayerUIInfoPre
def on_player_ui_info_pre(avsdplayer, class_, language, messages, now):
    if avsdplayer.current_class == settings.name:
        duration = avsdplayer.data['orb of souls'].get('failed')

        if duration is not None:
            now = time()

            if duration > now:
                messages.append(settings.strings['ui orb of souls'].get_string(language))
            else:
                # TODO: I guess this makes it perform a little bit better?
                del avsdplayer.data['orb of souls']['failed']


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class MeteorAbility(Ability):
    name = 'meteor'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        min_damage = skill['min_damage']
        max_damage = skill['max_damage']

        multiplier = avsdplayer.data['dark ritual'].get('meteor_damage_multiplier')

        if multiplier is not None:
            min_damage *= multiplier
            max_damage *= multiplier

        avsdplayer.data[self.name]['delay'] = Delay(0.25, meteor_explode, args=(origin, player.team_index, avsdplayer.userid, skill['distance'], min_damage, max_damage))

        _class_lilith_meteor.create(origin, lifetime=5)


@settings.ability
class CorrosiveBloodCloudAbility(Ability):
    name = 'corrosive blood cloud'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']

        distance = skill['distance']

        min_damage_min = skill['min_damage_min']
        min_damage_max = skill['min_damage_max']
        max_damage_min = skill['max_damage_min']
        max_damage_max = skill['max_damage_max']

        min_damage = (skill.level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
        max_damage = (skill.level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min

        zone = CorrosiveBloodCloudZone(avsdplayer, origin, distance, team=5 - player.team_index, attacker=player.index, min_damage=round(min_damage), max_damage=round(max_damage))

        zone_manager.append(zone)

        avsdplayer.data[self.name]['zone'] = zone
        avsdplayer.data[self.name]['delay'] = Delay(skill['duration'], corrosive_blood_cloud_remove_zone, args=(zone, ))


@settings.ability
class OrbOfSoulsAbility(Ability):
    name = 'orb of souls'

    def activate(self, avsdplayer, skill, player, now):
        projectile = avsdplayer.data[self.name].pop('projectile', None)

        if projectile is not None:
            try:
                entity = projectile.entity
            except ValueError:
                pass
            else:
                origin = entity.origin

                ray = Ray(origin, origin, player.mins, player.maxs)

                trace = GameTrace()

                engine_trace.trace_ray(ray, ContentMasks.ALL, TraceFilterSimple((entity, )), trace)

                if trace.did_hit():
                    avsdplayer.data[self.name]['failed'] = now + 2
                    return

                player.teleport(origin=origin)

            projectile.remove()

            return

        avsdplayer.data[self.name]['cooldown'] = now + 5

        min_damage = skill['min_damage']
        max_damage = skill['max_damage']
        min_lifesteal = skill['min_lifesteal']
        max_lifesteal = skill['max_lifesteal']

        damage = (skill.level / skill.max) * (max_damage - min_damage) + min_damage
        lifesteal = round((skill.level / skill.max) * (max_lifesteal - min_lifesteal) + min_lifesteal)

        avsdplayer.data[self.name]['projectile'] = OrbOfSoulsSkillshot(avsdplayer, damage=damage, lifesteal=lifesteal, team=player.team_index, attacker=avsdplayer.userid)

    def get_cooldown(self, avsdplayer):
        return 0 if avsdplayer.data[self.name].get('projectile') is not None else super().get_cooldown(avsdplayer)


@settings.ability
class DarkRitualAbility(Ability):
    name = 'dark ritual'

    def activate(self, avsdplayer, skill, player, now):
        if avsdplayer.data['skull collection'].get('count', 0) < 5:
            return

        origin = player.origin

        radius = skill['radius']

        zone = DarkRitualZone(avsdplayer, origin, radius)

        zone_manager.append(zone)

        avsdplayer.data['skull collection']['count'] -= 5

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']
        avsdplayer.data[self.name]['zone'] = zone

        avsdplayer.data[self.name]['delay'] = Delay(skill['duration'], zone_manager.remove, args=(zone, ))
