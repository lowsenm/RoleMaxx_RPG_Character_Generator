from openai import OpenAI
import time
import re, os
import random  # Make sure this is at the top if not already


# Set API key once
API_KEY = os.getenv('API_KEY')
client = OpenAI(api_key=API_KEY)

def truncate_at_period(text, max_length):
    if len(text) <= max_length:
        return text
    # Find all periods followed by a space within the limit
    sentences = list(re.finditer(r"\.(?:\s|$)", text))
    cutoff = 0
    for match in sentences:
        if match.end() <= max_length:
            cutoff = match.end()
        else:
            break
    # Fallback to simple truncation if no sentence ends within limit
    return text[:cutoff].strip() if cutoff > 0 else text[:max_length].strip()

def build_image_prompt(character_data):
    race = character_data.get("Race", "fantasy being")
    char_class = character_data.get("Class", "adventurer")
    build = character_data.get("Build")
    eyes = character_data.get("Eyes")
    hair = character_data.get("Hair")
    skin = character_data.get("Skin")
    gender = character_data.get("Sex", "character")
    mainweap = character_data.get("Attack1")

    # Random or customizable art style
    styles = [
        "black and white ink drawing",
        "watercolor painting",
        "pencil sketch",
        "digital painting with a soft color palette",
        "fantasy concept art",
        "charcoal drawing",
        "monochrome style",
        "illustration for a fantasy graphic novel",
        "classic RPG character sheet sketch",
        "studio Ghibli-style character portrait"
    ]
    art_style = character_data.get("ArtStyle", random.choice(styles))

    return (
        f"Portrait of a {gender} {race} {char_class}, with {hair} hair, "
        f"{eyes} eyes, and {skin} skin. {build} build. "
        f"Main weapon is {mainweap}. Rendered as a {art_style}. Do not add text!"
    )


def generate_character_image(character_data, size="1024x1024"):
    prompt = build_image_prompt(character_data)
    print(prompt) #DEBUG

    try:
        response = client.images.generate(
            prompt=prompt,
            n=1,
            size=size,
            model="dall-e-3"
        )
        print(f"DALL-E success: {response}")
        return response.data[0].url
    except Exception as e:
        print(f"DALL-E error: {str(e)}")
        print(f"Error type: {type(e)}")
        return None

def openaigen(prompt, tokens=150):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        time.sleep(2)  # avoid hitting RPM limits
        return completion.choices[0].message.content
    except Exception as e:
        print("Error in openaigen:", e)
        return " "

# Optional test run
if __name__ == "__main__":
    from chargen import character_data
    image_url = generate_character_image(character_data)
    if image_url:
        print("Character portrait URL:", image_url)
