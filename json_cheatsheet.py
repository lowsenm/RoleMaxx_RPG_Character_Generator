import json
from pathlib import Path

# read
items = []
with open("spells.ndjson", encoding="utf-8") as f:
    for line in f:
        items.append(json.loads(line))

# write
with open("out.ndjson", "w", encoding="utf-8") as f:
    for item in items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

s = '{"name": "Magic Missile", "level": 1}'
obj = json.loads(s)

out = {"ok": True, "items": [1, 2, 3]}
Path("out.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
# or:
with open("out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

name = data.get("name") if isinstance(data, dict) else None
school = data.get("school", "Evocation")  # default value

for item in data:          # when data is a list
    print(item["name"])    # KeyError if missing
    print(item.get("desc", ""))  # safe

# All level-1 spells’ names
lvl1_names = [x["name"] for x in data if x.get("level") == 1]

# Map into a simpler structure
rows = [{"name": x.get("name"), "dmg": x.get("basic_damage")} for x in data]

# e.g., data = {"meta":{"author":{"name":"Dorrit"}}}
author = (((data or {}).get("meta") or {}).get("author") or {}).get("name")

import json
from pathlib import Path

all_items = []
for p in Path("data").glob("*.json"):
    with p.open(encoding="utf-8") as f:
        obj = json.load(f)
        if isinstance(obj, list):
            all_items.extend(obj)
        else:
            all_items.append(obj)

# read
items = []
with open("spells.ndjson", encoding="utf-8") as f:
    for line in f:
        items.append(json.loads(line))

# write
with open("out.ndjson", "w", encoding="utf-8") as f:
    for item in items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

import json

try:
    data = json.loads(bad_string)
except json.JSONDecodeError as e:
    print("Bad JSON:", e.msg, "at line", e.lineno, "col", e.colno)

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent  # this file’s directory
data_path = BASE_DIR / "chargenapp" / "data" / "spells.json"

import json, re
from pathlib import Path

rx = re.compile(r"\b(\d+)d(\d+)\b", re.IGNORECASE)

p = Path("data/spells.json")
with p.open(encoding="utf-8") as f:
    spells = json.load(f)

for s in spells:
    desc = s.get("description", "")
    m = rx.search(desc)
    s["basic_damage"] = m.group(0) if m else None

with open("data/spells_enriched.json", "w", encoding="utf-8") as f:
    json.dump(spells, f, ensure_ascii=False, indent=2)

import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("infile")
ap.add_argument("--out", default="out.json")
args = ap.parse_args()

with open(args.infile, encoding="utf-8") as f:
    data = json.load(f)

# … process data …

with open(args.out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

def expect_spell(x: dict) -> bool:
    return isinstance(x, dict) and "name" in x and "level" in x
