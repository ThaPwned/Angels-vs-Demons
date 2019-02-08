# ../avsd/core/listeners/__init__.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Listeners
from listeners import ListenerManager
from listeners import ListenerManagerDecorator


# ============================================================================
# >> CLASSES
# ============================================================================
class OnPlayerAbilityPre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerAttack(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerAttackPost(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerAttackPre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerAscend(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerAscendPost(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerDelete(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerDestroy(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerFlyUpdate(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerFlyUpdatePost(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerFlyUpdatePre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerItemPickup(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerMailReceived(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerReady(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerReset(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerStartTouch(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerStatReceivePre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerStatsUpdatePre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerSwitchClass(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerSwitchClassPost(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerUpgradeSkill(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerUIBuffPre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerUICooldownPre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerUIDebuffPre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPlayerUIInfoPre(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPluginUnload(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPluginClassLoad(ListenerManagerDecorator):
    manager = ListenerManager()


class OnPluginClassUnload(ListenerManagerDecorator):
    manager = ListenerManager()


class OnTakeDamage(ListenerManagerDecorator):
    manager = ListenerManager()


class OnTraceAttack(ListenerManagerDecorator):
    manager = ListenerManager()


class OnQuestComplete(ListenerManagerDecorator):
    manager = ListenerManager()


class OnQuestReset(ListenerManagerDecorator):
    manager = ListenerManager()


class OnRequirementComplete(ListenerManagerDecorator):
    manager = ListenerManager()
