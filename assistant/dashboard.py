import inquirer
from .api_wrapper import AssistantAPIWrapper
from .ui_utils import app_exit, clear_screen
from .assistant_operations import create_assistant, select_assistant


def dashboard(api: AssistantAPIWrapper):
    """
    Displays the main dashboard and handles the selection of different options
    for managing assistants.

    Args:
        api (AssistantAPIWrapper): An instance of the API wrapper to interact with the backend.
    """
    clear_screen()
    manage_dashboard_options(api)


def manage_dashboard_options(api: AssistantAPIWrapper):
    """
    Manages the options in the dashboard for creating, selecting, or quitting the application.

    Args:
        api (AssistantAPIWrapper): An instance of the API wrapper.
    """
    options = ["Create a new assistant", "Manage an existent assistant", "Quit"]
    selected_option = inquirer.list_input(
        "Please select an option", choices=options, carousel=True
    )

    if selected_option == options[0]:
        handle_create_new_assistant(api)
    elif selected_option == options[1]:
        handle_manage_existing_assistant(api)
    elif selected_option == options[2]:
        handle_app_quit()


def handle_create_new_assistant(api: AssistantAPIWrapper):
    """
    Handles the creation of a new assistant.

    Args:
        api (AssistantAPIWrapper): An instance of the API wrapper.
    """
    create_assistant(api)
    clear_screen()


def handle_manage_existing_assistant(api: AssistantAPIWrapper):
    """
    Handles the management of an existing assistant.

    Args:
        api (AssistantAPIWrapper): An instance of the API wrapper.
    """
    select_assistant(api)
    clear_screen()


def handle_app_quit():
    """
    Handles the quitting of the application.
    """
    app_exit()
