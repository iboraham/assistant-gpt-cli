import argparse
import logging
import time

import inquirer

from . import ascii_art
from .api_validation import check_api_key
from .api_wrapper import AssistantAPIWrapper
from .config_manager import read_config, reset_config, save_config
from .dashboard import dashboard
from .ui_utils import clear_screen, console, welcome_user


def prompt_user_details():
    """
    Prompts the user for API key and name, validates the API key,
    and returns the entered details.
    """
    response = inquirer.prompt(
        [
            inquirer.Text(
                "api_key",
                message="Please enter your API key",
                validate=lambda _, x: check_api_key(x),
            ),
            inquirer.Text("name", message="Please enter your name"),
        ]
    )
    return response["api_key"], response["name"]


def handle_existing_config(config):
    """
    Handles the existing configuration by allowing the user to continue,
    change, or check the API key.
    Returns the API key and user's name.
    """
    api_key = config["api_key"]
    name = config["name"]

    options = ["Continue", "Change API key", "Check the API key"]
    selected_option = inquirer.list_input(
        "Would you like to", choices=options, carousel=True
    )

    if selected_option == options[1]:
        reset_config()
        return None, None
    elif selected_option == options[2] and not check_api_key(api_key):
        reset_config()
        return None, None

    return api_key, name


def main():
    """
    Entry point of the program.
    Manages configuration, user details, and launches the dashboard.
    """
    config = read_config()

    if config is None:
        api_key, name = prompt_user_details()
        if api_key and name:
            clear_screen()
            save_config(api_key, name)
    else:
        api_key, name = handle_existing_config(config)
        if api_key is None:
            return main()

    clear_screen()
    welcome_user(name)
    time.sleep(1)

    api = AssistantAPIWrapper(api_key, name)
    dashboard(api)


if __name__ == "__main__":
    console.print(ascii_art.ascii_welcome)
    time.sleep(1)
    clear_screen()

    # Argument parsing
    parser = argparse.ArgumentParser(description="Run the assistant program.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.INFO)

    main()
