# ../avsd/modules/stats/gravity.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Entities
from entities.entity import Entity
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter
#   Memory
from memory import make_object
#   Players
from players.constants import PlayerStates

# AvsD Imports
#   Listeners
from ...core.listeners import OnPlayerReady
from ...core.listeners import OnPlayerStartTouch
from ...core.listeners import OnPluginUnload
#   Players
from ...core.players.entity import Player


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('player_spawn')
def player_spawn(event):
    userid = event['userid']

    if not userid:
        return

    avsdplayer = Player.from_userid(userid)

    if not avsdplayer.ready:
        return

    on_player_ready(avsdplayer)


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnPlayerReady
def on_player_ready(avsdplayer):
    if avsdplayer.current_class is None:
        return

    gravity = avsdplayer.stats.get('gravity')

    if gravity is None:
        return

    player = avsdplayer.player

    if player.dead:
        return

    if player.team_index < 2:
        return

    player.gravity = gravity


@OnPluginUnload
def on_plugin_unload():
    for player in PlayerIter():
        player.gravity = 1


# ============================================================================
# >> HOOKS
# ============================================================================
@OnPlayerStartTouch
def on_player_start_touch(avsdplayer, other, grounded):
    if grounded:
        player = avsdplayer.player

        if not player.gravity:
            gravity = avsdplayer.stats.get('gravity')

            if gravity is not None:
                player.gravity = gravity


# @EntityPreHook(EntityCondition.is_player, 'start_touch')
# def start_touch(stack):
#     entity = make_object(Entity, stack[0])

#     if entity.is_player():
#         if entity.flags & PlayerStates.ONGROUND:
#             if not entity.gravity:
#                 avsdplayer = Player.from_index(entity.index)

#                 if avsdplayer.ready:
#                     gravity = avsdplayer.stats.get('gravity')

#                     if gravity is not None:
#                         entity.gravity = gravity
