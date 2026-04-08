import json
import os

DATA_FILE = "robot_data.json"

DEFAULT_DB = {
    "FRANCIA-1516S-V": {
        "X": {"acc": 3000, "dec": 3000, "vel": 1800},
        "Y": {"acc": 4000, "dec": 4000, "vel": 1500},
        "Z": {"acc": 5000, "dec": 5000, "vel": 2500},
        "R": {"acc": 1000, "dec": 1000, "vel": 800},
        "S": {"acc": 1000, "dec": 1000, "vel": 800}
    },
    "FRANCIA-1013S-VE": {
        "X": {"acc": 3500, "dec": 3500, "vel": 2000},
        "Y": {"acc": 4500, "dec": 4500, "vel": 1800},
        "Z": {"acc": 5500, "dec": 5500, "vel": 3000},
        "R": {"acc": 1200, "dec": 1200, "vel": 1000},
        "S": {"acc": 1200, "dec": 1200, "vel": 1000}
    }
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DB)
        return DEFAULT_DB

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
