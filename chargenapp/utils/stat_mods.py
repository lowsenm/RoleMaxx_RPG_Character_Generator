STAT_NAMES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
STAT_ABBRS = ["Str", "Dex", "Con", "Int", "Wis", "Cha"]  # PDF field name prefixes


def calculate_modifiers(stat_dict):
    """
    Takes a dictionary of stats and returns PDF-friendly modifiers.
    Expects keys like 'Strength', 'Dexterity', etc.
    """
    def modifier(score):
        return f"{(int(score) - 10) // 2:+}"

    return {
        f"{abbr}Mod": modifier(stat_dict[full])
        for full, abbr in zip(STAT_NAMES, STAT_ABBRS)
    }
