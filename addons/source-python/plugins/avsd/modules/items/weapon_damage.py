# ../avsd/modules/items/weapon_damage.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Random
from random import randint

# Source.Python Imports
#   Filters
from filters.weapons import WeaponClassIter

# AvsD Imports
#   Listeners
from ...core.listeners import OnTakeDamage


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
weapons = [x.basename for x in WeaponClassIter('all', ['melee', 'grenade', 'objective'])]
CHANCE = 0.25


# ============================================================================
# >> HOOKS
# ============================================================================
@OnTakeDamage
def on_take_damage(avsdvictim, avsdattacker, info, now):
    if avsdattacker is None:
        return

    if avsdattacker.ready:
        weapon_damage = avsdattacker.data.get('weapon_damage')

        if weapon_damage is not None:
            if info.weapon in weapons:
                if CHANCE > randint():
                    info.damage += weapon_damage
