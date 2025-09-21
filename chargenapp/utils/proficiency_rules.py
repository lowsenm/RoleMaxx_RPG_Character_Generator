def get_skill_proficiencies(class_name, level, background, feats=None, multiclass=None, race=None):
    feats = feats or []
    multiclass = multiclass or []

    # Base class skill options (simplified)
    class_skills = {
        "fighter": ["Athletics", "Perception", "Survival", "Intimidation"],
        "rogue": ["Acrobatics", "Stealth", "Investigation", "SleightOfHand", "Deception", "Perception"],
        "wizard": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
        "cleric": ["History", "Insight", "Medicine", "Persuasion", "Religion"],
        "bard": ["Any"]  # Bards can choose any
    }

    class_default = {
        "fighter": 2,
        "rogue": 4,
        "wizard": 2,
        "cleric": 2,
        "bard": 3
    }

    background_skills = {
        "soldier": ["Athletics", "Intimidation"],
        "sage": ["Arcana", "History"],
        "criminal": ["Deception", "Stealth"],
        "acolyte": ["Insight", "Religion"],
        "noble": ["History", "Persuasion"]
    }

    feat_skills = {
        "Skilled": "any_3",
        "Prodigy": "any_1",
        "Skill Expert": "any_1"
    }

    race_skills = {
        "half-elf": "any_2",
        "human (variant)": "any_1",
        "wood elf": ["Perception"],
        "rock gnome": ["History"]
    }

    all_skills = {
        "Acrobatics", "AnimalHandling", "Arcana", "Athletics", "Deception",
        "History", "Insight", "Intimidation", "Investigation", "Medicine",
        "Nature", "Perception", "Performance", "Persuasion", "Religion",
        "SleightOfHand", "Stealth", "Survival"
    }

    proficiencies = set()

    # 1. Class proficiencies
    cname = class_name.lower()
    if cname in class_skills:
        skill_choices = class_skills[cname]
        count = class_default.get(cname, 2)
        if skill_choices == ["Any"]:
            proficiencies.update(sorted(all_skills)[:count])
        else:
            proficiencies.update(skill_choices[:count])

    # 2. Background
    proficiencies.update(background_skills.get(background.lower(), []))

    # 3. Feats
    for feat in feats:
        rule = feat_skills.get(feat)
        if rule == "any_3":
            proficiencies.update(sorted(all_skills - proficiencies)[:3])
        elif rule == "any_1":
            proficiencies.update(sorted(all_skills - proficiencies)[:1])

    # 4. Multiclass
    for entry in multiclass:
        alt_class = entry.get("class")
        if alt_class and alt_class.lower() in class_skills:
            proficiencies.update(class_skills[alt_class.lower()][:1])

    # 5. Race
    r = race.lower() if race else ""
    if r in race_skills:
        skill = race_skills[r]
        if isinstance(skill, list):
            proficiencies.update(skill)
        elif skill == "any_1":
            proficiencies.update(sorted(all_skills - proficiencies)[:1])
        elif skill == "any_2":
            proficiencies.update(sorted(all_skills - proficiencies)[:2])

    return sorted(proficiencies)
