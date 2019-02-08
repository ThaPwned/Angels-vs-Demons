# ../avsd/modules/classes/raphael.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Enum
from enum import IntEnum
#   Random
from random import randint
#   Time
from time import time

# Source.Python Imports
#   Events
from events import Event
#   Listeners
from listeners.tick import Delay
from listeners.tick import Repeat
from listeners.tick import RepeatStatus
#   Menus
from menus import SimpleMenu
from menus import SimpleOption
from menus import Text
#   Messages
from messages import Shake
#   Weapons
from weapons.manager import weapon_manager

# AvsD Imports
#   Area
from ...core.area.aura import Aura
from ...core.area.aura import aura_manager
from ...core.area.zone import SphereZone
from ...core.area.zone import zone_manager
#   Helpers
from ...core.helpers.particle import Particle
#   Listeners
from ...core.listeners import OnPlayerDelete
from ...core.listeners import OnPlayerReady
from ...core.listeners import OnPlayerReset
from ...core.listeners import OnPlayerStatsUpdatePre
from ...core.listeners import OnPlayerSwitchClassPost
from ...core.listeners import OnPlayerUpgradeSkill
from ...core.listeners import OnPlayerUIBuffPre
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
class CelestialAuras(IntEnum):
    CERBERUS = 0
    PHOENIX = 1
    UNICORN = 2
    BEHEMOTH = 3
    DRAGON = 4
    FROST_GIANT = 5


class BestowZone(SphereZone):
    def on_enter_zone(self, player):
        self.on_update_zone(player)

    def on_update_zone(self, player):
        if player.dead:
            import traceback
            traceback.print_stack()

            with open('avsd_stack.txt', 'a') as f:
                f.writelines(traceback.format_stack())

        assert not player.dead

        active_weapon = player.active_weapon

        if active_weapon is not None:
            try:
                clip = active_weapon.clip
            except ValueError:
                pass
            else:
                max_clip = weapon_manager[active_weapon.classname].clip

                if clip < max_clip:
                    active_weapon.clip = min(clip + 1, max_clip)


class CerberusAura(Aura):
    owner_particle = Particle('_Class_Raphael_Aura_Ceberus')

    def on_update_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.ready:
            armor = target.armor

            if armor < avsdtarget.stats['armor']:
                target.armor = min(armor + self.data['value'], avsdtarget.stats['armor'])


class PhoenixAura(Aura):
    owner_particle = Particle('_Class_Raphael_Aura_Phoenix')

    def on_update_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.ready:
            health = target.health

            if health < avsdtarget.stats['health']:
                target.health = min(health + self.data['value'], avsdtarget.stats['health'])


class UnicornAura(Aura):
    owner_particle = Particle('_Class_Raphael_Aura_Unicorn')

    def on_enter_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)
        value = self.data['value']
        print('increasing', target.userid, value)

        avsdtarget.stats['speed'] += value
        avsdtarget.stats['flyspeed'] += value

        target.speed += value

        if 'value' not in avsdtarget.data['unicorn aura']:
            avsdtarget.data['unicorn aura']['value'] = 0

        avsdtarget.data['unicorn aura']['value'] += value

    def on_exit_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)
        value = self.data['value']
        print('decreasing', target.userid, value)

        avsdtarget.stats['speed'] -= value
        avsdtarget.stats['flyspeed'] -= value

        target.speed -= value

        avsdtarget.data['unicorn aura']['value'] -= value


class BehemothAura(Aura):
    owner_particle = Particle('_Class_Raphael_Aura_Behemoth')

    def on_update_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.ready:
            Shake(amplitude=self.data['value'], duration=3).send(target.index)


class DragonAura(Aura):
    owner_particle = Particle('_Class_Raphael_Aura_Dragon')

    def on_update_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)

        if avsdtarget.ready:
            health = target.health

            if health > 1:
                damage = randint(self.data['value'], self.data['value2'])

                if damage >= health:
                    damage = health - 1

                avsdtarget.take_damage(damage, self.owner.index, settings.name, 'celestial auras_dragon aura')


class FrostGiantAura(Aura):
    owner_particle = Particle('_Class_Raphael_Aura_Frost_Giant')

    def on_enter_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)
        value = self.data['value']

        avsdtarget.stats['speed'] -= value
        avsdtarget.stats['flyspeed'] -= value

        target.speed -= value

        if 'value' not in avsdtarget.data['frost giant aura']:
            avsdtarget.data['frost giant aura']['value'] = 0

        avsdtarget.data['frost giant aura']['value'] -= value

    def on_exit_aura(self, target):
        avsdtarget = AVSDPlayer.from_index(target.index)
        value = self.data['value']

        avsdtarget.stats['speed'] += value
        avsdtarget.stats['flyspeed'] += value

        target.speed += value

        avsdtarget.data['frost giant aura']['value'] += value


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
settings = Settings(__name__)
zone_delays = []
_class_raphael_bestow = Particle('_Class_Raphael_Bestow', lifetime=5)
_class_raphael_heavenly_touch = Particle('_Class_Raphael_Heavenly_Touch', lifetime=5)
_class_raphael_recovery = Particle('_Class_Raphael_Recovery', lifetime=5)
_class_raphael_empower = Particle('_Class_Raphael_Empower', lifetime=5)

menu = SimpleMenu(
    [
        Text(settings.strings['menu title']),
        ' ',
        SimpleOption(1, settings.strings['menu line 1'], CelestialAuras.CERBERUS),
        SimpleOption(2, settings.strings['menu line 2'], CelestialAuras.PHOENIX),
        SimpleOption(3, settings.strings['menu line 3'], CelestialAuras.UNICORN),
        SimpleOption(4, settings.strings['menu line 4'], CelestialAuras.BEHEMOTH),
        SimpleOption(5, settings.strings['menu line 5'], CelestialAuras.DRAGON),
        SimpleOption(6, settings.strings['menu line 6'], CelestialAuras.FROST_GIANT),
        SimpleOption(7, menu_strings['back'], ability_menu),
        ' ',
        SimpleOption(9, menu_strings['close'], highlight=False),
    ])


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    userid = event['userid']
    avsdplayer = AVSDPlayer.from_userid(userid)

    if avsdplayer.ready:
        if avsdplayer.current_class == settings.name:
            player = avsdplayer.player

            if not player.dead and player.team_index in (2, 3):
                skill = avsdplayer.skills['ancient power']
                level = skill.level

                if level:
                    avsdplayer.data['ancient power']['value'] = skill['max_value']

                    repeat = avsdplayer.data['ancient power'].get('repeat')

                    if repeat is not None and repeat.status == RepeatStatus.RUNNING:
                        repeat.stop()

                    repeat = avsdplayer.data['ancient power']['repeat'] = Repeat(ancient_power_regen, args=(avsdplayer, ))
                    repeat.start(skill['regen_interval'])


@Event('player_death')
def player_death(event):
    userid = event['userid']
    avsdplayer = AVSDPlayer.from_userid(userid)

    if avsdplayer.ready:
        if avsdplayer.current_class == settings.name:
            repeat = avsdplayer.data['ancient power'].get('repeat')

            if repeat is not None and repeat.status == RepeatStatus.RUNNING:
                repeat.stop()

            skill = avsdplayer.skills['bestow']
            level = skill.level

            if level:
                distance = skill['distance']
                min_duration = skill['min_duration']
                max_duration = skill['max_duration']

                duration = (level / skill.max) * (max_duration - min_duration) + min_duration

                player = avsdplayer.player
                origin = player.origin
                origin[2] -= 64

                zone = BestowZone(avsdplayer, origin, distance, team=player.team_index)

                zone_manager.append(zone)

                zone_delays.append(Delay(duration, zone_manager.remove, args=(zone, )))

                _class_raphael_bestow.create(origin)

            repeat = avsdplayer.data['recovery'].get('repeat')

            if repeat is not None and repeat.status == RepeatStatus.RUNNING:
                repeat.stop()


@Event('round_prestart')
def round_prestart(event):
    for delay in zone_delays:
        if delay.running:
            delay()

    zone_delays.clear()

    for _, avsdplayer in PlayerReadyIter():
        if avsdplayer.current_class == settings.name:
            repeat = avsdplayer.data['recovery'].get('repeat')

            if repeat is not None and repeat.status == RepeatStatus.RUNNING:
                repeat.stop()

            aura = avsdplayer.data['celestial auras'].pop('aura', None)

            if aura is not None:
                aura_manager.remove(aura)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerDelete
def on_player_delete(avsdplayer):
    if avsdplayer.current_class == settings.name:
        delay = avsdplayer.data['heavenly touch'].get('delay')

        if delay is not None and delay.running:
            delay.cancel()

        repeat = avsdplayer.data['heavenly touch'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        repeat = avsdplayer.data['recovery'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        repeat = avsdplayer.data['ancient power'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        aura = avsdplayer.data['celestial auras'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)


@OnPlayerReady
def on_player_ready(avsdplayer):
    if avsdplayer.current_class == settings.name:
        player = avsdplayer.player

        if not player.dead and player.team_index >= 2:
            skill = avsdplayer.skills['ancient power']
            level = skill.level

            if level:
                avsdplayer.data['ancient power']['value'] = skill['max_value']

                repeat = avsdplayer.data['ancient power'].get('repeat')

                if repeat is None or repeat.status != RepeatStatus.RUNNING:
                    repeat = avsdplayer.data['ancient power']['repeat'] = Repeat(ancient_power_regen, args=(avsdplayer, ))
                    repeat.start(skill['regen_interval'])


@OnPlayerReset
def on_player_reset(avsdplayer):
    if avsdplayer.current_class == settings.name:
        skill = avsdplayer.skills['ancient power']
        level = skill.level

        if level:
            skill.stats['max_value'] -= level
            skill.stats['regen_interval'] += level

        delay = avsdplayer.data['heavenly touch'].get('delay')

        if delay is not None and delay.running:
            delay.cancel()

        repeat = avsdplayer.data['heavenly touch'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        avsdplayer.data['heavenly touch']['value'] = 0

        repeat = avsdplayer.data['recovery'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        aura = avsdplayer.data['celestial auras'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)


@OnPlayerStatsUpdatePre
def on_player_stats_update_pre(avsdplayer, class_, initialize, data):
    if initialize:
        if class_.name == settings.name:
            skill = class_.skills['ancient power']
            level = skill.level

            if level:
                skill.stats['max_value'] += level
                skill.stats['regen_interval'] -= level


@OnPlayerSwitchClassPost
def on_player_switch_class_post(avsdplayer, old, new):
    if old == settings.name:
        repeat = avsdplayer.data['ancient power'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        delay = avsdplayer.data['heavenly touch'].get('delay')

        if delay is not None and delay.running:
            delay.cancel()

        repeat = avsdplayer.data['heavenly touch'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        repeat = avsdplayer.data['recovery'].get('repeat')

        if repeat is not None and repeat.status == RepeatStatus.RUNNING:
            repeat.stop()

        if not avsdplayer._is_bot:
            menu.close(avsdplayer.index)

        aura = avsdplayer.data['celestial auras'].pop('aura', None)

        if aura is not None:
            aura_manager.remove(aura)
    elif new == settings.name:
        player = avsdplayer.player

        if not player.dead:
            skill = avsdplayer.skills['ancient power']
            level = skill.level

            if level:
                avsdplayer.data['ancient power']['value'] = skill['max_value']

                repeat = avsdplayer.data['ancient power'].get('repeat')

                if repeat is None or repeat.status != RepeatStatus.RUNNING:
                    repeat = avsdplayer.data['ancient power']['repeat'] = Repeat(ancient_power_regen, args=(avsdplayer, ))
                    repeat.start(skill['regen_interval'])


@OnPlayerUpgradeSkill
def on_player_upgrade_skill(avsdplayer, skill, old_level, new_level):
    if avsdplayer.current_class == settings.name:
        if skill.name == 'ancient power':
            skill.stats['max_value'] += new_level - old_level
            skill.stats['regen_interval'] -= new_level - old_level


@OnPlayerUIBuffPre
def on_player_ui_buff_pre(avsdplayer, class_, language, messages, now):
    if avsdplayer.current_class == settings.name:
        value = avsdplayer.data['ancient power'].get('value')

        if value is not None and value:
            messages.append(settings.strings['ui ancient power'].get_string(language, value=value))

        value = avsdplayer.data['heavenly touch'].get('value')

        if value is not None and value:
            messages.append(settings.strings['ui heavenly touch'].get_string(language, value=value))


# ============================================================================
# >> FUNCTIONS
# ============================================================================
def ancient_power_regen(avsdplayer):
    skill = avsdplayer.skills['ancient power']
    value = avsdplayer.data['ancient power']['value']

    if value < skill['max_value']:
        avsdplayer.data['ancient power']['value'] = min(skill['max_value'], value + skill['regen_value'])


def heavenly_touch_start_decrease(avsdplayer):
    heavenly_touch_decrease(avsdplayer)

    repeat = avsdplayer.data['heavenly touch']['repeat'] = Repeat(heavenly_touch_decrease, args=(avsdplayer, ))
    repeat.start(1, avsdplayer.data['heavenly touch']['value'])


def heavenly_touch_decrease(avsdplayer):
    assert avsdplayer.data['heavenly touch']['value']

    avsdplayer.data['heavenly touch']['value'] -= 1


def recovery_step(avsdplayer, heal, leftover):
    player = avsdplayer.player

    if not avsdplayer.data['recovery']['repeat'].loops_remaining:
        heal += leftover

    if player.health + heal < avsdplayer.stats['health']:
        player.health += heal


# ============================================================================
# >> ABILITIES
# ============================================================================
@settings.ability
class CelestialAurasAbility(Ability):
    name = 'celestial auras'

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
class EmpowerAbility(Ability):
    name = 'empower'

    def activate(self, avsdplayer, skill, player, now):
        if avsdplayer.data['ancient power'].get('value', 0) < 5:
            return

        avsdplayer.data['ancient power']['value'] -= 5

        avsdplayer.data[self.name]['cooldown'] = now + 5
        avsdplayer.data[self.name]['active'] = now + 3

        _class_raphael_empower.create(player.origin, parent=player)


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    if avsdvictim.ready:
        if avsdvictim.current_class == settings.name:
            skill = avsdvictim.skills['recovery']
            level = skill.level

            if level:
                now = time()

                if avsdvictim.data['recovery'].get('cooldown', 0) <= now:
                    min_cooldown = skill['min_cooldown']
                    max_cooldown = skill['max_cooldown']

                    cooldown = (level / skill.max) * (min_cooldown - max_cooldown) + max_cooldown

                    avsdvictim.data['recovery']['cooldown'] = now + cooldown

                    repeat = avsdvictim.data['recovery'].get('repeat')

                    if repeat is not None:
                        if repeat.status == RepeatStatus.RUNNING:
                            repeat.stop()

                        assert repeat.status != RepeatStatus.RUNNING

                    damage = info.damage * 0.5

                    heal = damage / 12

                    # For item Girdle of recovery
                    healing = skill.stats.get('healing')

                    if healing is not None:
                        heal *= (healing + 1)

                    leftover = round((heal - int(heal)) * 12)
                    heal = int(heal)

                    repeat = avsdvictim.data['recovery']['repeat'] = Repeat(recovery_step, args=(avsdvictim, heal, leftover))
                    repeat.start(0.25, 12)

                    _class_raphael_recovery.create(avsdattacker.player.origin, parent=avsdattacker.player)


@OnTraceAttack
def on_trace_attack(avsdvictim, avsdattacker, info):
    if avsdattacker is None:
        return

    if avsdattacker.ready:
        if avsdattacker.current_class == settings.name:
            skill = avsdattacker.skills['heavenly touch']
            level = skill.level

            if level:
                cost = skill['cost']

                if avsdattacker.data['ancient power'].get('value', 0) >= cost:
                    now = time()

                    if avsdattacker.data['heavenly touch'].get('cooldown', 0) <= now:
                        victim = avsdvictim.player
                        health = victim.health

                        if health < avsdvictim.stats['health']:
                            avsdattacker.data['ancient power']['value'] -= cost
                            avsdattacker.data['heavenly touch']['cooldown'] = now + skill['cooldown']

                            min_heal_min = skill['min_heal_min']
                            min_heal_max = skill['min_heal_max']
                            max_heal_min = skill['max_heal_min']
                            max_heal_max = skill['max_heal_max']

                            min_heal = (level / skill.max) * (min_heal_max - min_heal_min) + min_heal_min
                            max_heal = (level / skill.max) * (max_heal_max - max_heal_min) + max_heal_min

                            victim.health = min(health + round(randint(round(min_heal), round(max_heal))), avsdvictim.stats['health'])

                            value = avsdattacker.data['heavenly touch'].get('value', 0)

                            if value < 100:
                                avsdattacker.data['heavenly touch']['value'] = min(value + 10, 100)

                            delay = avsdattacker.data['heavenly touch'].get('delay')

                            if delay is not None and delay.running:
                                delay.cancel()

                            repeat = avsdattacker.data['heavenly touch'].get('repeat')

                            if repeat is not None and repeat.status == RepeatStatus.RUNNING:
                                repeat.stop()

                            avsdattacker.data['heavenly touch']['delay'] = Delay(10, heavenly_touch_start_decrease, args=(avsdattacker, ))

                            _class_raphael_heavenly_touch.create(victim.origin, parent=victim)


# ============================================================================
# >> MENUS
# ============================================================================
@menu.register_select_callback
def menu_select(menu, client, option):
    if option.choice_index not in (1, 2, 3, 4, 5, 6):
        if option.choice_index == 7:
            return option.value

        return

    avsdplayer = AVSDPlayer.from_index(client)

    assert avsdplayer.current_class == settings.name

    skill = avsdplayer.skills['celestial auras']

    aura = avsdplayer.data['celestial auras'].get('aura')

    if aura is not None:
        aura_manager.remove(aura)

    if option.value == CelestialAuras.CERBERUS:
        min_cerberus_armor = skill['min_cerberus_armor']
        max_cerberus_armor = skill['max_cerberus_armor']

        value = round((skill.level / skill.max) * (max_cerberus_armor - min_cerberus_armor) + min_cerberus_armor)

        aura = CerberusAura(avsdplayer, 250, team=avsdplayer.player.team_index, value=value)
    elif option.value == CelestialAuras.PHOENIX:
        min_phoenix_health = skill['min_phoenix_health']
        max_phoenix_health = skill['max_phoenix_health']

        value = round((skill.level / skill.max) * (max_phoenix_health - min_phoenix_health) + min_phoenix_health)

        aura = PhoenixAura(avsdplayer, 250, team=avsdplayer.player.team_index, value=value)
    elif option.value == CelestialAuras.UNICORN:
        min_unicorn_speed = skill['min_unicorn_speed']
        max_unicorn_speed = skill['max_unicorn_speed']

        value = (skill.level / skill.max) * (max_unicorn_speed - min_unicorn_speed) + min_unicorn_speed

        aura = UnicornAura(avsdplayer, 250, team=avsdplayer.player.team_index, value=value)
    elif option.value == CelestialAuras.BEHEMOTH:
        min_behemoth_shake = skill['min_behemoth_shake']
        max_behemoth_shake = skill['max_behemoth_shake']

        value = round((skill.level / skill.max) * (max_behemoth_shake - min_behemoth_shake) + min_behemoth_shake)

        aura = BehemothAura(avsdplayer, 250, team=5 - avsdplayer.player.team_index, value=value)
    elif option.value == CelestialAuras.DRAGON:
        min_dragon_damage_min = skill['min_dragon_damage_min']
        min_dragon_damage_max = skill['min_dragon_damage_max']
        max_dragon_damage_min = skill['max_dragon_damage_min']
        max_dragon_damage_max = skill['max_dragon_damage_max']

        value = round((skill.level / skill.max) * (min_dragon_damage_max - min_dragon_damage_min) + min_dragon_damage_min)
        value2 = round((skill.level / skill.max) * (max_dragon_damage_max - max_dragon_damage_min) + max_dragon_damage_min)

        aura = DragonAura(avsdplayer, 250, team=5 - avsdplayer.player.team_index, value=value, value2=value2)
    else:
        min_frost_giant_speed = skill['min_frost_giant_speed']
        max_frost_giant_speed = skill['max_frost_giant_speed']

        value = (skill.level / skill.max) * (max_frost_giant_speed - min_frost_giant_speed) + min_frost_giant_speed

        aura = FrostGiantAura(avsdplayer, 250, team=avsdplayer.player.team_index, value=value)

    aura.data['type'] = option.value

    avsdplayer.data['celestial auras']['aura'] = aura

    aura_manager.append(aura)

    return menu


@menu.register_build_callback
def menu_build(menu, client):
    avsdplayer = AVSDPlayer.from_index(client)

    assert avsdplayer.current_class == settings.name

    if avsdplayer.current_class == settings.name:
        current_level = avsdplayer.skills['celestial auras'].level
        aura = avsdplayer.data['celestial auras'].get('aura')

        for i, level in enumerate([1, 6, 3, 9, 15, 12], 2):
            menu[i].selectable = menu[i].highlight = current_level >= level and (aura is None or aura.data['type'] != menu[i].value)
    else:
        menu.close(client)
