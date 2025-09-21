import requests

HF_API_TOKEN = "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"
MODEL = "gpt2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_traits(race, char_class, max_tokens=40):
    prompt = (
        f"List three brief character traits for a {race} {char_class}, "
        f"separated by commas."
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.7,
            "do_sample": True,
            "stop": ["\n"]
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            generated = response.json()[0]["generated_text"]
            traits = generated[len(prompt):].strip()
            # Clean trailing punctuation or newlines
            traits = traits.rstrip(".").strip()
            return traits
        except Exception as e:
            print("Error parsing response:", e)
            return None
    else:
        print("API Error:", response.status_code)
        print(response.text)
        return None

# Example usage
traits = generate_traits("Halfling", "Rogue")
print("Generated Traits:", traits)
