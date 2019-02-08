# ../avsd/modules/stats/hregen.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Listeners
from listeners.tick import Repeat

# AvsD Imports
#   Listeners
from ...core.listeners import OnPlayerStatReceivePre
#   Players
from ...core.players.filters import PlayerReadyIter


# ============================================================================
# >> FUNCTIONS
# ============================================================================
@Repeat
def regen():
    for player, avsdplayer in PlayerReadyIter('alive', ['un', 'spec']):
        if avsdplayer.current_class is None:
            continue

        health = avsdplayer.stats.get('health')

        if health is None:
            continue

        hregen = avsdplayer.stats.get('hregen')

        if hregen is None:
            continue

        curhealth = player.health

        if curhealth >= health:
            continue

        if isinstance(hregen, float):
            _hregen = avsdplayer.data.pop('_hregen', 0)
            hregen += _hregen
            leftovers = hregen - int(hregen)
            hregen = int(hregen - leftovers)

            data = {'value':hregen}

            OnPlayerStatReceivePre.manager.notify(avsdplayer, 'hregen', data)

            hregen = data['value']

            if not hregen:
                avsdplayer.data['_hregen'] = _hregen
                continue

            if leftovers:
                avsdplayer.data['_hregen'] = leftovers
        else:
            data = {'value':hregen}

            OnPlayerStatReceivePre.manager.notify(avsdplayer, 'hregen', data)

            hregen = data['value']

            if not hregen:
                continue

            if isinstance(hregen, float):
                _hregen = avsdplayer.data.pop('_hregen', 0)
                hregen += _hregen
                leftovers = hregen - int(hregen)
                hregen = int(hregen - leftovers)

                if leftovers:
                    avsdplayer.data['_hregen'] = leftovers

        player.health = min(curhealth + hregen, health)
regen.start(1)
