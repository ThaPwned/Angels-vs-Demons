# ../avsd/modules/stats/speed.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Events
from events import Event
#   Filters
from filters.players import PlayerIter

# AvsD Imports
#   Listeners
from ...core.listeners import OnPlayerFlyUpdatePost
from ...core.listeners import OnPlayerReady
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
@OnPlayerFlyUpdatePost
def on_player_fly_update_post(avsdplayer, state):
    stat = 'flyspeed' if state else 'speed'

    speed = avsdplayer.stats.get(stat)

    if speed is None:
        return

    avsdplayer.player.speed = speed


@OnPlayerReady
def on_player_ready(avsdplayer):
    if avsdplayer.current_class is None:
        return

    stat = 'speed'

    if hasattr(avsdplayer, 'flying'):
        if avsdplayer.flying:
            stat = 'flyspeed'

    speed = avsdplayer.stats.get(stat)

    if speed is None:
        return

    player = avsdplayer.player

    if player.dead:
        return

    if player.team_index < 2:
        return

    player.speed = speed


@OnPluginUnload
def on_plugin_unload():
    for player in PlayerIter():
        player.speed = 1
