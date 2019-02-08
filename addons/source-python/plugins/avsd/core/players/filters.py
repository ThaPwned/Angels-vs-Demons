# ../avsd/core/players/iterator.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Filters
from filters.players import PlayerIter as SPPlayerIter

# AvsD Imports
#   Player
from .entity import _players
from .entity import Player


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'PlayerIter',
    'PlayerReadyIter'
)


# =============================================================================
# >> CLASSES
# =============================================================================
class PlayerIter(SPPlayerIter):
    def __iter__(self):
        for item in self.iterator():
            valid, avsdplayer = self._is_valid(item)

            if valid:
                yield item, avsdplayer

    def _is_valid(self, item):
        if super()._is_valid(item):
            return True, Player.from_index(item.index)

        return False, None

    # def iterator(self):
    #     for player in _players.values():
    #         yield player


class PlayerReadyIter(PlayerIter):
    def __init__(self, is_filters=None, not_filters=None, ready=True):
        super().__init__(is_filters, not_filters)

        self.ready = ready

    def _is_valid(self, item):
        valid, avsdplayer = super()._is_valid(item)

        if valid:
            return avsdplayer.ready == self.ready, avsdplayer

        return False, None


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
PlayerIter._filters = SPPlayerIter.filters
PlayerReadyIter._filters = SPPlayerIter.filters
