# ../avsd/modules/classes/buer.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
from collections import defaultdict
#   Enum
from enum import IntEnum
#   Random
from random import randint
#   Time
from time import time

# Source.Python Imports
#   Colors
from colors import Color
#   Engines
from engines.precache import Model
#   Entities
from entities.constants import MoveType
from entities.constants import RenderEffects
from entities.constants import RenderMode
from entities.entity import Entity
from entities.helpers import index_from_inthandle
#   Events
from events import Event
#   Listeners
from listeners import OnLevelInit
from listeners.tick import Delay
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Mathlib
from mathlib import Vector
#   Menus
from menus import SimpleMenu
from menus import SimpleOption
from menus import Text

# AvsD Imports
#   Area
from ...core.area.aura import Aura
from ...core.area.aura import aura_manager
from ...core.area.zone import SphereZone
from ...core.area.zone import zone_manager
#   Helpers
from ...core.helpers.particle import Particle
#   Listeners
from ...core.listeners import OnPlayerAscendPost
from ...core.listeners import OnPlayerUIBuffPre
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerReady
from ...core.listeners import OnPlayerReset
from ...core.listeners import OnPlayerSwitchClass
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnPlayerUpgradeSkill
from ...core.listeners import OnPluginUnload
from ...core.listeners import OnTakeDamage
from ...core.listeners import OnTraceAttack
#   Menus
from ...core.menus import ability_menu
#   Modules
from ...core.modules.classes.ability import Ability
from ...core.modules.classes.settings import Settings
#   Players
from ...core.players.entity import Player as AVSDPlayer
from ...core.players.filters import PlayerReadyIter
#   Translations
from ...core.translations import menu_strings


# ============================================================================
# >> CLASSES
# ============================================================================
class PandemonicBlessings(IntEnum):
    FEATHER_OF_THE_GARUDA = 0
    HEART_OF_THE_HYDRA = 1
    SCALE_OF_THE_LEVIATHAN = 2


class BloodWyrmAura(Aura):
    target_particle = Particle('_Class_Buer_Healing_Spirit_2', lifetime=5, offsets=[0, 0, 32])

    def on_enter_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if 'active' not in avsdtarget.data['blood wyrm']:
            avsdtarget.data['blood wyrm']['active'] = []

        avsdtarget.data['blood wyrm']['active'].append(self)

        if len(avsdtarget.data['blood wyrm']['active']) == 1:
            self.on_update_aura(target)

    def on_update_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.ready:
            if 'active' in avsdtarget.data['blood wyrm'] and avsdtarget.data['blood wyrm']['active']:
                if avsdtarget.data['blood wyrm']['active'][0] == self:
                    now = time()

                    if avsdtarget.data['blood wyrm'].get('cooldown', 0) < now:
                        avsdplayer = self.owner
                        skill = avsdplayer.skills['blood wyrm']
                        health = avsdtarget.stats.get('health')

                        if health is not None:
                            curhealth = target.health

                            if curhealth < health:
                                avsdtarget.data['blood wyrm']['cooldown'] = now + 5

                                percentage = skill.level / skill.max

                                min_ally_health_min = skill['min_ally_health_min']
                                min_ally_health_max = skill['min_ally_health_max']
                                max_ally_health_min = skill['max_ally_health_min']
                                max_ally_health_max = skill['max_ally_health_max']

                                min_health = percentage * (min_ally_health_max - min_ally_health_min) + min_ally_health_min
                                max_health = percentage * (max_ally_health_max - max_ally_health_min) + max_ally_health_min

                                value = randint(round(min_health), round(max_health))

                                target.health = min(curhealth + value, health)

                                health = avsdplayer.stats.get('health')

                                if health is not None:
                                    player = avsdplayer.player
                                    curhealth = player.health

                                    if curhealth < health:
                                        min_health_min = skill['min_health_min']
                                        min_health_max = skill['min_health_max']
                                        max_health_min = skill['max_health_min']
                                        max_health_max = skill['max_health_max']

                                        min_health = percentage * (min_health_max - min_health_min) + min_health_min
                                        max_health = percentage * (max_health_max - max_health_min) + max_health_min

                                        value = randint(round(min_health), round(max_health))

                                        player.health = min(curhealth + value, health)

                                self.set_particle(target, True)

                        # For item Blood-Soaked Cloth Armour (Buer)
                        armor_gained = skill.stats.get('armor_gained')

                        if armor_gained is not None:
                            armor = avsdplayer.stats.get('armor')

                            if armor is not None:
                                player = avsdplayer.player
                                curarmor = player.armor

                                if curhealth < armor:
                                    player.armor = min(curarmor + armor_gained, armor)

    def on_exit_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.ready:
            avsdtarget.data['blood wyrm']['active'].remove(self)

            self.set_particle(target, False)


class SigilOfDecayZone(SphereZone):
    def on_enter_zone(self, player):
        self.on_exit_zone(player)

    def on_exit_zone(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        if 'attackers' not in avsdplayer.data['sigil of decay']:
            avsdplayer.data['sigil of decay']['attackers'] = {}

        if self.data['attacker'] not in avsdplayer.data['sigil of decay']['attackers']:
            avsdplayer.data['sigil of decay']['attackers'][self.data['attacker']] = self.data['slow']

            attacker = max(avsdplayer.data['sigil of decay']['attackers'], key=avsdplayer.data['sigil of decay']['attackers'].get)
            max_ = avsdplayer.data['sigil of decay']['attackers'][attacker]
            slowed = avsdplayer.data['sigil of decay'].get('slowed', 0)

            if max_ > slowed:
                player.speed -= max_ - slowed

                avsdplayer.stats['speed'] -= max_ - slowed
                avsdplayer.stats['flyspeed'] -= max_ - slowed

                avsdplayer.data['sigil of decay']['slowed'] = max_

        delay = avsdplayer.data['sigil of decay'].get('delay')

        if delay is not None:
            if delay.running:
                delay.cancel()

        avsdplayer.data['sigil of decay']['delay'] = Delay(self.data['duration'], self.sigil_of_decay_speed, args=(avsdplayer, ))

        repeat = avsdplayer.data['sigil of decay'].get('repeat')

        if repeat is not None:
            repeat.stop()

        repeat = avsdplayer.data['sigil of decay']['repeat'] = Repeat(self.sigil_of_decay_damage, args=(avsdplayer, ))
        repeat.start(1, self.data['duration'])

    def on_remove_zone(self):
        for index in self.entities:
            avsdplayer = AVSDPlayer.from_index(index)

            if 'attackers' in avsdplayer.data['sigil of decay'] and self.data['attacker'] in avsdplayer.data['sigil of decay']['attackers']:
                delay = avsdplayer.data['sigil of decay'].get('delay')

                if delay is not None:
                    if delay.running:
                        delay.cancel()

                avsdplayer.data['sigil of decay']['delay'] = Delay(self.data['duration'], self.sigil_of_decay_speed, args=(avsdplayer, ))

                repeat = avsdplayer.data['sigil of decay'].get('repeat')

                if repeat is not None:
                    repeat.stop()

                repeat = avsdplayer.data['sigil of decay']['repeat'] = Repeat(self.sigil_of_decay_damage, args=(avsdplayer, ))
                repeat.start(1, self.data['duration'])

    def on_client_disconnect(self, player):
        avsdplayer = AVSDPlayer.from_index(player.index)

        delay = avsdplayer.data['sigil of decay'].get('delay')

        if delay is not None and delay.running:
            delay.cancel()

        repeat = avsdplayer.data['sigil of decay'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

    def sigil_of_decay_speed(self, avsdplayer):
        attacker = self.data['attacker']
        player = avsdplayer.player

        del avsdplayer.data['sigil of decay']['attackers'][attacker]

        slowed = avsdplayer.data['sigil of decay']['slowed']

        if avsdplayer.data['sigil of decay']['attackers']:
            attacker = max(avsdplayer.data['sigil of decay']['attackers'], key=avsdplayer.data['sigil of decay']['attackers'].get)
            max_ = avsdplayer.data['sigil of decay']['attackers'][attacker]

            if max_ < slowed:
                player.speed += slowed - max_

                avsdplayer.stats['speed'] += slowed - max_
                avsdplayer.stats['flyspeed'] += slowed - max_
        else:
            player.speed += slowed

            avsdplayer.stats['speed'] += slowed
            avsdplayer.stats['flyspeed'] += slowed

            del avsdplayer.data['sigil of decay']['slowed']

    def sigil_of_decay_damage(self, avsdplayer):
        attacker = self.data['attacker']
        min_damage = self.data['min_damage']
        max_damage = self.data['max_damage']

        damage = randint(min_damage, max_damage)
        player = avsdplayer.player

        if player.health > damage:
            avsdplayer.take_damage(damage, attacker, settings.name, 'sigil of decay')


class SpiritZone(SphereZone):
    def on_enter_zone(self, player):
        pass

    def on_exit_zone(self, player):
        pass


class Spirits(object):
    def __init__(self, avsdplayer):
        self.avsdplayer = avsdplayer

        skill = avsdplayer.passives['spirits']
        skill2 = avsdplayer.skills['enslaving']

        self.count = skill['spawn']
        self.max = skill['spawn']

        self.interval = skill['interval']

        if skill2.level:
            self.interval -= skill2.level

            if self.interval <= 0:
                from warnings import warn
                warn('Spirits less than 0: {0}'.format(self.interval))

            if skill2.level == skill2.max:
                self.max += 1

        self.inthandle = None
        self.spirits = []

        self.repeat = Repeat(self.recovery)
        self.repeat.start(self.interval)

    def recovery(self):
        if self.interval <= 0:
            from warnings import warn
            warn('Spirits less than 0: {0}'.format(self.interval))

        if self.count < self.max:
            self.count += 1

            self.update()

    def update(self):
        player = self.avsdplayer.player
        origin = player.origin
        origin[2] += 20

        if self.inthandle is not None:
            try:
                parent = Entity(index_from_inthandle(self.inthandle))
            except ValueError:
                self.inthandle = None

                for particle in self.spirits:
                    particle.remove()

                self.spirits.clear()

        if self.inthandle is None:
            entity = Entity.create('func_rotating')
            entity.origin = origin
            entity.spawnflags = 65
            entity.maxspeed = 180
            entity.render_mode = RenderMode.NORMAL
            entity.render_fx = RenderEffects.NONE
            entity.render_color = Color(0, 0, 0, 0)
            entity.move_type = MoveType.FLY

            entity.set_property_ushort('m_Collision.m_usSolidFlags', 8)
            entity.set_property_uchar('m_CollisionGroup', 2)
            entity.set_property_uchar('m_nSolidType', 2)

            entity.spawn()

            entity.model = MODEL

            effects = entity.get_property_ushort('m_fEffects')
            effects |= 32
            entity.set_property_ushort('m_fEffects', effects)

            entity.call_input('Start')
            entity.set_parent(player, -1)

            self.inthandle = entity.basehandle.to_int()

            parent = entity

        for _ in range(self.count - len(self.spirits)):
            self.spirits.append(_class_buer_spirit.create(origin, parent=parent))

        while self.count < len(self.spirits):
            self.spirits.pop(0).remove()

        if self.count:
            locations = spirits_location[self.count]

            for i, particle in enumerate(self.spirits):
                particle.entity.origin = origin + locations[i]

    def delete(self):
        if self.inthandle is not None:
            try:
                entity = Entity(index_from_inthandle(self.inthandle))
            except ValueError:
                pass
            else:
                if entity.class_name == 'func_rotating':
                    entity.remove()

        for particle in self.spirits:
            particle.remove()

        self.inthandle = None
        self.spirits.clear()


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
_class_buer_spirit = Particle('_Class_Buer_Spirit_4')
_class_buer_malevolent_spirit = Particle('_Class_Buer_Malevolent_Spirit', lifetime=5)
_class_buer_garuda = Particle('_Class_Buer_Garuda')
_class_buer_hydra = Particle('_Class_Buer_Hydra')
_class_buer_leviathan = Particle('_Class_Buer_Leviathan')
_class_buer_sigil_of_decay = Particle('_Class_Buer_Sigil_Of_Decay', lifetime=5)
_class_buer_familiar = Particle('_Class_Buer_Familiar_copy')
menu = SimpleMenu(
    [
        Text(settings.strings['menu title']),
        ' ',
        SimpleOption(1, settings.strings['menu line 1'], PandemonicBlessings.FEATHER_OF_THE_GARUDA),
        SimpleOption(2, settings.strings['menu line 2'], PandemonicBlessings.HEART_OF_THE_HYDRA),
        SimpleOption(3, settings.strings['menu line 3'], PandemonicBlessings.SCALE_OF_THE_LEVIATHAN),
        ' ',
        ' ',
        ' ',
        SimpleOption(7, menu_strings['back'], ability_menu),
        ' ',
        SimpleOption(9, menu_strings['close'], highlight=False),
    ])
spirits_location = {
    1:[
        Vector(0, 55, 0),
    ],
    2:[
        Vector(0, 55, 0),
        Vector(0, -55, 0),
    ],
    3:[
        Vector(0, 55, 0),
        Vector(-44.6875, -34.375, 0),
        Vector(44.6875, -34.375, 0),
    ],
    4:[
        Vector(43, 43, 0),
        Vector(-43, -43, 0),
        Vector(43, -43, 0),
        Vector(-43, 43, 0),
    ],
    5:[
        Vector(0, 62.5, 0),
        Vector(-59.375, 18.75, 0),
        Vector(-37.5, -50, 0),
        Vector(37.5, -50, 0),
        Vector(59.375, 18.75, 0),
    ],
}

MODEL = Model('models/error.mdl')


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    if avsdplayer.ready:
        if avsdplayer.current_class == settings.name:
            player = avsdplayer.player

            if not player.dead and player.team_index in (2, 3):
                manager = avsdplayer.data['spirits'].get('manager')

                if manager is None:
                    manager = avsdplayer.data['spirits']['manager'] = Spirits(avsdplayer)
                else:
                    avsdplayer.data['spirits']['manager'].delete()

                avsdplayer.data['spirits']['manager'].update()

                skill = avsdplayer.skills['blood wyrm']
                level = skill.level

                if level:
                    min_distance = skill['min_distance']
                    max_distance = skill['max_distance']

                    distance = (level / skill.max) * (max_distance - min_distance) + min_distance

                    aura = avsdplayer.data['blood wyrm'].pop('aura', None)

                    if aura is not None:
                        aura_manager.remove(aura)

                    aura = BloodWyrmAura(avsdplayer, distance, team=player.team_index)

                    aura_manager.append(aura)

                    avsdplayer.data['blood wyrm']['aura'] = aura


@Event('player_death')
def player_death(event):
    avsdplayer = AVSDPlayer.from_userid(event['userid'])

    if avsdplayer.current_class == settings.name:
        aura = avsdplayer.data['blood wyrm'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)

        manager = avsdplayer.data['spirits'].get('manager')

        if manager is not None:
            avsdplayer.data['spirits']['manager'].delete()


@Event('round_prestart')
def round_prestart(event):
    spells = defaultdict(dict)

    for player, avsdplayer in PlayerReadyIter('alive'):
        if avsdplayer.current_class == settings.name:
            spell = avsdplayer.data['pandemonic blessings'].get('spell')

            if spell is not None:
                assert isinstance(spell, PandemonicBlessings)

                team = player.team_index

                if spell in spells[team]:
                    if avsdplayer.skills['pandemonic blessings'].level > spells[team][spell].skills['pandemonic blessings'].level:
                        spells[team][spell] = avsdplayer
                else:
                    spells[team][spell] = avsdplayer

        for item in ('flyspeed', 'health', 'armor'):
            value = avsdplayer.data['pandemonic blessings'].pop(item, None)

            if value is not None:
                avsdplayer.stats[item] -= value

    for team, data in spells.items():
        players = list(PlayerReadyIter(['alive', 't' if team == 2 else 'ct']))

        for spell, avsdplayer in data.items():
            index = avsdplayer.index
            skill = avsdplayer.skills['pandemonic blessings']

            if spell == PandemonicBlessings.FEATHER_OF_THE_GARUDA:
                min_value = skill['min_flyspeed']
                max_value = skill['max_flyspeed']
                multiplier = skill['flyspeed_multiplier']
            elif spell == PandemonicBlessings.HEART_OF_THE_HYDRA:
                min_value = skill['min_health']
                max_value = skill['max_health']
                multiplier = skill['health_multiplier']
            else:
                min_value = skill['min_armor']
                max_value = skill['max_armor']
                multiplier = skill['armor_multiplier']

            value = (skill.level / skill.max) * (max_value - min_value) + min_value

            for player, avsdtarget in players:
                if spell == PandemonicBlessings.FEATHER_OF_THE_GARUDA:
                    flyspeed = avsdplayer.stats.get('flyspeed', 1) * (1 + (value * multiplier if player.index == index else value) / 100)

                    avsdplayer.stats['flyspeed'] += flyspeed

                    avsdplayer.data['pandemonic blessings']['flyspeed'] = flyspeed
                elif spell == PandemonicBlessings.HEART_OF_THE_HYDRA:
                    health = avsdplayer.stats.get('health', 100) + round((value * multiplier if player.index == index else value))

                    avsdplayer.stats['health'] += health

                    avsdplayer.data['pandemonic blessings']['health'] = health
                else:
                    armor = avsdplayer.stats.get('armor', 0) + round((value * multiplier if player.index == index else value))

                    avsdplayer.stats['armor'] += armor

                    avsdplayer.data['pandemonic blessings']['armor'] = armor


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnLevelInit
def on_level_init(map_name):
    for _, avsdplayer in PlayerReadyIter():
        aura = avsdplayer.data['blood wyrm'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)


@OnPlayerAscendPost
def on_player_ascend_post(avsdplayer, class_):
    if class_.name == settings.name:
        manager = avsdplayer.data['spirits'].get('manager')

        if manager is not None:
            manager.repeat.stop()

            manager.delete()

        manager = avsdplayer.data['spirits']['manager'] = Spirits(avsdplayer)
        manager.update()


@OnPlayerUIBuffPre
def on_player_buff_pre(avsdplayer, class_, language, messages, now):
    if class_.name == settings.name:
        manager = avsdplayer.data['spirits'].get('manager')

        if manager is not None:
            messages.append(f'spirits: {manager.count}')


@OnPlayerDelete
def on_player_delete(avsdplayer):
    delay = avsdplayer.data['sigil of decay'].get('delay')

    if delay is not None:
        if delay.running:
            delay.cancel()

    repeat = avsdplayer.data['sigil of decay'].get('repeat')

    if repeat is not None:
        if repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

    if avsdplayer.current_class == settings.name:
        manager = avsdplayer.data['spirits'].get('manager')

        if manager is not None:
            manager.repeat.stop()

            manager.delete()

        aura = avsdplayer.data['blood wyrm'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)


@OnPlayerReady
def on_player_ready(avsdplayer):
    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player

        if not player.dead and player.team_index in (2, 3):
            skill = avsdplayer.skills['blood wyrm']
            level = skill.level

            if level:
                min_distance = skill['min_distance']
                max_distance = skill['max_distance']

                distance = (level / skill.max) * (max_distance - min_distance) + min_distance

                aura = avsdplayer.data['blood wyrm'].pop('aura', None)

                if aura is not None:
                    aura_manager.remove(aura)

                aura = BloodWyrmAura(avsdplayer, distance, team=player.team_index)

                aura_manager.append(aura)

                avsdplayer.data['blood wyrm']['aura'] = aura

            if 'manager' not in avsdplayer.data['spirits']:
                manager = avsdplayer.data['spirits']['manager'] = Spirits(avsdplayer)
                manager.update()


@OnPlayerReset
def on_player_reset(avsdplayer):
    if avsdplayer.current_class == settings.name:
        manager = avsdplayer.data['spirits']['manager']

        skill = avsdplayer.skills['enslaving']

        if skill.level == skill.max:
            manager.max -= 1

        manager.delete()


@OnPlayerSwitchClass
def on_player_switch_class(avsdplayer, old, new):
    for item in ('flyspeed', 'health', 'armor'):
        value = avsdplayer.data['pandemonic blessings'].get(item)

        if value is not None:
            avsdplayer.stats[item] -= value


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if old == settings.name:
        manager = avsdplayer.data['spirits'].pop('manager', None)

        if manager is not None:
            manager.delete()
            manager.repeat.stop()

        aura = avsdplayer.data['blood wyrm'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)

        if menu.is_active_menu(avsdplayer.player.index):
            menu.close(avsdplayer.player.index)
    elif new == settings.name and old is not None:
        on_player_ready(avsdplayer)


@OnPlayerUpgradeSkill
def on_player_upgrade_skill(avsdplayer, skill, old_level, new_level):
    if avsdplayer.current_class == settings.name:
        if not avsdplayer.player.dead:
            if skill.name == 'enslaving':
                manager = avsdplayer.data['spirits'].get('manager')

                if manager is not None:
                    # Sue me
                    manager.repeat._interval -= (new_level - old_level)

                    if manager.repeat._interval <= 0:
                        from warnings import warn
                        warn('Spirits less than 0: {0}'.format(manager.repeat._interval))

                if new_level == skill.max:
                    avsdplayer.data['spirits']['manager'].max += 1
                    avsdplayer.data['spirits']['manager'].update()
            elif skill.name == 'blood wyrm':
                min_distance = skill['min_distance']
                max_distance = skill['max_distance']

                distance = (skill.level / skill.max) * (max_distance - min_distance) + min_distance

                aura = avsdplayer.data['blood wyrm'].pop('aura', None)

                if aura is not None:
                    aura_manager.remove(aura)

                aura = BloodWyrmAura(avsdplayer, distance, team=avsdplayer.player.team_index)

                aura_manager.append(aura)

                avsdplayer.data['blood wyrm']['aura'] = aura


@OnPluginUnload
def on_plugin_unload():
    for _, avsdplayer in PlayerReadyIter():
        manager = avsdplayer.data['spirits'].get('manager')

        if manager is not None:
            manager.delete()
            manager.repeat.stop()


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class PandemonicBlessingsAbility(Ability):
    name = 'pandemonic blessings'

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
class SigilOfDecayAbility(Ability):
    name = 'sigil of decay'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        _class_buer_sigil_of_decay.create(origin)

        radius = skill['radius']
        min_damage_min = skill['min_damage_min']
        min_damage_max = skill['min_damage_max']
        max_damage_min = skill['max_damage_min']
        max_damage_max = skill['max_damage_max']
        min_slow = skill['min_slow']
        max_slow = skill['max_slow']

        min_damage = (skill.level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
        max_damage = (skill.level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min
        slow = (skill.level / skill.max) * (max_slow - min_slow) + min_slow

        zone = SigilOfDecayZone(avsdplayer, origin, radius, slow=slow, duration=skill['duration'], min_damage=round(min_damage), max_damage=round(max_damage), team=5 - player.team_index, attacker=player.index)

        zone_manager.append(zone)

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']
        avsdplayer.data[self.name]['zone'] = zone

        avsdplayer.data[self.name]['delay'] = Delay(skill['duration'], zone_manager.remove, args=(zone, ))


@settings.ability
class SpiritAbility(Ability):
    name = 'spirit'

    def activate(self, avsdplayer, skill, player, now):
        origin = player.get_view_coordinates()

        if origin is None:
            return

        radius = skill['radius']
        min_ally_damage_boost = skill['min_ally_damage_boost']
        max_ally_damage_boost = skill['max_ally_damage_boost']
        min_speed_reduction = skill['min_speed_reduction']
        max_speed_reduction = skill['max_speed_reduction']

        _class_buer_familiar.create(origin, lifetime=5)

        zone = SpiritZone(avsdplayer, origin, radius)

        zone_manager.append(zone)

        avsdplayer.data[self.name]['cooldown'] = now + skill['cooldown']
        avsdplayer.data[self.name]['zone'] = zone

        avsdplayer.data[self.name]['delay'] = Delay(skill['duration'], zone_manager.remove, args=(zone, ))


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    now = time()

    if avsdvictim.data['malevolent spirits'].get('duration', 0) >= now:
        min_damage = avsdvictim.data['malevolent spirits']['min_damage']
        max_damage = avsdvictim.data['malevolent spirits']['max_damage']

        info.damage += randint(min_damage, max_damage)


@OnTraceAttack
def on_trace_attack(avsdvictim, avsdattacker, info):
    if avsdattacker is None:
        return

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            skill = avsdattacker.skills['malevolent spirits']
            level = skill.level

            if level:
                manager = avsdattacker.data['spirits'].get('manager')

                if manager is None:
                    manager = avsdattacker.data['spirits']['manager'] = Spirits(avsdattacker)

                if manager.count:
                    now = time()

                    if avsdvictim.data['malevolent spirits'].get('duration', 0) < now:
                        min_damage_min = skill['min_damage_min']
                        min_damage_max = skill['min_damage_max']
                        max_damage_min = skill['max_damage_min']
                        max_damage_max = skill['max_damage_max']

                        min_damage = (level / skill.max) * (min_damage_max - min_damage_min) + min_damage_min
                        max_damage = (level / skill.max) * (max_damage_max - max_damage_min) + max_damage_min

                        manager.count -= 1
                        manager.update()

                        avsdvictim.data['malevolent spirits']['duration'] = now + 10
                        avsdvictim.data['malevolent spirits']['min_damage'] = round(min_damage)
                        avsdvictim.data['malevolent spirits']['max_damage'] = round(max_damage)

                        _class_buer_malevolent_spirit.create(info.position, parent=avsdvictim.player)


# ============================================================================
# >> MENUS
# ============================================================================
@menu.register_select_callback
def menu_select(menu, client, option):
    if option.choice_index not in (1, 2, 3):
        if option.choice_index == 7:
            return option.value

        return

    avsdplayer = AVSDPlayer.from_index(client)

    assert avsdplayer.current_class == settings.name

    player = avsdplayer.player
    spell = option.value

    if spell == PandemonicBlessings.FEATHER_OF_THE_GARUDA:
        _class_buer_garuda.create(player.origin, lifetime=5)
    elif spell == PandemonicBlessings.HEART_OF_THE_HYDRA:
        _class_buer_hydra.create(player.origin, lifetime=5)
    else:
        _class_buer_leviathan.create(player.origin, lifetime=5)

    avsdplayer.data['pandemonic blessings']['spell'] = spell


@menu.register_build_callback
def menu_build(menu, client):
    avsdplayer = AVSDPlayer.from_index(client)
    spell = avsdplayer.data['pandemonic blessings'].get('spell')

    for option in menu[2:5]:
        option.selectable = option.highlight = option.value != spell
