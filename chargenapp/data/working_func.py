import json
import os

def remove_urls(obj):
    """Recursively remove all 'url' keys from nested dictionaries and lists."""
    if isinstance(obj, dict):
        return {
            k: remove_urls(v)
            for k, v in obj.items()
            if k != "url"
        }
    elif isinstance(obj, list):
        return [remove_urls(i) for i in obj]
    else:
        return obj

# Load original file
input_path = "weapons1.json"
output_path = "weapons.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Strip all URLs
cleaned_data = remove_urls(data)

# Save cleaned file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, indent=2)

print(f"URLs removed. Cleaned data saved to {output_path}")
