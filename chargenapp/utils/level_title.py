def get_level_title(char_class, level):
    class_map = {
        "Fighter": ["Fighter", "Sergeant", "Fighting Master", "Captain", "Captain of the Realm",
                    "Champion", "Grand Champion", "Chieftain", "Lord", "Grand Lord"],
        "Paladin": ["Fighter", "Sergeant", "Fighting Master", "Captain", "Captain of the Realm",
                    "Champion", "Grand Champion", "Chieftain", "Lord", "Grand Lord"],
        "Ranger": ["Fighter", "Sergeant", "Fighting Master", "Captain", "Captain of the Realm",
                   "Champion", "Grand Champion", "Chieftain", "Lord", "Grand Lord"],

        "Sorcerer": ["Magician", "Thaumaturge", "Dweomer Master", "Wizard", "Wizard of the Realm",
                     "Magus", "Grand Magus", "Warlock", "Sorcerer", "Grand Sorcerer"],
        "Warlock":  ["Magician", "Thaumaturge", "Dweomer Master", "Wizard", "Wizard of the Realm",
                     "Magus", "Grand Magus", "Warlock", "Sorcerer", "Grand Sorcerer"],
        "Wizard":   ["Magician", "Thaumaturge", "Dweomer Master", "Wizard", "Wizard of the Realm",
                     "Magus", "Grand Magus", "Warlock", "Sorcerer", "Grand Sorcerer"],

        "Cleric": ["Initiate", "Adept", "Shrine Master", "Priest", "Priest of the Realm",
                   "Shaman", "Grand Shaman", "Cultmaster", "Archon", "Grand Archon"],
        "Druid":  ["Initiate", "Adept", "Shrine Master", "Priest", "Priest of the Realm",
                   "Shaman", "Grand Shaman", "Cultmaster", "Archon", "Grand Archon"],
        "Monk":   ["Initiate", "Adept", "Shrine Master", "Priest", "Priest of the Realm",
                   "Shaman", "Grand Shaman", "Cultmaster", "Archon", "Grand Archon"],

        "Barbarian": ["Stripling", "Bandit", "Horsethief", "Raider", "Highwayman",
                      "Bandsman", "Bandchief", "Chieftain", "Khan", "Great Khan"],
        "Rogue":     ["Stripling", "Bandit", "Horsethief", "Raider", "Highwayman",
                      "Bandsman", "Bandchief", "Chieftain", "Khan", "Great Khan"],

        "Bard": ["Tinker", "Journeyman", "Songmaster", "Spinner of Tales", "Conjurer",
                 "Talenti", "Luminary", "Elysial", "Great Muse", "God-Muse"],
    }

    level_ranges = [
        range(1, 4),    # 1–3
        range(4, 7),    # 4–6
        range(7, 10),   # 7–9
        range(10, 14),  # 10–13
        range(14, 18),  # 14–17
        range(18, 21),  # 18–20
        range(21, 24),  # 21–23
        range(24, 28),  # 24–27
        range(28, 30),  # 28–29
        range(30, 100), # 30+
    ]

    print(f"😍char_class is: {char_class} ({type(char_class)})")

    titles = class_map.get(char_class)
    if not titles:
        return "Unknown Class"

    for i, r in enumerate(level_ranges):
        if level in r:
            return titles[i]
    
    return "Unknown Level"
