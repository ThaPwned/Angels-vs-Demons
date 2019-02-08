# ../avsd/modules/stats/health.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Events
from events import Event

# AvsD Imports
#   Listeners
from ...core.listeners import OnPlayerReady
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

    health = avsdplayer.stats.get('health')

    if health is None:
        return

    player = avsdplayer.player

    if player.dead:
        return

    if player.team_index < 2:
        return

    player.health = health
