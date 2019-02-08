# ../avsd/core/helpers/area/aura.py

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
class AuraManager(AutoUnload, list):
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
        for aura in self:
            index = aura.owner.index

            try:
                origin = players[index][0]
            except KeyError:
                from warnings import warn

                warn(f'Please remove {aura} from the manager.')

                raise

            entities = aura.entities
            team = aura.team

            for target, (position, player) in players.items():
                if index != target:
                    if team is None or player.team == team:
                        if origin.get_distance_sqr(position) <= aura.radius ** 2:
                            if target in entities:
                                if entities[target] <= now:
                                    entities[target] = now + aura.update_interval

                                    try:
                                        aura.on_update_aura(player)
                                    except:
                                        except_hooks.print_exception()
                            else:
                                entities[target] = now + aura.update_interval

                                try:
                                    aura.on_enter_aura(player)
                                except:
                                    except_hooks.print_exception()
                        else:
                            if target in entities:
                                del entities[target]

                                try:
                                    aura.on_exit_aura(player)
                                except:
                                    except_hooks.print_exception()

    def append(self, aura):
        assert not aura.owner.player.dead

        if self.start_on_any:
            if not self:
                area_manager.append(self._tick)

        super().append(aura)

        if aura.owner_particle is not None:
            player = aura.owner.player

            aura.particles[None] = aura.owner_particle.create(player.origin, parent=player)

    def remove(self, aura):
        super().remove(aura)

        for particle in aura.particles.values():
            particle.remove()

        aura.particles.clear()

        # for index in aura.entities:
        #     try:
        #         aura.on_exit_aura(Player(index))
        #     except:
        #         except_hooks.print_exception()

        try:
            aura.on_remove_aura()
        except:
            except_hooks.print_exception()

        aura.entities.clear()

        if self.stop_on_empty:
            if not self:
                area_manager.remove(self._tick)
aura_manager = AuraManager()


class Aura(object):
    owner_particle = None
    target_particle = None
    update_interval = 1

    def __init__(self, owner, radius, team=None, **kwargs):
        self.owner = owner
        self.radius = radius
        self.team = team
        self.data = kwargs
        self.entities = {}
        self.particles = {}

    def set_particle(self, player, state):
        assert self.target_particle is not None

        index = player.index

        if state:
            particle = self.particles.pop(index, None)

            if particle is not None:
                particle.remove()

            self.particles[index] = self.target_particle.create(player.origin, parent=player)
        else:
            particle = self.particles.pop(index, None)

            if particle is not None:
                particle.remove()

    def on_enter_aura(self, player):
        pass

    def on_update_aura(self, player):
        pass

    def on_exit_aura(self, player):
        pass

    def on_remove_aura(self):
        pass

    def on_client_disconnect(self, player):
        pass


# =============================================================================
# >> LISTENERS
# =============================================================================
@OnPlayerDelete
def on_player_delete(avsdplayer):
    index = avsdplayer.index

    for aura in aura_manager:
        if index in aura.entities and index != aura.owner.index:
            try:
                aura.on_client_disconnect(Player(index))
            except:
                except_hooks.print_exception()

            del aura.entities[index]
