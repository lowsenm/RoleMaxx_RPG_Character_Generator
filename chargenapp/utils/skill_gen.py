from .proficiency_rules import get_skill_proficiencies

def skillgen(character_data):
    from chargenapp.utils.proficiency_rules import get_skill_proficiencies

    skill_to_ability = {
        "Acrobatics": "DEX", "AnimalHandling": "WIS", "Arcana": "INT", "Athletics": "STR",
        "Deception": "CHA", "History": "INT", "Insight": "WIS", "Intimidation": "CHA",
        "Investigation": "INT", "Medicine": "WIS", "Nature": "INT", "Perception": "WIS",
        "Performance": "CHA", "Persuasion": "CHA", "Religion": "INT",
        "SleightOfHand": "DEX", "Stealth": "DEX", "Survival": "WIS"
    }

    checkbox_field_map = {skill: skill + "CB" for skill in skill_to_ability}

    race = character_data.get("Race", "").strip().lower()
    class_name = character_data.get("Class", "").strip().lower()
    background = character_data.get("Background", "").strip().lower()
    level = int(character_data.get("Level", 1))
    stats = character_data.get("Stats", {})

    prof_bonus = 2 + ((level - 1) // 4)
    result = {"ProficiencyBonus": f"+{prof_bonus}"}

    profs = get_skill_proficiencies(class_name, level, background, [], [], race)

    # fallback to 2 random proficiencies if all lookups fail
    if not profs:
        import random
        profs = random.sample(sorted(skill_to_ability.keys()), 2)


    for skill, ability in skill_to_ability.items():
        score = stats.get(ability, 10)
        mod = (score - 10) // 2
        has_prof = skill in profs

        if has_prof:
            mod += prof_bonus
            result[checkbox_field_map[skill]] = "•"
        else:
            result[checkbox_field_map[skill]] = " "

        result[skill] = "" if mod == 0 else f"{mod:+d}" if mod > 0 else str(mod)

    dex_mod = (stats.get("DEX", 10) - 10) // 2
    result["Initiative"] = "" if dex_mod == 0 else f"{dex_mod:+d}" if dex_mod > 0 else str(dex_mod)

    return result
