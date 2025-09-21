import json
import csv

# Load the item types from CSV
item_types = {}
with open("item_types.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        index = row["Index"].strip()
        item_type = row["ItemType"].strip()
        item_types[index] = item_type

print("Loaded item types from CSV:")
print(item_types)

# Load equipment data
with open("equipment_indexed_extended.json", "r", encoding="utf-8") as f:
    equipment = json.load(f)

# Update each item with the ItemType from the CSV
for idx_str, item in equipment.items():
    item["ItemType"] = item_types.get(idx_str, "Unknown")

# Save updated data
with open("equipment_indexed_extended_with_types.json", "w", encoding="utf-8") as f:
    json.dump(equipment, f, indent=2)

print("\n✅ Updated equipment saved to 'equipment_indexed_extended_with_types.json'")
