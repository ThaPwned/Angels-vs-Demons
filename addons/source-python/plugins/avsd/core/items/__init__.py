# ../avsd/core/items/__init__.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Random
from random import choice
from random import choices

# Source.Python Imports
#   Engines
from engines.precache import Model
from engines.trace import MAX_TRACE_LENGTH
from engines.trace import engine_trace
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
#   Entities
from entities.entity import Entity
from entities.helpers import index_from_inthandle
#   Mathlib
from mathlib import Vector
#   Messages
from messages import SayText2

# AvsD Imports
#   Area
from ..area.zone import SphereZone
from ..area.zone import zone_manager
#   Config
from ..config import items_data
#   Constants
from ..constants import ItemQuality
#   Helpers
from ..helpers.particle import Particle
#   Listeners
from ..listeners import OnPlayerItemPickup
#   Menus
from ..menus import SimpleMenu
from ..menus import item_zone_menu
#   Translations
from ..translations import chat_strings
from ..translations import items_strings
from ..translations import menu_strings


# ============================================================================
# >> CLASSES
# ============================================================================
class _ItemManager(object):
    def __init__(self):
        self._spawned_items = []
        self._categories = {}
        self._items = items_data['items']

        for category in items_data['categories']:
            self._categories[category] = {}

            for name, item in self._items.items():
                if category == item['category']:
                    for class_ in ([item['allow']] if isinstance(item['allow'], str) else item['allow']):
                        if class_ not in self._categories[category]:
                            self._categories[category][class_] = []

                        self._categories[category][class_].append(name)

    def __getitem__(self, item):
        return self._items[item]

    def get_items_by_category(self, category):
        seen = []

        for class_ in self._categories[category]:
            for item in self._categories[category].get(class_, []) + self._categories[category].get('all', []):
                if item not in seen:
                    yield item
                    seen.append(item)

    def get_items_by_class(self, class_):
        seen = []

        for category in self._categories:
            for item in self._categories[category].get(class_, []) + self._categories[category].get('all', []):
                if item not in seen:
                    yield item
                    seen.append(item)

    def get_items_by_class_and_category(self, class_, category):
        seen = []

        for item in self._categories[category].get(class_, []) + self._categories[category].get('all', []):
            if item not in seen:
                yield item
                seen.append(item)

    def get_max_slots(self, slot_level):
        inventory = items_data['inventory']

        return inventory['default'] + inventory['increase'] * slot_level

    def generate(self, level=0, class_=None):
        max_quality = ItemQuality.POOR

        for quality, value in items_data['quality_drop_min_level'].items():
            if level >= int(value):
                new_quality = ItemQuality.from_str(quality)

                if new_quality > max_quality:
                    max_quality = new_quality

        weights = {}

        for quality, chance in items_data['quality_chance'].items():
            quality = ItemQuality.from_str(quality)

            if quality <= max_quality:
                weights[quality] = float(chance)

        # This is done to make sure the order is the same (not sure if it's even necessary)
        order = list(weights.keys())

        quality = choices(order, weights=[weights[x] for x in order])[0]
        quality_name = quality.name.lower()

        items = self._items if class_ is None else self.get_items_by_class(class_)

        # This tries to make sure there's always an item given, even if there's no item with the given quality (it just lowers the quality)
        while True:
            items = [item for item in items if quality_name in self._items[item]['quality']]

            if items:
                break

            # Raises a ValueError after maximum 5 tries
            try:
                quality = ItemQuality(quality.value - 1)
            except ValueError:
                raise ValueError(f'Failed to find item with {class_} from level {level}.')

            quality_name = quality.name

        name = choice(items)

        return Item(name, quality)

    @property
    def categories(self):
        return self._categories.keys()
item_manager = _ItemManager()


class Item(object):
    # particle = Particle('_General_ItemDrop')
    particle = Particle('_General_Level')

    class Zone(SphereZone):
        def __init__(self, item, owner, origin, radius):
            super().__init__(owner, origin, radius)

            self.item = item
            self._ignore = False

        def on_enter_zone(self, player):
            if self.owner.index == player.index:
                # if self.owner.max_slots > len(self.owner.items.valid):
                if self.owner.max_slots > self.owner.items.total:
                    self.owner.items.give(self.item.name, self.item.quality)

                    # gain_item.send(player.index, name=items_strings.get('{0} name'.format(self.item.name), self.item.name), quality=menu_strings[self.item.quality.name.lower()])
                    gain_item.send(player.index, name=items_strings.get(f'{self.item.name} name', self.item.name), quality=menu_strings[self.item.quality.name.lower()])

                    self._ignore = True

                    self.item.remove()

                    OnPlayerItemPickup.manager.notify(self.owner, self.item.name, self.item.quality)
                else:
                    if '_items' not in self.owner.data:
                        self.owner.data['_items'] = []

                    self.owner.data['_items'].append(self.item)

                    if not item_zone_menu.is_active_menu(player.index):
                        item_zone_menu.send(player.index)

        def on_exit_zone(self, player):
            if self.owner.index == player.index:
                if not self._ignore:
                    if '_items' in self.owner.data:
                        if self.item in self.owner.data['_items']:
                            self.owner.data['_items'].remove(self.item)

                            if self.owner.data['_items']:
                                if item_zone_menu.is_active_menu(player.index):
                                    queue = SimpleMenu.get_user_queue(player.index)
                                    queue._refresh()
                            else:
                                del self.owner.data['_items']

                                item_zone_menu.close(player.index)

    def __init__(self, name, quality):
        self.name = name
        self.quality = quality

    def spawn(self, owner, origin, floor=True):
        if floor:
            origin_down = Vector(*origin)
            origin_down.z *= MAX_TRACE_LENGTH
            origin_down.z = -abs(origin_down.z)

            ray = Ray(origin, origin_down)

            trace = GameTrace()

            engine_trace.trace_ray(ray, ContentMasks.ALL, TraceFilterSimple(), trace)

            if not trace.did_hit():
                raise ValueError('Failed to get end position from trace')

            origin = trace.end_position

        entity = Entity.create('prop_dynamic_override')
        entity.model = MODEL
        entity.origin = origin
        entity.spawn()

        self._inthandle = entity.inthandle

        self._zone = self.Zone(self, owner, origin, 50)
        zone_manager.append(self._zone)

        origin = Vector(*origin)
        # origin.z -= 120

        self._particle = self.particle.create(origin)

        item_manager._spawned_items.append(self)

    def remove(self):
        try:
            index = index_from_inthandle(self._inthandle)
        except ValueError:
            pass
        else:
            Entity(index).remove()

        self._particle.remove()

        zone_manager.remove(self._zone)

        item_manager._spawned_items.remove(self)


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
MODEL = Model('models/props/de_dust/hr_dust/dust_crates/dust_crate_style_01_32x16x32.mdl')

gain_item = SayText2(chat_strings['gain item'])
