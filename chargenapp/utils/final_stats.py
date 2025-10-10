import os
import json
import random


def calculate_saving_throws(character_data):
    class_saves = {
        "Barbarian": ["Strength", "Constitution"],
        "Bard": ["Dexterity", "Charisma"],
        "Cleric": ["Wisdom", "Charisma"],
        "Druid": ["Intelligence", "Wisdom"],
        "Fighter": ["Strength", "Constitution"],
        "Monk": ["Strength", "Dexterity"],
        "Paladin": ["Wisdom", "Charisma"],
        "Ranger": ["Strength", "Dexterity"],
        "Rogue": ["Dexterity", "Intelligence"],
        "Sorcerer": ["Constitution", "Charisma"],
        "Warlock": ["Wisdom", "Charisma"],
        "Wizard": ["Intelligence", "Wisdom"],
        "Artificer": ["Constitution", "Intelligence"]
    }

    char_class = character_data.get("Class", "")
    proficient_saves = class_saves.get(char_class, [])
    saving_throws = {}

    for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
        mod_key = f"{ability}Mod"
        mod = int(character_data.get(mod_key, 0))
        bonus = mod + (2 if ability in proficient_saves else 0)

        bonus_str = f"{bonus:+d}" if bonus != 0 else ""
        save_field = f"{ability}ST"
        checkbox_field = ability[:3] + "CB"

        saving_throws[save_field] = bonus_str
        saving_throws[checkbox_field] = "•" if ability in proficient_saves else " "

    return saving_throws


def assign_treasure(character_data):
    level = int(character_data.get("Level", 1))
    count = max(1, level // 3)  # 1 item minimum

    # Load magic items from the JSON file
    json_path = os.path.join(os.path.dirname(__file__), "../data/magic_items.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            magic_items_data = json.load(f)
        magic_items = [item["name"] for item in magic_items_data if "name" in item]
    except Exception as e:
        print(f"Error loading magic items: {e}")
        magic_items = []

    # Fallback if loading fails
    if not magic_items:
        magic_items = [
            "Potion of Healing", "Bag of Holding", "Ring of Protection",
            "Wand of Magic Missiles", "Cloak of Invisibility", "Boots of Speed",
            "Sword of Sharpness", "Amulet of Health"
        ]

    # Mundane treasure table
    mundane_treasures = [
        "50 gp in assorted coins", "Jade statuette (25 gp)",
        "Ruby pendant (100 gp)", "Silk robe embroidered with gold (75 gp)",
        "Gold ring with sapphire (250 gp)", "Silver goblet (30 gp)",
        "Map to a hidden vault", "Set of jeweled dice (60 gp)"
    ]

    assigned_magic = random.sample(magic_items, min(count, len(magic_items)))
    assigned_loot = random.sample(mundane_treasures, min(count, len(mundane_treasures)))

    treasure_list = assigned_magic + assigned_loot
    character_data["Treasure"] = "\n".join(treasure_list)

    return character_data
