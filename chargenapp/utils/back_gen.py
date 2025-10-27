import random
from chargenapp.utils.openai_gen import openaigen


def weight_to_build(weight, thresholds):
    """Determine body type based on weight thresholds."""
    low, high = thresholds
    print('🤣 LOW & HI:', low, high)
    if weight < low:
        return random.choice(["slight", "lean", "lithe"])
    elif weight > high:
        return random.choice(["stocky", "burly", "thickset"])
    else:
        return random.choice(["average", "fit", "proportional"])


# Physical trait tables by race
physical_trait_tables = {
    "Elf": {
        "Age": lambda: str(random.randint(100, 750)),
        "Height": lambda: f"{random.randint(5, 6)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(100, 150),
        "WeightThresholds": (110, 135),
        "Eyes": ["violet", "green", "hazel", "silver", "blue"],
        "Skin": ["pale", "bronzed", "copper", "fair"],
        "Hair": ["white", "silver", "blond", "auburn", "black"]
    },
    "Dwarf": {
        "Age": lambda: str(random.randint(40, 350)),
        "Height": lambda: f"{random.randint(4, 5)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(150, 200),
        "WeightThresholds": (160, 185),
        "Eyes": ["brown", "gray", "hazel", "black"],
        "Skin": ["ruddy", "tan", "earthy", "light brown"],
        "Hair": ["brown", "red", "black", "gray"]
    },
    "Human": {
        "Age": lambda: str(random.randint(18, 80)),
        "Height": lambda: f"{random.randint(5, 6)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(120, 220),
        "WeightThresholds": (140, 190),
        "Eyes": ["blue", "brown", "green", "hazel", "gray"],
        "Skin": ["fair", "tan", "brown", "olive", "dark"],
        "Hair": ["black", "brown", "blond", "red", "gray"]
    },
    "Half-Elf": {
        "Age": lambda: str(random.randint(20, 180)),
        "Height": lambda: f"{random.randint(5, 6)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(110, 170),
        "WeightThresholds": (125, 160),
        "Eyes": ["green", "blue", "hazel", "gray"],
        "Skin": ["pale", "olive", "tan"],
        "Hair": ["black", "brown", "blond", "auburn"]
    },
    "Halfling": {
        "Age": lambda: str(random.randint(20, 100)),
        "Height": lambda: f"{random.randint(2, 3)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(30, 45),
        "WeightThresholds": (34, 42),
        "Eyes": ["brown", "hazel", "green"],
        "Skin": ["ruddy", "rosy", "fair", 'black'],
        "Hair": ["brown", "sandy", "red"]
    },
    "Orc": {
        "Age": lambda: str(random.randint(14, 50)),
        "Height": lambda: f"{random.randint(5, 7)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(180, 250),
        "WeightThresholds": (190, 230),
        "Eyes": ["red", "yellow", "black"],
        "Skin": ["gray", "green-gray", "dark green"],
        "Hair": ["black", "gray", "white"]
    },
    "Gnome": {
        "Age": lambda: str(random.randint(40, 300)),
        "Height": lambda: f"{random.randint(3, 4)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(35, 45),
        "WeightThresholds": (36, 42),
        "Eyes": ["blue", "green", "hazel"],
        "Skin": ["pink", "light brown", "tan"],
        "Hair": ["white", "gray", "blond", "brown"]
    },
    "Tiefling": {
        "Age": lambda: str(random.randint(18, 100)),
        "Height": lambda: f"{random.randint(5, 6)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(120, 200),
        "WeightThresholds": (130, 180),
        "Eyes": ["black", "red", "gold", "white"],
        "Skin": ["purple", "crimson", "ashen", "dark gray", "reddish"],
        "Hair": ["black", "dark red", "purple", "white", "none"]
    },
    "Dragonborn": {
        "Age": lambda: str(random.randint(15, 80)),
        "Height": lambda: f"{random.randint(6, 7)}' {random.choice(['0', '2', '4', '6', '8', '10'])}\"",
        "Weight": lambda: random.randint(220, 320),
        "WeightThresholds": (240, 300),
        "Eyes": ["gold", "bronze", "copper", "silver"],
        "Skin": ["red", "blue", "green", "bronze", "white", "black"],
        "Hair": ["none"]
    }
}


def generate_physical_traits(race):
    table = physical_trait_tables.get(race.title(), physical_trait_tables["Human"])
    age = table["Age"]()
    height = table["Height"]()
    weight = table.get("Weight", lambda: random.randint(120, 200))()
    build = weight_to_build(weight, table["WeightThresholds"])
    return {
        "Age": age,
        "Height": height,
        "Weight": str(weight),
        "Build": build,
        "Eyes": random.choice(table["Eyes"]),
        "Skin": random.choice(table["Skin"]),
        "Hair": random.choice(table["Hair"]),
    }


def backgen(name, sex, alignment, race, char_class, background, known_languages):
    # generate name if required
    if not name:
        prompt = (
            f"Create a name for a fantasy character. Use one or two words, no more.\n"
            f"Examples:\n"
            f"1. Elf Ranger: Faelar\n"
            f"2. Dwarf Warrior: Thrain\n"
            f"3. Orc Shaman: Grozug\n"
            f"4. {sex} {race} {char_class}:\n"
        )
        name = str(openaigen(prompt, 5))

    prompt = f"Create a brief backstory for a {sex} {alignment} {race} {char_class} with {background} background who speaks {known_languages} named {name}. No more than 660 characters. End your response with a complete sentence."
    backstory = str(openaigen(prompt, 175))

    prompt = f"List three brief character traits for a {sex} {race} {char_class}, separated by commas. No more than 80 characters. End your response with a complete sentence."
    traits = str(openaigen(prompt, 5))

    prompt = f"Give one brief character ideal for a {sex} {race} {char_class} with {backstory} backstory. No more than 80 characters. End your response with a complete sentence."
    ideal = str(openaigen(prompt, 5))

    prompt = f"Give a terse description of bonds for a {sex} {race} {char_class} with {backstory} backstory. No more than 80 characters. End your response with a complete sentence."
    bonds = str(openaigen(prompt, 5))

    prompt = f"Briefly describe a flaw for a {sex} {race} {char_class} with {backstory} backstory. No more than 80 characters. End your response with a complete sentence."
    flaw = str(openaigen(prompt, 5))

    prompt = f"Briefly describe one organizational affiliation for a {sex} {race} {char_class} with {backstory} backstory. No more than 80 characters. End your response with a complete sentence."
    allies = str(openaigen(prompt, 75))

    physical_traits = generate_physical_traits(race)

    return name, backstory, traits, ideal, bonds, flaw, physical_traits, allies
