import requests

# Your Hugging Face API token
HF_API_TOKEN = "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"

# Model URL
MODEL = "gpt2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_backstory(race, char_class, background, max_tokens=300):
    prompt = (
        f"Write a 150-word Dungeons & Dragons backstory for a {race} {char_class} "
        f"with the background of a {background}. The backstory should be in paragraph form, "
        f"character-rich, and immersive."
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.85,
            "do_sample": True,
            "stop": ["\n\n"]
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            generated = response.json()[0]["generated_text"]
            # Extract backstory (strip out prompt if included)
            backstory = generated[len(prompt):].strip()
            return backstory
        except Exception as e:
            print("Error parsing response:", e)
            return None
    else:
        print("API Error:", response.status_code)
        print(response.text)
        return None

# Example usage
backstory = generate_backstory("Halfling", "Rogue", "Artisan")
print("Generated Backstory:\n", backstory)
