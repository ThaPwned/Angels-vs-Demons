# ../avsd/core/emulate/__init__.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Random
from random import random

# Source.Python Imports
#   CVars
# from cvars import cvar
#   Listeners
from listeners import OnConVarChanged
from listeners.tick import Repeat
from listeners.tick import RepeatStatus

# AvsD Imports
#   Constants
from ..constants import EMULATE_ABILITY_CHANCE
#   Players
from ..players.filters import PlayerReadyIter


# ============================================================================
# >> CLASSES
# ============================================================================
class _Emulate(object):
    def __init__(self):
        self._repeat = Repeat(self.tick)
        self._filter = PlayerReadyIter(['bot', 'alive'], ['un', 'spec'])

    def tick(self):
        # if bot_stop_cvar is not None:
        #     if bot_stop_cvar.get_int():
        #         return

        for player, avsdplayer in self._filter:
            active_class = avsdplayer.active_class

            if active_class is not None:
                for name in active_class.abilities:
                    if random() <= EMULATE_ABILITY_CHANCE:
                        active_class.skills[name]()

    def start(self):
        if self._repeat.status != RepeatStatus.RUNNING:
            self._repeat.start(1)

    def stop(self):
        if self._repeat.status == RepeatStatus.RUNNING:
            self._repeat.stop()


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
emulate_manager = _Emulate()
# emulate_manager.start()

# bot_stop_cvar = cvar.find_var('bot_stop')


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnConVarChanged
def on_convar_changed(convar, old_value):
    if convar.name == 'bot_stop':
        if convar.get_int():
            emulate_manager.stop()
        else:
            emulate_manager.start()
