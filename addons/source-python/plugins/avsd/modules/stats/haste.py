# ../avsd/modules/stats/haste.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
# from collections import defaultdict

# Source.Python Imports
# #   Engines
# from engines.server import global_vars
# #   Entities
# from entities.hooks import EntityCondition
# from entities.hooks import EntityPostHook
# from entities.hooks import EntityPreHook
# #   Memory
# from memory import make_object
# #   Players
# from players.constants import PlayerButtons
# from players.entity import Player

# AvsD Imports
#   Helpers
# from ...core.helpers.players import is_allowed_to_attack
from ...core.helpers.rate import ecx_storage  # Just to load it
#   Listeners
from ...core.listeners import OnPlayerAttackPre
#   Players
# from ...core.players.entity import Player as AVSDPlayer


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
# ecx_storage = {}
# players = defaultdict(dict)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerAttackPre
def on_player_attack_pre(avsdplayer, player, weapon, is_attack1, data):
    haste = avsdplayer.stats.get('haste' if is_attack1 else 'haste2')

    if haste is not None:
        data['rate'] += haste


# ============================================================================
# >> FUNCTIONS
# ============================================================================
# def set_attack_rate(index, key, weapon, haste, attribute):
#     if players[index].get(key, False):
#         players[index][key] = False

#         if haste is not None:
#             haste += 1

#             current_time = global_vars.current_time
#             next_attack = getattr(weapon, attribute) - current_time

#             weapon.set_property_float('m_flPlaybackRate', haste)

#             setattr(weapon, attribute, (next_attack / haste) + current_time)


# ============================================================================
# >> HOOKS
# ============================================================================
# # @EntityPreHook(EntityCondition.is_player, 'pre_think')
# def pre_pre_think(stack):
#     player = make_object(Player, stack[0])

#     if not player.dead:
#         weapon = player.active_weapon

#         if weapon is not None:
#             if player.buttons & PlayerButtons.ATTACK2 and global_vars.current_time >= weapon.next_secondary_fire_attack and is_allowed_to_attack(player):
#                 players[player.index]['haste2'] = True
#             elif player.buttons & PlayerButtons.ATTACK and global_vars.current_time >= weapon.next_attack and is_allowed_to_attack(player):
#                 players[player.index]['haste'] = True


# # @EntityPreHook(EntityCondition.is_player, 'post_think')
# def pre_post_think(stack):
#     ecx_storage[stack.registers.esp.address.address] = make_object(Player, stack[0])


# @EntityPostHook(EntityCondition.is_player, 'post_think')
# def post_post_think(stack, return_value=None):
#     player = ecx_storage.pop(stack.registers.esp.address.address, None)

#     if player is not None:
#         if not player.dead:
#             weapon = player.active_weapon

#             if weapon is not None:
#                 if player.buttons & PlayerButtons.ATTACK2:
#                     avsdplayer = AVSDPlayer.from_index(player.index)

#                     if avsdplayer.ready:
#                         set_attack_rate(player.index, 'haste2', weapon, avsdplayer.stats.get('haste2'), 'next_secondary_fire_attack')
#                 elif player.buttons & PlayerButtons.ATTACK:
#                     avsdplayer = AVSDPlayer.from_index(player.index)

#                     if avsdplayer.ready:
#                         set_attack_rate(player.index, 'haste', weapon, avsdplayer.stats.get('haste'), 'next_attack')
