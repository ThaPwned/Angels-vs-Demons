# ../avsd/modules/stats/aregen.py

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

        armor = avsdplayer.stats.get('armor')

        if armor is None:
            continue

        aregen = avsdplayer.stats.get('aregen')

        if aregen is None:
            continue

        curarmor = player.armor

        if curarmor >= armor:
            continue

        if isinstance(aregen, float):
            _aregen = avsdplayer.data.pop('_aregen', 0)
            aregen += _aregen
            leftovers = aregen - int(aregen)
            aregen = int(aregen - leftovers)

            data = {'value':aregen}

            OnPlayerStatReceivePre.manager.notify(avsdplayer, 'aregen', data)

            aregen = data['value']

            if not aregen:
                avsdplayer.data['_aregen'] = _aregen
                continue

            if leftovers:
                avsdplayer.data['_aregen'] = leftovers
        else:
            data = {'value':aregen}

            OnPlayerStatReceivePre.manager.notify(avsdplayer, 'aregen', data)

            aregen = data['value']

            if not aregen:
                continue

            if isinstance(aregen, float):
                _aregen = avsdplayer.data.pop('_aregen', 0)
                aregen += _aregen
                leftovers = aregen - int(aregen)
                aregen = int(aregen - leftovers)

                if leftovers:
                    avsdplayer.data['_aregen'] = leftovers

        player.armor = min(curarmor + aregen, armor)
regen.start(1)
