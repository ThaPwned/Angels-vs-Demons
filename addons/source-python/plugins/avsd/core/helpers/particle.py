# ../avsd/core/helpers/particle.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Warnings
from warnings import warn

# Source.Python Imports
#   Core
from core import AutoUnload
#   Engines
from engines.precache import Generic
from engines.server import global_vars
#   Entities
from entities.entity import Entity
from entities.helpers import index_from_inthandle
#   Events
from events import Event
#   Listeners
from listeners import OnEntityDeleted
from listeners import OnLevelInit
from listeners.tick import Delay
#   Mathlib
from mathlib import QAngle
#   Paths
from paths import GAME_PATH
#   Stringtables
from stringtables import string_tables


# ============================================================================
# >> CLASSES
# ============================================================================
class Particle(AutoUnload):
    def __init__(self, name, lifetime=None, offsets=None):
        self.name = name
        self.lifetime = lifetime
        self.offsets = offsets

        if global_vars.map_name:
            self.index = string_tables.ParticleEffectNames.add_string(self.name)
        else:
            self.index = None

        self._entities = {}

        _managers.add(self)

    def _unload_instance(self):
        _managers.discard(self)

        for particle in list(self._entities.values()):
            if particle.delay is not None:
                if particle.delay.running:
                    # warn(f'Particle {self.name} should not be running.')

                    particle.delay()

    def create(self, origin, angles=None, lifetime=0, parent=None, index=-1):
        entity = Entity.create('info_particle_system')

        if self.index is None:
            self.index = string_tables.ParticleEffectNames.add_string(self.name)

        if self.offsets is not None:
            for i, x in enumerate(self.offsets):
                origin[i] += x

        if angles is not None:
            if not isinstance(angles, QAngle):
                angles = QAngle(*angles)

            entity.angles = angles

        entity.origin = origin
        entity.effect_name = self.name
        entity.effect_index = self.index
        entity.start_active = 1
        entity.set_key_value_string('classname', self.name)

        inthandle = entity.basehandle.to_int()

        particle = self._entities[inthandle] = _ParticleEntity(self, inthandle, lifetime if self.lifetime is None else self.lifetime + lifetime)

        if parent is None:
            particle._delayed_initialize = Delay(0, particle._initialize, cancel_on_level_end=True)
        else:
            # Dyncall
            particle._delayed_initialize = Delay(0, particle._initialize, args=(parent.inthandle, index), cancel_on_level_end=True)

        return particle


class _ParticleEntity(object):
    def __init__(self, manager, inthandle, lifetime):
        self._manager = manager
        self.inthandle = inthandle

        if lifetime > 0:
            self.delay = Delay(lifetime, self.remove)
        else:
            self.delay = None

        self._delayed_initialize = None

    def remove(self):
        if self.delay is not None:
            if self.delay.running:
                self.delay.cancel()

        if self._delayed_initialize.running:
            self._delayed_initialize.cancel()

        self._manager._entities.pop(self.inthandle, None)

        # TODO: Check if it's safe to just remove it without a delay
        # Delay(0, self._safe_remove)

    # def _safe_remove(self):
        try:
            entity = self.entity
        except ValueError:
            pass
        else:
            entity.remove()

    def _initialize(self, inthandle=None, index=-1):
        try:
            entity = self.entity
        except ValueError:
            pass
        else:
            if inthandle is not None:
                try:
                    parent = Entity(index_from_inthandle(inthandle))
                except ValueError:
                    self.remove()
                    return
                else:
                    entity.set_parent(parent, index)

            entity.start()

    @property
    def entity(self):
        return Entity(index_from_inthandle(self.inthandle))


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
_managers = set()


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('round_prestart')
def round_prestart(event):
    for manager in _managers:
        if manager._entities:
            for entity in manager._entities.values():
                if entity.delay is not None:
                    if entity.delay.running:
                        entity.delay.cancel()

            manager._entities.clear()


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnEntityDeleted
def on_entity_deleted(base_entity):
    if not base_entity.is_networked():
        return

    inthandle = base_entity.inthandle

    for manager in _managers:
        particle = manager._entities.pop(inthandle, None)

        if particle is not None:
            particle.remove()

            break


@OnLevelInit
def on_level_init(map_name):
    for path in GAME_PATH.joinpath('particles').listdir('*.pcf'):
        if map_name:
            string_tables.ExtraParticleFilesTable.add_string(path.name)

        Generic('particles/' + path.name, True, True)

    if map_name:
        for manager in _managers:
            manager.index = string_tables.ParticleEffectNames.add_string(manager.name)


on_level_init(global_vars.map_name)
