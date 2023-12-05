import inquirer

from .api_wrapper import AssistantAPIWrapper
from .ui_utils import app_exit, clear_screen


def dashboard(api: AssistantAPIWrapper):
    from .assistant_operations import create_assistant, select_assistant

    clear_screen()
    options = ["Create a new assistant", "Manage an existent assistant", "Quit"]
    selected_option = inquirer.list_input(
        "Please select an option", choices=options, carousel=True
    )

    if selected_option == options[0]:
        create_assistant(api)
        clear_screen()
    elif selected_option == options[1]:
        select_assistant(api)
        clear_screen()
    elif selected_option == options[2]:
        app_exit()
        return
