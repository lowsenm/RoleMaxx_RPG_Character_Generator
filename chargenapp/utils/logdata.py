import json, os, datetime

def log_character(character_data, file_path):
    # Make sure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Load whatever is there
    container = "list_root"   # or "dict_with_log"
    data = None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    # Coerce to a list we can append to
    if isinstance(data, dict):
        if "log" in data and isinstance(data["log"], list):
            log = data["log"]
            container = "dict_with_log"
        else:
            # Unexpected dict shape: start a new list but keep dict to preserve future fields
            log = []
            container = "dict_with_log"
            data.setdefault("log", log)
    elif isinstance(data, list):
        log = data
    else:
        # Corrupt/unknown -> start fresh
        log = []
        container = "list_root"

    # Build entry (adjust fields to your needs)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "character": character_data,  # or a subset if large
    }

    log.append(entry)

    # Write back atomically, preserving original container style
    to_write = data if container == "dict_with_log" else log
    tmp = file_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(to_write, f, ensure_ascii=False, indent=2)
    os.replace(tmp, file_path)
