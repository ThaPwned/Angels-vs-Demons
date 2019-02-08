# ../avsd/core/helpers/rate.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Engines
from engines.server import global_vars
#   Entities
from entities.helpers import index_from_inthandle
from entities.hooks import EntityCondition
from entities.hooks import EntityPostHook
from entities.hooks import EntityPreHook
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
#   Memory
from memory import make_object
#   Players
from players.constants import PlayerButtons
from players.entity import Player
#   Weapons
from weapons.entity import Weapon

# AvsD Imports
#   Listeners
from ..listeners import OnPlayerAttack
from ..listeners import OnPlayerAttackPost
from ..listeners import OnPlayerAttackPre
#   Players
from ..players.entity import Player as AVSDPlayer


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
ecx_storage = {}
_blocked = set()
_allowed = True


# ============================================================================
# >> HOOKS
# ============================================================================
@EntityPreHook(EntityCondition.is_player, 'post_think')
def pre_post_think(stack):
    if _allowed:
        player = make_object(Player, stack[0])
        buttons = player.buttons

        if buttons & PlayerButtons.ATTACK or buttons & PlayerButtons.ATTACK2:
            if player.index in _blocked:
                return

            weapon = player.active_weapon

            if weapon is not None:
                current_time = global_vars.current_time

                if current_time >= player.get_property_float('m_flNextAttack'):
                    if buttons & PlayerButtons.ATTACK2 and current_time >= weapon.get_property_float('m_flNextSecondaryAttack'):
                        ecx_storage[stack.registers.esp.address.address] = (player, False, current_time, weapon.inthandle)
                    elif buttons & PlayerButtons.ATTACK and current_time >= weapon.get_property_float('m_flNextPrimaryAttack'):
                        ecx_storage[stack.registers.esp.address.address] = (player, True, current_time, weapon.inthandle)
        else:
            _blocked.discard(player.index)


@EntityPostHook(EntityCondition.is_player, 'post_think')
def post_post_think(stack, return_value):
    address = stack.registers.esp.address.address
    data = ecx_storage.pop(address, None)

    if data is not None:
        player, is_attack1, current_time, inthandle = data

        avsdplayer = AVSDPlayer.from_index(player.index)

        if avsdplayer.current_class:
            weapon = Weapon(index_from_inthandle(inthandle))

            data = {'rate':1}

            OnPlayerAttackPre.manager.notify(avsdplayer, player, weapon, is_attack1, data)

            rate = data['rate']

            OnPlayerAttack.manager.notify(avsdplayer, player, weapon, is_attack1)

            if rate != 1:
                name = 'm_flNextPrimaryAttack' if is_attack1 else 'm_flNextSecondaryAttack'

                next_attack = weapon.get_property_float(name) - current_time

                weapon.set_property_float('m_flPlaybackRate', rate)

                weapon.set_property_float(name, (next_attack / rate) + current_time)

            OnPlayerAttackPost.manager.notify(avsdplayer, player, weapon, is_attack1)


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('round_prestart')
def on_round_prestart(event):
    global _allowed
    _allowed = False

    _blocked.clear()

    for player in PlayerIter('alive'):
        _blocked.add(player.index)


@Event('round_freeze_end')
def on_round_freeze_end(event):
    global _allowed
    _allowed = True
