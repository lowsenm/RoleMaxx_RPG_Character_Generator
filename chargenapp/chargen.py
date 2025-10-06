import importlib.util
import sys
import subprocess
#from utils.story_gen import generate_backstory
import re
from .utils.build_char import build_character
from .utils.char_stats import generate_character_stats
#from utils.trait_gen import generate_traits
#from utils.back_gen_local import gen_traits, build_prompt, build_backstory, backgen, gen_name
from .utils.fill_pdf import fillpdf
from .utils.stat_mods import calculate_modifiers
from .utils.level_title import get_level_title
#from utils.name_gen import generate_fantasy_name
#from utils.groq_gen import groqgen
import json
from .utils.skill_gen import skillgen
from .utils.pageone_gen import add_features_traits_and_gear
from .utils.back_gen import backgen, generate_physical_traits
from .utils.combat_stats import calculate_combat_stats
from .utils.spellcast import fill_spellcasting_info, get_spell_data
from .utils.attackparser import parse_attacks
from .utils.openai_gen import generate_character_image
from .utils.final_stats import calculate_saving_throws, assign_treasure
import os
from django.conf import settings
from .utils.logdata import log_character


# MAIN GENERATE ROUTINE

def chargen_call(character_data):
    print("👌 Beginning generative routines")

    race = character_data["Race"]
    sex = character_data["Sex"]
    char_class = character_data["Class"]
    background = character_data["Background"]
    level = int(character_data["Level"])
    alignment = character_data["Alignment"]
    name = character_data["CharacterName"]

    title = get_level_title(char_class, level)
    known_languages = []
    known_languages = build_character(known_languages, race, sex, char_class, background, level, alignment)

    # Generate background
    name, backstory, traits, ideal, bonds, flaw, physical_traits, allies = backgen(name, sex, alignment, race, char_class, background, known_languages)
#non-gen test line: "A", "B", "C", "D", "E", {}, "G"

    # Create char data to send to pdfrw
    char_stats = generate_character_stats(race, char_class, level)
    stats = char_stats["stats"]
    character_data.update({
        "CharacterName": name,
        "CharacterNameA": name,
        "LevelTitle": title,
        "PersonalityTraits": traits,
        "OtherProficiencies&Languages": ", ".join(known_languages),
        "Backstory": backstory,
        "Ideals": ideal,
        "Bonds": bonds,
        "Flaws": flaw,
        "XP": char_stats["XP"],
        "Level": char_stats["level"],
        "Allies&Organizations": allies
    })

    # Add the ability scores
    for ability, value in stats.items():
        character_data[ability] = str(value)

    # Add all six ability scores (must be string values!)
    for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
        character_data[ability] = str(stats[ability])
        character_data.update(calculate_modifiers(stats))

    # Add combat stats
    calculate_combat_stats(character_data)

    # Add features traits and gear
    add_features_traits_and_gear(character_data)
    #print("chargen chardat WeaponIndices:", character_data["WeaponIndices"])

    # Discover key attacks
    parse_attacks(character_data)

    # Generate skillz, physical data and update character_data
    character_data.update(skillgen(character_data))

    character_data.update({
        "Age": physical_traits.get("Age", ""),
        "Height": physical_traits.get("Height", ""),
        "Weight": physical_traits.get("Weight", ""),
        "Eyes": physical_traits.get("Eyes", ""),
        "Skin": physical_traits.get("Skin", ""),
        "Build": physical_traits.get("Build", ""),
        "Hair": physical_traits.get("Hair", "")
    })

    character_data.update({"Appearance": generate_character_image(character_data)})

        # Add saving throws and treasure
    character_data.update(calculate_saving_throws(character_data))
    character_data.update(assign_treasure(character_data))
    # print("⭐ ⭐ ⭐ ALL CHARACTER DATA SO FAR: ⭐ ⭐ ⭐/r", character_data)

    # Write the pdf w/ pdfrw
    print("😉 Writing PDF")

    file_path = os.path.join(settings.BASE_DIR, "charsheets")
    pdf_path = f"{file_path}/{character_data['CharacterName']}.pdf"

    # Define known spellcasting classes
    spellcasting_classes = {
        "Bard", "Cleric", "Druid", "Sorcerer", "Wizard", "Warlock",
        "Paladin", "Ranger", "Artificer"
    }

    # Transfer DexMod to Initiative
    dex_mod = character_data.get("DexMod", "0")
    character_data["Initiative"] = dex_mod

    # If the class is a spellcaster, call fill_spellcasting_info
    if char_class in spellcasting_classes:
        character_data.update(fill_spellcasting_info(char_class, character_data))

    fillpdf(f"{settings.BASE_DIR}/charsheet_chart.pdf", pdf_path, character_data)

    # Log character data
    file_path = os.path.join(settings.BASE_DIR, "chargenapp/data/chardatalog.json")
    log_character(character_data, file_path)

    return pdf_path
