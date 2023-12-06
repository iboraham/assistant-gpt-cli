import json
import os
from .error_handling import handleError

# Path to the configuration file
CONFIG_FILE = os.path.expanduser("~/.assistant-gpt-key.json")


def save_config(api_key, name):
    """
    Saves the configuration to a JSON file.

    Args:
        api_key (str): The API key to be saved.
        name (str): The name associated with the API key.
    """
    config = {"api_key": api_key, "name": name}
    try:
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(config, config_file)
    except Exception as e:
        handleError(e, "Error saving configuration")


def read_config():
    """
    Reads the configuration from a JSON file.

    Returns:
        dict or None: Returns the configuration as a dictionary if the file exists,
                      otherwise returns None.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as config_file:
                return json.load(config_file)
        except Exception as e:
            handleError(e, "Error reading configuration")
            return None
    else:
        return None


def reset_config():
    """
    Resets the configuration by deleting the configuration file.
    """
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
    except Exception as e:
        handleError(e, "Error resetting configuration")
