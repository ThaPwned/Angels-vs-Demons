# ../avsd/modules/stats/cregen.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Listeners
from listeners.tick import Repeat
#   Weapons
from weapons.manager import weapon_manager

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

        cregen = avsdplayer.stats.get('cregen')

        if cregen is None:
            continue

        active_weapon = player.active_weapon

        if active_weapon is None:
            continue

        try:
            clip = active_weapon.clip
        except ValueError:
            continue

        max_clip = weapon_manager[active_weapon.classname].clip

        if clip >= max_clip:
            continue

        if isinstance(cregen, float):
            _cregen = avsdplayer.data.pop('_cregen', 0)
            cregen += _cregen
            leftovers = cregen - int(cregen)
            cregen = int(cregen - leftovers)

            data = {'value':cregen}

            OnPlayerStatReceivePre.manager.notify(avsdplayer, 'cregen', data)

            cregen = data['value']

            if not cregen:
                avsdplayer.data['_cregen'] = _cregen
                continue

            if leftovers:
                avsdplayer.data['_cregen'] = leftovers
        else:
            data = {'value':cregen}

            OnPlayerStatReceivePre.manager.notify(avsdplayer, 'cregen', data)

            cregen = data['value']

            if not cregen:
                continue

            if isinstance(cregen, float):
                _cregen = avsdplayer.data.pop('_cregen', 0)
                cregen += _cregen
                leftovers = cregen - int(cregen)
                cregen = int(cregen - leftovers)

                if leftovers:
                    avsdplayer.data['_cregen'] = leftovers

        active_weapon.clip = min(clip + cregen, max_clip)
regen.start(3)
