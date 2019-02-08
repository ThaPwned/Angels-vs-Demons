# ../avsd/core/helpers/skillshot.py

# interpenetrating entities! (<entity> and <other>)
# Failing to submit row for a grenade detonation: Grenade has no weapon info!

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
#   Core
from core import AutoUnload
#   Engines
from engines.trace import TraceFilterSimple
#   Entities
from entities.constants import WORLD_ENTITY_INDEX
from entities.constants import MoveType
from entities.entity import Entity
from entities.helpers import index_from_inthandle
from entities.helpers import inthandle_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
#   Filters
from filters.players import PlayerIter
#   Hooks
from hooks.exceptions import except_hooks
#   Listeners
from listeners import OnEntityDeleted
#   Mathlib
from mathlib import Vector
#   Memory
from memory import make_object

# AvsD Imports
#   Helpers
from ...core.helpers.math import InFront
# #   Players
# from ...core.players.entity import Player as AVSDPlayer


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
_managers = {}

ENTITY = 'flashbang_projectile'


# =============================================================================
# >> CLASSES
# =============================================================================
class Skillshot(AutoUnload):
    particle = None
    remove_on_world_hit = True

    def __init__(self, player, velocity=1000, **kwargs):
        # if not isinstance(player, AVSDPlayer):
        #     player = AVSDPlayer.from_index(player.index)

        self.owner = player
        self.velocity = velocity
        self.data = kwargs

        player = player.player

        origin = Vector(*InFront(player.eye_location, player.eye_angle))

        trace = player.get_trace_ray(trace_filter=TraceFilterSimple(PlayerIter()))

        vector = trace.end_position - origin
        vector.normalize()
        vector *= velocity

        entity = Entity.create(ENTITY)

        self.inthandle = entity.inthandle
        _managers[self.inthandle] = self

        entity.teleport(origin=origin, velocity=vector)
        entity.spawn()

        entity.set_key_value_int('disableshadows', 1)
        entity.set_key_value_int('disablereceiveshadows', 1)

        entity.set_property_uchar('m_CollisionGroup', 1)
        entity.set_property_ushort('m_Collision.m_usSolidFlags', 8)
        entity.set_property_float('m_flElasticity', 0)
        entity.set_property_int('m_nNextThinkTick', -1)

        entity.color = entity.color.with_alpha(0)
        entity.mins = Vector(-2.5, -2.5, -2.5)
        entity.maxs = Vector(2.5, 2.5, 2.5)

        entity.move_type = MoveType.FLY

        if self.particle is None:
            self._particle = None
        else:
            self._particle = self.particle.create(entity.origin, parent=entity)

    def _unload_instance(self):
        self.remove()

    def remove(self):
        _managers.pop(self.inthandle, None)

        try:
            entity = self.entity
        except ValueError:
            pass
        else:
            entity.remove()

        if self._particle is not None:
            self._particle.remove()

    @property
    def entity(self):
        return Entity(index_from_inthandle(self.inthandle))

    def on_automatically_removed(self):
        pass

    def on_start_touch(self, other):
        pass


# =============================================================================
# >> LISTENERS
# =============================================================================
@OnEntityDeleted
def on_entity_deleted(base_entity):
    if not base_entity.is_networked():
        return

    manager = _managers.pop(base_entity.inthandle, None)

    if manager is not None:
        try:
            manager.on_automatically_removed()
        except:
            except_hooks.print_exception()

        if manager._particle is not None:
            manager._particle.remove()


# =============================================================================
# >> HOOKS
# =============================================================================
@EntityPreHook(EntityCondition.equals_entity_classname(ENTITY), 'start_touch')
def pre_start_touch(stack):
    if _managers:
        inthandle = inthandle_from_pointer(stack[0])
        manager = _managers.get(inthandle)

        if manager is not None:
            other = make_object(Entity, stack[1])

            try:
                return_value = manager.on_start_touch(other)
            except:
                except_hooks.print_exception()

                return_value = True

            if not return_value:
                if manager.remove_on_world_hit:
                    if other.index == WORLD_ENTITY_INDEX:
                        return_value = True

            if return_value:
                del _managers[inthandle]

                manager.entity.remove()
