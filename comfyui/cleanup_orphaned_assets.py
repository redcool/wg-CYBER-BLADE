# cleanup_orphaned_assets.py
# Compare source definitions vs disk files, delete orphaned PNGs
import os, re, sys

PROJECT = r"H:/ai_works/buffPrj1"

# ============================================================
# 1. Valid IDs from source definitions
# ============================================================

# From shop.js allWeapons (45 weapons)
VALID_WEAPONS = {
    # melee (10)
    'plasma', 'axe', 'dagger', 'chainsaw', 'sword', 'katana', 'hammer',
    'spear', 'claws', 'whip',
    # gun (10)
    'pistol', 'smg', 'shotgun', 'sniper', 'gatling', 'revolver', 'rifle',
    'shotgun_double', 'magnum', 'minigun',
    # bow (10)
    'bow', 'crossbow', 'longbow', 'recurve', 'explosive_arrow', 'frost_arrow',
    'poison_arrow', 'triple_shot', 'piercing_shot', 'homing_bow',
    # magic (10)
    'fire_staff', 'frost_staff', 'thunder_staff', 'energy_staff', 'magic_orb',
    'poison_staff', 'void_staff', 'lightning_staff', 'fire_wand', 'arcane_orb',
    # spray (3, magic tag)
    'flame_spray', 'poison_spray', 'cold_spray',
    # medic (5)
    'heal_gun', 'shield', 'holy_staff', 'life_wand', 'blessing',
}

# Short aliases from earlier z-image-turbo regeneration
SHORT_ALIAS_WEAPONS = {
    'frost', 'homing', 'laser', 'rocket', 'shock',
    'grenade', 'plasma_cannon', 'shuriken', 'swarm',
}

# From shop.js allItems (26 items)
VALID_ITEMS = {
    'hpUp', 'regen', 'armorUp', 'dodgeUp', 'critUp', 'critDmg',
    'speedUp', 'lifesteal', 'rangeUp', 'harvestUp', 'pickupUp', 'luckUp',
    'thorn', 'energy_shield', 'stim', 'ammo_pack', 'replicator',
    'magnet', 'piggy', 'blood_pact', 'scope', 'compression',
    'armor_piercing_ammo', 'burn_spreader', 'ice_core', 'element_amp',
}

# From enemy.js types
VALID_ENEMIES = {'basic', 'fast', 'tank', 'ranged', 'elite', 'boss'}

# From character.js allCharacters
VALID_CHARACTERS = {
    'swordsman', 'gunslinger', 'fire_mage', 'archer',
    'mech', 'assassin', 'medic', 'paladin', 'engineer', 'berserker',
}

# ============================================================
# 2. Scan disk and compare
# ============================================================

def extract_id(filename, prefix):
    """Extract the ID from cb_{prefix}_{id}_00001_.png"""
    name = filename.replace('.png', '')
    if name.startswith(f'cb_{prefix}_'):
        rest = name[len(f'cb_{prefix}_'):]
        # Pattern: {id}_00001_  (note trailing underscore before .png)
        # Find the last _NNNNN_ suffix
        import re as _re
        m = _re.match(r'^(.+)_\d{5,}_$', rest)
        if m:
            return m.group(1)
        return rest
    return None

def scan_directory(dir_path, prefix, valid_ids, extra_aliases=None):
    full_path = os.path.join(PROJECT, dir_path)
    if not os.path.exists(full_path):
        print(f"  Directory not found: {dir_path}")
        return [], []
    
    orphans = []
    valid = []
    unknown_format = []
    
    for f in sorted(os.listdir(full_path)):
        if not f.endswith('.png'):
            continue
        file_id = extract_id(f, prefix)
        if file_id is None:
            # Try alternative prefix (cp_ variants exist for some weapons)
            alt_prefix = 'weapon' if prefix == 'weapon' else prefix
            if prefix == 'weapon':
                file_id = extract_id(f.replace('cb_', ''), prefix)
            if file_id is None:
                unknown_format.append(f)
                continue
        
        # Check if valid
        is_valid = file_id in valid_ids
        if not is_valid and extra_aliases:
            is_valid = file_id in extra_aliases
        
        if is_valid:
            valid.append(f)
        else:
            orphans.append(f)
    
    return orphans, valid, unknown_format


# ============================================================
# 3. Run
# ============================================================

DRY_RUN = '--delete' not in sys.argv

print("=" * 60)
print("  ASSET CLEANUP - Orphaned PNG Detector")
if DRY_RUN:
    print("  MODE: DRY RUN (use --delete to actually delete)")
print("=" * 60)

all_orphans = {}
all_valid = {}
all_unknown = {}

# Weapons
print("\n[WEAPONS] assets/weapons/")
orphans, valid, unknown = scan_directory('assets/weapons', 'weapon', VALID_WEAPONS, SHORT_ALIAS_WEAPONS)
all_orphans['weapons'] = orphans
all_valid['weapons'] = valid
all_unknown['weapons'] = unknown
print(f"  Valid: {len(valid)}  Orphaned: {len(orphans)}  Unknown: {len(unknown)}")

for f in orphans:
    fp = os.path.join(PROJECT, 'assets/weapons', f)
    size = os.path.getsize(fp)
    print(f"    ORPHAN: {f} ({size:,} bytes)")

# Items
print("\n[ITEMS] assets/items/")
orphans, valid, unknown = scan_directory('assets/items', 'item', VALID_ITEMS)
all_orphans['items'] = orphans
all_valid['items'] = valid
all_unknown['items'] = unknown
print(f"  Valid: {len(valid)}  Orphaned: {len(orphans)}  Unknown: {len(unknown)}")

for f in orphans:
    fp = os.path.join(PROJECT, 'assets/items', f)
    size = os.path.getsize(fp)
    print(f"    ORPHAN: {f} ({size:,} bytes)")

# Enemies
print("\n[ENEMIES] assets/enemies/")
orphans, valid, unknown = scan_directory('assets/enemies', 'enemy', VALID_ENEMIES)
all_orphans['enemies'] = orphans
all_valid['enemies'] = valid
all_unknown['enemies'] = unknown
print(f"  Valid: {len(valid)}  Orphaned: {len(orphans)}  Unknown: {len(unknown)}")

for f in orphans:
    fp = os.path.join(PROJECT, 'assets/enemies', f)
    size = os.path.getsize(fp)
    print(f"    ORPHAN: {f} ({size:,} bytes)")

# Characters
print("\n[CHARS] assets/chars/")
orphans, valid, unknown = scan_directory('assets/chars', 'char', VALID_CHARACTERS)
all_orphans['chars'] = orphans
all_valid['chars'] = valid
all_unknown['chars'] = unknown
print(f"  Valid: {len(valid)}  Orphaned: {len(orphans)}  Unknown: {len(unknown)}")

for f in orphans:
    fp = os.path.join(PROJECT, 'assets/chars', f)
    size = os.path.getsize(fp)
    print(f"    ORPHAN: {f} ({size:,} bytes)")

# ============================================================
# Summary
# ============================================================
total_orphans = sum(len(v) for v in all_orphans.values())
total_valid = sum(len(v) for v in all_valid.values())
total_unknown = sum(len(v) for v in all_unknown.values())
total_files = total_orphans + total_valid + total_unknown

print("\n" + "=" * 60)
print(f"  SUMMARY: {total_files} total PNG files")
print(f"  VALID (in use):   {total_valid}")
print(f"  ORPHANED (unused): {total_orphans}")
if total_unknown:
    print(f"  UNKNOWN FORMAT:   {total_unknown}")
print("=" * 60)

if total_orphans == 0:
    print("\n  No orphaned files found. Everything clean!")
    sys.exit(0)

if not DRY_RUN:
    # Actually delete
    total_deleted = 0
    total_size = 0
    print("\n  DELETING orphaned files...")
    
    for category, orphans in all_orphans.items():
        if not orphans:
            continue
        print(f"\n  [{category}]")
        for f in orphans:
            dir_map = {
                'weapons': 'assets/weapons',
                'items': 'assets/items',
                'enemies': 'assets/enemies',
                'chars': 'assets/chars',
            }
            fp = os.path.join(PROJECT, dir_map[category], f)
            if os.path.exists(fp):
                size = os.path.getsize(fp)
                os.remove(fp)
                print(f"    DELETED: {f} ({size:,} bytes)")
                total_deleted += 1
                total_size += size
    
    print(f"\n  Done: {total_deleted} files deleted ({total_size:,} bytes freed)")
else:
    print(f"\n  To delete, run: python comfyui/cleanup_orphaned_assets.py --delete")
