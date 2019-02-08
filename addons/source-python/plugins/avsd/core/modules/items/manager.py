# ../avsd/core/modules/items/manager.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# AvsD Imports
#   Config
from ...config import items_data
#   Modules
from ..base import _BaseManager


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'items_manager',
)


# =============================================================================
# >> CLASSES
# =============================================================================
class _ItemsManager(_BaseManager):
    module = 'items'

    def load_all(self):
        for item in items_data['items']:
            library = items_data['items'][item].get('library')

            if library is not None:
                if library not in self:
                    self.load(library)
items_manager = _ItemsManager()
