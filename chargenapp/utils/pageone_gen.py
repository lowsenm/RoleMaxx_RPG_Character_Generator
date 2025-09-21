from .openai_gen import openaigen
import random, json, os
from django.conf import settings


top_cantrip_pool = {
    "Warlock": ["Eldritch Blast (Evocation)"],
    "Wizard": ["Fire Bolt (Evocation)", "Ray Of Frost (Evocation)", "Toll The Dead (Necromancy)", "Chill Touch (Necromancy)"],
    "Sorcerer": ["Fire Bolt (Evocation)", "Ray Of Frost (Evocation)"],
    "Cleric": ["Sacred Flame (Evocation)", "Toll The Dead (Necromancy)"],
    "Druid": ["Produce Flame (Conjuration)", "Thorn Whip (Transmutation)"]
}

def average_damage(damage_str):
    try:
        parts = damage_str.lower().split("d")
        count = int(parts[0])
        size = int(parts[1].split()[0])
        return (count * (1 + size)) / 2  # average of dice roll
    except:
        return 0

# convert index nums to equipment names
file_path = os.path.join(settings.BASE_DIR, "chargenapp", "data", "equipment_indexed_extended.json")
def convert_indices_to_equipment_names(indices):
    with open(file_path, "r", encoding="utf-8") as ef:
        full_items = json.load(ef)
    index_to_name = {item["Index"]: item["Name"] for item in full_items}
    return ", ".join(index_to_name.get(idx, f"Item {idx}") for idx in sorted(indices))


def assign_starting_coins(level):
    import random

    # Total value in gold equivalent
    base_gold = random.randint(100, 150)
    if level > 1:
        base_gold += sum(random.randint(50, 100) for _ in range(level - 1))

    # Convert to copper for easier scaling (1 GP = 100 CP)
    total_cp = int(base_gold * 100)

    # Distribute using weighted shares (e.g., ~50% CP, 25% SP, etc.)
    #cp_share = random.randint(35, 50)   # %
    #sp_share = random.randint(20, 30)
    ep_share = random.randint(10, 15)
    gp_share = random.randint(10, 20)
    pp_share = 100 - (ep_share + gp_share) #(cp_share + sp_share + ep_share + gp_share)

    if pp_share < 0:
        # Reallocate excess to CP if other categories are too greedy
        cp_share += abs(pp_share)
        pp_share = 0

    # Convert share percentages to values in CP
    #cp_value = total_cp * cp_share // 100
    #sp_value = total_cp * sp_share // 100
    ep_value = total_cp * ep_share // 100
    gp_value = total_cp * gp_share // 100
    pp_value = total_cp * pp_share // 100

    coins = {
        #"CP": cp_value,
        #"SP": sp_value // 10,
        "EP": ep_value // 50,
        "GP": gp_value // 100,
        "PP": pp_value // 1000
    }

    return {k: int(v) for k, v in coins.items()}


# Load equipment data
file_path = os.path.join(settings.BASE_DIR, "chargenapp", "data", "combined_equipment_indices.json")
with open(file_path, "r", encoding="utf-8") as f:
    combined_equipment = json.load(f)

file_path = os.path.join(settings.BASE_DIR, "chargenapp", "data", "weapons.json")
with open(file_path, "r", encoding="utf-8") as f:
    weapons = json.load(f)  # dict of dicts: {index: {weapon data}}

    # Convert string keys to int (optional but recommended for numeric lookup)
    weapons = {int(k): v for k, v in weapons.items()}

    weapon_damage_map = {
        idx: f'{w["damage"]["damage_dice"]} {w["damage"]["damage_type"]["name"].lower()}'
        for idx, w in weapons.items()
        if "damage" in w and "damage_dice" in w["damage"] and "damage_type" in w["damage"]
    }

    weapon_type_map = {
        idx: w.get("DamageType", "")
        for idx, w in weapons.items()
    }

    weapon_bonus_map = {
        idx: w.get("AttackBonus", "")
        for idx, w in weapons.items()
    }

    weapon_indices = set(weapons.keys())



def select_equipment(race, char_class, background, level):
    # Load equipment data
    file_path = os.path.join(settings.BASE_DIR, "chargenapp", "data", "equipment_indexed_extended.json")
    with open(file_path, "r", encoding="utf-8") as ef:
        equipment_data = json.load(ef)

    # Build category-based index pools
    categories = {
        "weapon": [],
        "tool": [],
        "armor": [],
        "gear": [],
        "apparel": [],
        "mount": []
    }

    for idx, data in equipment_data.items():
        item_type = data.get("ItemType", "").lower()
        if item_type in categories:
            categories[item_type].append(int(idx))

    # Number of items per category
    num_items = {
        "weapon": 3,
        "tool": 4,
        "armor": 1,
        "gear": 4,
        "apparel": 1,
        "mount": 1 if level >= 10 else 0
    }

    # Random selection
    selected = []
    for cat, count in num_items.items():
        if categories[cat] and count > 0:
            selected.extend(random.sample(categories[cat], min(count, len(categories[cat]))))

    return sorted(selected)


def add_features_traits_and_gear(character_data):
    race = character_data.get("Race", "").lower()
    char_class = character_data.get("Class", "").lower()
    background = character_data.get("Background", "").lower()
    level = int(character_data.get("Level", 1))

    race_features = {
        "half-elf": ["Darkvision", "Fey Ancestry", "Skill Versatility"],
        "elf": ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance"],
        "human": ["Extra Language", "Versatile"],
        "dwarf": ["Darkvision", "Dwarven Resilience", "Stonecunning"],
    }

    class_features = {
        "barbarian": [
            "Rage",
            "Unarmored Defense",
            "Danger Sense" if level >= 2 else None,
            "Reckless Attack" if level >= 2 else None,
        ],
        "cleric": [
            "Spellcasting",
            "Divine Domain",
            "Channel Divinity" if level >= 2 else None
        ],
        "rogue": [
            "Sneak Attack",
            "Thieves' Cant",
            "Cunning Action" if level >= 2 else None
        ],
        "bard": [
            "Spellcasting",
            "Bardic Inspiration",
            "Jack of All Trades" if level >= 2 else None,
            "Song of Rest" if level >= 2 else None,
        ],
        # Warlock invocations are added to reflect combat cantrip enhancements
        "warlock": [
            "Eldritch Invocations",
            "Agonizing Blast (add CHA to Eldritch Blast damage)",
            "Repelling Blast (pushes target when hit by Eldritch Blast)",
            "Pact Magic"
        ],
    }

    background_features = {
        "soldier": ["Military Rank"],
        "acolyte": ["Shelter of the Faithful"],
        "criminal": ["Criminal Contact"],
        "artisan": ["Guild Membership"],
        "entertainer": ["By Popular Demand"],
        "scholar": ["Researcher Access"],
    }

    features = []
    features += race_features.get(race, [])
    features += [f for f in class_features.get(char_class, []) if f]
    features += background_features.get(background, [])

    if features:
        formatted = "\n".join(f"- {f}" for f in features)
        existing = character_data.get("Features&Traits", "").strip()
        character_data["Features&Traits"] = f"{existing}\n{formatted}" if existing else formatted
    else:
        character_data["Features&Traits"] = "None yet."


    # New deterministic equipment logic
    # Add class-appropriate equipment pack

    # Generate main gear list
    indices = select_equipment(race, char_class, background, level)

    # Add equipment pack
    pack_index_map = {
        "barbarian": 86, "bard": 85, "cleric": 166, "druid": 86,
        "fighter": 82, "monk": 86, "paladin": 166, "ranger": 86,
        "rogue": 41, "sorcerer": 82, "warlock": 188, "wizard": 188
    }
    pack_index = pack_index_map.get(char_class)
    if pack_index is not None:
        indices.append(pack_index)

    # Final output to EquipmentIdx and Equipment
    sorted_indices = sorted(indices)
    character_data["EquipmentIdx"] = sorted_indices

    with open(os.path.join(os.path.dirname(__file__), "../data/equipment_indexed_extended.json"), "r", encoding="utf-8") as f:
        equipment_data = json.load(f)
        index_to_name = {int(idx): data["Name"].lower() for idx, data in equipment_data.items()}
    # Convert index numbers to item names, one per line
    equipment_names = [index_to_name.get(idx, f"Item {idx}") for idx in sorted_indices]
    # Split into chunks: 13 to Equipment, 15 each to AdditionalFeatures&Traits and AdditionalFeatures&TraitsA
    character_data["Equipment"] = "\n".join(equipment_names[:13])
    if len(equipment_names) > 13:
        print("\n cont. in ADDITIONAL FEATURES & TRAITS")
    character_data["AdditionalFeatures&Traits"] = "\n".join(equipment_names[13:28]) if len(equipment_names) > 13 else ""
    character_data["AdditionalFeatures&TraitsA"] = "\n".join(equipment_names[28:43]) if len(equipment_names) > 28 else ""

    # Find the weapons
    weaponlist = []

    for idx in sorted_indices:
        item = equipment_data.get(str(idx))
        if item and item.get("IsWeapon") is True:
            weaponlist.append(item.get("Index", idx))

    character_data["WeaponIndices"] = sorted(weaponlist)

    # Coinage generation
    try:
        coins = assign_starting_coins(level)
        for key in ["CP", "SP", "EP", "GP", "PP"]:
            character_data[key] = str(coins.get(key, 0))
    except Exception as e:
        print("Error generating coin values:", e)

