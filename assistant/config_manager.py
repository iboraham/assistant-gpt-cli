import json
import os

CONFIG_FILE = os.path.expanduser("~/.assistant-gpt-key.json")


def save_config(api_key, name):
    config = {"api_key": api_key, "name": name}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None


def reset_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
