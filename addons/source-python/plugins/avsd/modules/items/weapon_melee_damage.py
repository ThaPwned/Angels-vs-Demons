# ../avsd/modules/items/weapon_melee_damage.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Source.Python Imports
#   Filters
from filters.weapons import WeaponClassIter
#   Players
from players.constants import PlayerButtons

# AvsD Imports
#   Listeners
from ...core.listeners import OnTakeDamage


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
weapons = [x.basename for x in WeaponClassIter('melee')]


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    if avsdattacker.ready:
        if info.weapon in weapons:
            buttons = avsdattacker.player.buttons

            if buttons & PlayerButtons.ATTACK:
                weapon_melee_damage = avsdattacker.data.get('weapon_melee_left_damage')

                if weapon_melee_damage is not None:
                    info.damage += weapon_melee_damage
            elif buttons & PlayerButtons.ATTACK2:
                weapon_melee_damage = avsdattacker.data.get('weapon_melee_right_damage')

                if weapon_melee_damage is not None:
                    info.damage += weapon_melee_damage
