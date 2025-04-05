import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")

def load_json(file_name):
    with open(os.path.join(DATA_DIR, file_name), "r") as f:
        return json.load(f)

def save_json(file_name, data):
    with open(os.path.join(DATA_DIR, file_name), "w") as f:
        json.dump(data, f, indent=4)