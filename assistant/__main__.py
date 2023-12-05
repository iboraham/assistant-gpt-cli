import logging
import time

import inquirer

from . import ascii_art
from .api_validation import check_api_key
from .api_wrapper import AssistantAPIWrapper
from .config_manager import read_config, reset_config, save_config
from .dashboard import dashboard
from .ui_utils import clear_screen, console, welcome_user


def main():
    config = read_config()
    if config is None:
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
        api_key = response["api_key"]
        name = response["name"]
        clear_screen()

        save_config(api_key, name)
    else:
        api_key = config["api_key"]
        name = config["name"]

        # Ask if user wants to change API key or check it or continue
        options = ["Continue", "Change API key", "Check the API key"]
        selected_option = inquirer.list_input(
            "Would you like to ", choices=options, carousel=True
        )
        if selected_option == options[1]:
            reset_config()
            main()
        elif selected_option == options[2]:
            if not check_api_key(api_key):
                reset_config()
                main()

    clear_screen()
    welcome_user(name)
    time.sleep(1)

    api = AssistantAPIWrapper(api_key, name)
    return dashboard(api)


if __name__ == "__main__":
    # Print welcome message
    console.print(ascii_art.ascii_welcome)
    time.sleep(1)
    clear_screen()

    # Confirm debug mode with user
    debug = inquirer.list_input(
        "Would you like to enable debug mode?", choices=["Yes", "No"], carousel=True
    )
    debug = debug == "Yes"
    clear_screen()

    if debug:
        logging.basicConfig(level=logging.INFO)
    main()
