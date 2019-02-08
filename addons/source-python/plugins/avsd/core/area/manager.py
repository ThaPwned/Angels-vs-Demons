# ../avsd/core/helpers/area/manager.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Time
from time import time
#   Warnings
from warnings import warn

# Source.Python Imports
#   Core
from core import AutoUnload
#   Filters
from filters.players import PlayerIter
#   Hooks
from hooks.exceptions import except_hooks
#   Listeners
from listeners.tick import Repeat
from listeners.tick import RepeatStatus


# =============================================================================
# >> CLASSES
# =============================================================================
class _AreaManager(AutoUnload, list):
    def __init__(self):
        super().__init__()

        self._repeat = Repeat(self._tick)
        self._filter = PlayerIter(is_filters='alive')

    def _unload_instance(self):
        if self._repeat.status == RepeatStatus.RUNNING:
            self._repeat.stop()

    def _tick(self):
        now = time()
        players = {x.index:[x.origin, x] for x in self._filter}

        for index, (_, player) in players.copy().items():
            if player.dead:
                warn(f'Player "{player.name}" should NOT be here. Plz fix {time()}')

                del players[index]

        for callback in self:
            try:
                callback(now, players)
            except:
                except_hooks.print_exception()

    def append(self, item):
        if not self:
            self._repeat.start(0.1)

        super().append(item)

    def remove(self, item):
        super().remove(item)

        if not self:
            self._repeat.stop()
area_manager = _AreaManager()
