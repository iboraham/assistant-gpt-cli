import time
from typing import Callable

import inquirer
from halo import Halo
from rich.prompt import Prompt

from .error_handling import handleError
from .ui_utils import clear_screen, console


def _input_tools():
    """
    Handles the input for selecting assistant tools.

    Returns:
        List[str]: A list of selected tools.
    """
    assistant_tools = inquirer.list_input(
        "Please select assistant tools",
        choices=[
            "code_interpreter",
            "retrieval",
            "both",
            "none",
        ],
        carousel=True,
    )
    if assistant_tools == "none":
        return []
    elif assistant_tools == "both":
        return ["code_interpreter", "retrieval"]
    else:
        return [assistant_tools]


def create_assistant(api):
    """
    Creates a new assistant based on user input.

    Args:
        api: API object to interact with the backend.
    """
    # Collect assistant details from user
    assistant_model = Prompt.ask(
        "Please enter assistant model", default="gpt-4-1106-preview"
    )
    assistant_name = Prompt.ask("Please enter assistant name")
    assistant_description = Prompt.ask("Please enter assistant description")
    assistant_instructions = Prompt.ask("Please enter assistant instructions")
    assistant_tools = _input_tools()

    # Attempt to create an assistant
    try:
        api.create_assistant(
            assistant_name,
            assistant_description,
            assistant_model,
            assistant_instructions,
            assistant_tools,
        )
    except Exception as e:
        handleError(e, assistant_dashboard, [api])
    else:
        console.print(
            f"[bold green]Assistant '{assistant_name}' created successfully.[/bold green]"
        )
        time.sleep(1)
        clear_screen()
        assistant_dashboard(api)


def assistant_dashboard(api):
    """
    Displays the dashboard for the assistant and handles navigation.

    Args:
        api: API object to interact with the backend.
    """
    from .thread_management import threads_dashboard

    clear_screen()
    # Display assistant details
    display_assistant_details(api)

    # Handle user options for assistant management
    manage_assistant_options(api)


def display_assistant_details(api):
    """
    Display the details of the current assistant.

    Args:
        api: API object to interact with the backend.
    """
    console.print(f"[bold green]Assistant[/bold green]: {api.assistant.name}")
    console.print(f"[bold green]Description[/bold green]: {api.assistant.description}")
    console.print(f"[bold green]Model[/bold green]: {api.assistant.model}")
    console.print(
        f"[bold green]Instructions[/bold green]: {api.assistant.instructions}"
    )
    console.print(f"[bold green]Tools[/bold green]: {api.assistant.tools}")
    display_uploaded_files(api)


def display_uploaded_files(api):
    """
    Display the list of uploaded files for the assistant.

    Args:
        api: API object to interact with the backend.
    """
    if api.assistant.file_ids:
        filenames = [
            api.client.files.retrieve(file_id).filename
            for file_id in api.assistant.file_ids
        ]
        console.print(
            f"[bold green]Files uploaded[/bold green]: {', '.join(filenames)}"
        )
    else:
        console.print(f"[bold green]Files uploaded[/bold green]: No files uploaded yet")


def manage_assistant_options(api):
    """
    Manage the options for editing, deleting, or managing files of the assistant.

    Args:
        api: API object to interact with the backend.
    """
    from .thread_management import threads_dashboard

    options = [
        "Continue",
        "Edit assistant",
        "Manage files",
        "Delete assistant",
        "Back",
    ]
    selected_option = inquirer.list_input(
        f"You've selected an assistant {api.assistant.name}. What would you like to do?",
        choices=options,
        carousel=True,
    )

    if selected_option == options[0]:
        threads_dashboard(api)
    elif selected_option == options[1]:
        edit_assistant(api)
    elif selected_option == options[2]:
        # Manage files
        clear_screen()
        files_dashboard(api, assistant_dashboard)
    elif selected_option == options[3]:
        delete_assistant(api)
    elif selected_option == options[4]:
        api.assistant = None
        select_assistant(api)


def edit_assistant(api):
    """
    Allows the user to edit the details of the assistant.

    Args:
        api: API object to interact with the backend.
    """
    # Collect new details from user
    name = Prompt.ask("Please enter assistant name", default=api.assistant.name)
    description = Prompt.ask(
        "Please enter assistant description", default=api.assistant.description
    )
    model = Prompt.ask("Please enter assistant model", default=api.assistant.model)
    instructions = Prompt.ask(
        "Please enter assistant instructions",
        default=api.assistant.instructions,
    )
    tools = _input_tools()

    # Attempt to edit the assistant
    try:
        api.edit_assistant(name, description, model, instructions, tools)
        console.print(
            f"[bold green]Assistant '{api.assistant.name}' edited successfully![/bold green]"
        )
        time.sleep(1)
        assistant_dashboard(api)
    except Exception as e:
        handleError(e, assistant_dashboard, [api])


def delete_assistant(api):
    """
    Deletes the selected assistant.

    Args:
        api: API object to interact with the backend.
    """

    api.client.beta.assistants.delete(assistant_id=api.assistant.id)
    console.print(
        f"[bold green]Assistant '{api.assistant.name}' deleted successfully![/bold green]"
    )
    api.assistant = None
    time.sleep(1)
    select_assistant(api)


def files_dashboard(api, back: Callable = assistant_dashboard):
    """
    Displays the dashboard for managing files associated with the assistant.

    Args:
        api: API object to interact with the backend.
        back (Callable): Function to call when navigating back.
    """
    clear_screen()
    assert api.assistant is not None, "No assistant selected"

    manage_file_options(api, back)


def manage_file_options(api, back: Callable):
    """
    Handles the options for managing files of the assistant.

    Args:
        api: API object to interact with the backend.
        back (Callable): Function to call when navigating back.
    """
    list_files = get_uploaded_files(api)
    choices = ["New File", "Back", *["Remove file: " + file for file in list_files]]
    selected_option = inquirer.list_input(
        "Please select an option", choices=choices, carousel=True
    )

    if selected_option == "New File":
        upload_new_file(api, back)
    elif selected_option == "Back":
        back(api)
    else:
        remove_selected_file(api, selected_option, back)


def get_uploaded_files(api):
    """
    Retrieves a list of filenames of files uploaded to the assistant.

    Args:
        api: API object to interact with the backend.

    Returns:
        List[str]: List of uploaded filenames.
    """
    return [
        api.client.files.retrieve(file_id).filename
        for file_id in api.assistant.file_ids
    ]


def upload_new_file(api, back: Callable):
    """
    Handles the upload of a new file to the assistant.

    Args:
        api: API object to interact with the backend.
        back (Callable): Function to call when navigating back.
    """
    file_path = Prompt.ask("Please enter file path")
    try:
        upload_file(api, file_path)
        console.print(
            f"[bold green]File '{file_path}' uploaded successfully![/bold green]"
        )
    except Exception as e:
        handleError(e, files_dashboard, [api, back])
    finally:
        time.sleep(1)
        files_dashboard(api, back)


def upload_file(api, file_path):
    """
    Uploads a file to the assistant.

    Args:
        api: API object to interact with the backend.
        file_path (str): Path of the file to be uploaded.
    """
    with Halo(text="Uploading file...", spinner="dots") as spinner:
        try:
            file = api.client.files.create(
                file=open(file_path, "rb"), purpose="assistants"
            )
            spinner.succeed("File uploaded successfully!")

            # Assign file to assistant
            api.assistant = api.client.beta.assistants.update(
                assistant_id=api.assistant.id,
                file_ids=[file.id],
            )
        except Exception as e:
            spinner.fail("Error:")
            raise e


def remove_selected_file(api, selected_option, back: Callable):
    """
    Removes a selected file from the assistant.

    Args:
        api: API object to interact with the backend.
        selected_option (str): The file to be removed.
        back (Callable): Function to call when navigating back.
    """
    file_to_remove = selected_option.replace("Remove file: ", "")
    try:
        api.client.files.delete(file_id=file_to_remove)
        console.print(
            f"[bold green]File '{file_to_remove}' removed successfully![/bold green]"
        )
    except Exception as e:
        handleError(e, files_dashboard, [api, back])
    finally:
        time.sleep(1)
        files_dashboard(api, back)


def select_assistant(api):
    """
    Allows the user to select an assistant from the list of available assistants.

    Args:
        api: API object to interact with the backend.
    """
    from .dashboard import dashboard

    assistants = api.list_assistants()
    clear_screen()
    handle_assistant_selection(api, assistants)


def handle_assistant_selection(api, assistants):
    """
    Handles the assistant selection process.

    Args:
        api: API object to interact with the backend.
        assistants: List of available assistants.
    """
    from .dashboard import dashboard

    if not assistants.data:
        handle_no_assistants_available(api)
        return

    selected_assistant = choose_assistant(assistants)
    if selected_assistant == "Back":
        return dashboard(api)

    set_selected_assistant(api, assistants, selected_assistant)
    assistant_dashboard(api)


def handle_no_assistants_available(api):
    """
    Handles the scenario where no assistants are available.

    Args:
        api: API object to interact with the backend.
    """
    console.print("[yellow]No assistants available. Please create a new one.[/yellow]")
    response = inquirer.list_input(
        "What would you like to do?",
        choices=["Back", "Quit"],
        carousel=True,
    )
    if response == "Back":
        assistant_dashboard(api)


def choose_assistant(assistants):
    """
    Prompts the user to choose an assistant.

    Args:
        assistants: List of available assistants.

    Returns:
        str: The name of the selected assistant or 'Back'.
    """
    return inquirer.list_input(
        "Please select an assistant:",
        choices=[*[assistant.name for assistant in assistants], "Back"],
        carousel=True,
    )


def set_selected_assistant(api, assistants, selected_assistant_name):
    """
    Sets the selected assistant in the API object.

    Args:
        api: API object to interact with the backend.
        assistants: List of available assistants.
        selected_assistant_name (str): Name of the selected assistant.
    """
    selected_assistant = [
        assistant
        for assistant in assistants
        if assistant.name == selected_assistant_name
    ][0]
    api.assistant = selected_assistant
