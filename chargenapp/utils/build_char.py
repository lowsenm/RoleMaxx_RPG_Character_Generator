import random


def pick_languages(existing, extra_count):
    """Let the user choose extra languages."""
    languages_all = [
        "Common", "Dwarvish", "Elvish", "Giant", "Gnomish", "Goblin", "Halfling", "Orc",
        "Abyssal", "Celestial", "Draconic", "Deep Speech", "Infernal", "Primordial", "Sylvan", "Underworld"
    ]
    available = sorted(list(set(languages_all) - set(existing)))
    chosen = []
    while len(chosen) < extra_count and available:
        print("\nAvailable languages:")
        for i, lang in enumerate(available):
            print(f"  {i + 1}. {lang}")
        try:
            choice = random.randint(1, len(available)) # int(input(f"Choose language {len(chosen)+1} of {extra_count}: ")) - 1
            if 0 <= choice < len(available):
                chosen.append(available.pop(choice))
                print('💕 langs chosen:', chosen)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a number.")
    return chosen

def build_character(known_languages, race, sex, char_class, background, level, alignment):

    races = [
        "Elf", "Dwarf", "Human", "Halfling", "Dragonborn", "Gnome",
        "Half-Elf", "Half-Orc", "Tiefling"
    ]

    sexes = ["Male", "Female", "Surprise me!"]

    classes = [
        "Fighter", "Wizard", "Rogue", "Barbarian", "Bard", "Cleric", "Druid",
        "Monk", "Paladin", "Ranger", "Sorcerer", "Warlock"
    ]

    alignments = [
        "Lawful Good", "Lawful Neutral", "Lawful Evil",
        "Neutral Good", "True Neutral", "Neutral Evil",
        "Chaotic Good", "Chaotic Neutral", "Chaotic Evil"
    ]

    backgrounds = [
        "Noble", "Soldier", "Scholar", "Shoemaker", "Artisan", "Criminal Organization",
        "Performer", "Petty Crook", "Trader-Traveler", "Street Urchin", "Spy",
        "Acolyte", "Ascetic", "Herder", "Farmer", "Local Hero", "Montaignard",
        "Forester", "Riverman"
    ]

    levels = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]

    racial_languages = {
        "Elf": ["Common", "Elvish"],
        "Dwarf": ["Common", "Dwarvish"],
        "Human": ["Common"],
        "Halfling": ["Common", "Halfling"],
        "Dragonborn": ["Common", "Draconic"],
        "Gnome": ["Common", "Gnomish"],
        "Half-Elf": ["Common", "Elvish"],
        "Half-Orc": ["Common", "Orc"],
        "Tiefling": ["Common", "Infernal"],
    }
    
    print("🧝 Welcome to the D&D Character Builder 🛠️")

    # Start with racial languages
    known_languages = list(racial_languages.get(race, ["Common"]))

    # Choose additional languages
    extra_languages = 0
    if race == "Human":
        extra_languages += 1
    elif race == "Half-Elf":
        extra_languages += 1
    if background in ["Scholar", "Acolyte", "Spy", "Trader-Traveler"]:
        extra_languages += 1

    if extra_languages:
        known_languages += pick_languages(known_languages, extra_languages)

    print("\n🎉 Character Created!")
    
    return(known_languages)
