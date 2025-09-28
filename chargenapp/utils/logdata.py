import json
import os
from datetime import datetime


def log_character(character_data, filename):
    # Build entry
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "character_data": character_data
    }

    # Load existing log if present
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = []
    else:
        log = []

    # Append and write back
    log.append(entry)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"Logged character at {entry['timestamp']} into {filename}")

if __name__ == "__main__":
    log_character(character_data)
