# ../avsd/core/helpers/area/zone.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Core
from core import AutoUnload
#   Hooks
from hooks.exceptions import except_hooks
#   Players
from players.entity import Player

# AvsD Imports
#   Area
from .manager import area_manager
#   Listeners
from ..listeners import OnPlayerDelete


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
_managers = []


# =============================================================================
# >> CLASSES
# =============================================================================
class ZoneManager(AutoUnload, list):
    def __init__(self, start_on_any=True, stop_on_empty=True):
        super().__init__()

        self.start_on_any = start_on_any
        self.stop_on_empty = stop_on_empty

        _managers.append(self)

    def _unload_instance(self):
        if self:
            area_manager.remove(self._tick)

        _managers.remove(self)

    def _tick(self, now, players):
        for zone in self:
            entities = zone.entities
            team = zone.team

            for target, (position, player) in players.items():
                if team is None or player.team == team:
                    if zone.has_within(position):
                        if target in entities:
                            if entities[target] <= now:
                                entities[target] = now + zone.update_interval

                                try:
                                    zone.on_update_zone(player)
                                except:
                                    except_hooks.print_exception()
                        else:
                            entities[target] = now + zone.update_interval

                            try:
                                zone.on_enter_zone(player)
                            except:
                                except_hooks.print_exception()
                    else:
                        if target in entities:
                            del entities[target]

                            try:
                                zone.on_exit_zone(player)
                            except:
                                except_hooks.print_exception()

    def append(self, zone):
        if self.start_on_any:
            if not self:
                area_manager.append(self._tick)

        super().append(zone)

        if zone.zone_particle is not None:
            zone.particles[None] = zone.zone_particle.create(zone.particle_location)

    def remove(self, zone):
        super().remove(zone)

        for particle in zone.particles.values():
            particle.remove()

        zone.particles.clear()

        # for index in zone.entities:
        #     try:
        #         zone.on_exit_zone(Player(index))
        #     except:
        #         except_hooks.print_exception()

        try:
            zone.on_remove_zone()
        except:
            except_hooks.print_exception()

        zone.entities.clear()

        if self.stop_on_empty:
            if not self:
                area_manager.remove(self._tick)
zone_manager = ZoneManager()


class BaseZone(object):
    zone_particle = None
    target_particle = None
    update_interval = 1

    def __init__(self, owner, team=None, **kwargs):
        self.owner = owner
        self.team = team
        self.data = kwargs
        self.entities = {}
        self.particles = {}

    def has_within(self, origin):
        raise NotImplementedError()

    def set_particle(self, player, state):
        assert self.target_particle is not None

        index = player.index

        if state:
            assert index not in self.particles

            particle = self.particles.pop(index, None)

            if particle is not None:
                particle.remove()

            self.particles[index] = self.target_particle.create(player.origin, parent=player)
        else:
            particle = self.particles.pop(index, None)

            if particle is not None:
                particle.remove()

    def on_enter_zone(self, player):
        pass

    def on_update_zone(self, player):
        pass

    def on_exit_zone(self, player):
        pass

    def on_remove_zone(self):
        pass

    def on_client_disconnect(self, player):
        pass

    @property
    def particle_location(self):
        raise NotImplementedError()


class SphereZone(BaseZone):
    def __init__(self, owner, origin, radius, team=None, **kwargs):
        super().__init__(owner, team, **kwargs)

        self.origin = origin
        self.radius = radius

    def has_within(self, origin):
        return self.origin.get_distance_sqr(origin) <= self.radius ** 2

    @property
    def particle_location(self):
        return self.origin


class SquareZone(BaseZone):
    def __init__(self, owner, vector1, vector2, team=None, **kwargs):
        super().__init__(owner, team, **kwargs)

        self.vector1 = vector1
        self.vector2 = vector2

    def has_within(self, origin):
        return origin.is_within_box(self.vector1, self.vector2)

    @property
    def particle_location(self):
        position = self.vector1 + self.vector2
        position.z -= abs(self.vector1.z) - abs(self.vector2.z)
        position /= 2

        return position


# =============================================================================
# >> LISTENERS
# =============================================================================
@OnPlayerDelete
def on_player_delete(avsdplayer):
    index = avsdplayer.index

    for zone in zone_manager:
        if index in zone.entities:
            try:
                zone.on_client_disconnect(Player(index))
            except:
                except_hooks.print_exception()

            del zone.entities[index]
