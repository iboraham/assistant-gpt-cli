import time
from typing import Callable

import inquirer
from halo import Halo
from rich.prompt import Prompt

from .error_handling import handleError
from .ui_utils import clear_screen, console


def _input_tools():
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
        assistant_tools = []
    elif assistant_tools == "both":
        assistant_tools = ["code_interpreter", "retrieval"]
    else:
        assistant_tools = [assistant_tools]
    return assistant_tools


def create_assistant(api):
    assistant_model = Prompt.ask(
        "Please enter assistant model", default="gpt-4-1106-preview"
    )
    assistant_name = Prompt.ask("Please enter assistant name")
    assistant_description = Prompt.ask("Please enter assistant description")
    assistant_instructions = Prompt.ask("Please enter assistant instructions")
    assistant_tools = _input_tools()
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

    console.print(
        f"[bold green]Assistant '{assistant_name}' created successfully.[/bold green]"
    )
    time.sleep(1)
    clear_screen()
    assistant_dashboard(api)


def assistant_dashboard(api):
    from .thread_management import threads_dashboard

    clear_screen()

    console.print(f"[bold green]Assistant[/bold green]: {api.assistant.name}")
    console.print(f"[bold green]Description[/bold green]: {api.assistant.description}")
    console.print(f"[bold green]Model[/bold green]: {api.assistant.model}")
    console.print(
        f"[bold green]Instructions[/bold green]: {api.assistant.instructions}"
    )
    console.print(f"[bold green]Tools[/bold green]: {api.assistant.tools}")
    if api.assistant.file_ids != []:
        filenames = [
            api.client.files.retrieve(file_id).filename
            for file_id in api.assistant.file_ids
        ]
        console.print(
            f"[bold green]Files uploaded[/bold green]: {', '.join(filenames)}"
        )
    else:
        console.print(f"[bold green]Files uploaded[/bold green]: No files uploaded yet")

    console.print()

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
        # Edit assistant
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
        try:
            api.edit_assistant(name, description, model, instructions, tools)
            console.print(
                f"[bold green]Assistant '{api.assistant.name}' edited successfully![/bold green]"
            )
            time.sleep(1)
            assistant_dashboard(api)
        except Exception as e:
            handleError(e, assistant_dashboard, [api])
    elif selected_option == options[2]:
        # Manage files
        clear_screen()
        files_dashboard(api, assistant_dashboard)
    elif selected_option == options[3]:
        # Delete assistant
        api.client.beta.assistants.delete(assistant_id=api.assistant.id)
        console.print(
            f"[bold green]Assistant '{api.assistant.name}' deleted successfully![/bold green]"
        )
        api.assistant = None
        time.sleep(1)
        assistant_dashboard(api)
    elif selected_option == options[4]:
        api.assistant = None
        select_assistant(api)


def files_dashboard(api, back: Callable = assistant_dashboard):
    clear_screen()
    assert api.assistant is not None, "No assistant selected"
    list_files = [
        api.client.files.retrieve(file_id).filename
        for file_id in api.assistant.file_ids
    ]
    choices = ["New File", "Back", *["Remove file: " + file for file in list_files]]
    selected_option = inquirer.list_input(
        "Please select an option", choices=choices, carousel=True
    )

    if selected_option == "New File":
        file_path = Prompt.ask("Please enter file path")
        try:
            try:
                spinner = Halo(text="Uploading file...", spinner="dots").start()
                file = api.client.files.create(
                    file=open(file_path, "rb"), purpose="assistants"
                )
                spinner.succeed("File uploaded successfully!")
                time.sleep(1)
            except Exception as e:
                spinner.fail("Error:")
                raise e

            # Assign file to assistant
            api.assistant = api.client.beta.assistants.update(
                assistant_id=api.assistant.id,
                file_ids=[file.id],
            )
        except Exception as e:
            handleError(e, files_dashboard, [api, back])
        console.print(
            f"[bold green]File '{file_path}' uploaded successfully![/bold green]"
        )
        time.sleep(1)
        files_dashboard(api, back)
    elif selected_option == "Back":
        back(api)
    else:
        selected_option = selected_option.replace("Remove file: ", "")
        try:
            api.client.files.delete(file_id=selected_option)
        except Exception as e:
            handleError(e, files_dashboard, [api, back])
        console.print(
            f"[bold green]File '{selected_option}' removed successfully![/bold green]"
        )
        time.sleep(1)
        files_dashboard(api, back)


def select_assistant(api):
    from .dashboard import dashboard

    assistants = api.list_assistants()

    clear_screen()
    if assistants.data == []:
        console.print(
            "[yellow]No assistants available. Please create a new one.[/yellow]"
        )
        response = inquirer.list_input(
            "What would you like to do?",
            choices=["Back", "Quit"],
            carousel=True,
        )
        if response == "Back":
            return assistant_dashboard(api)
        else:
            return exit()

    selected_assistant = inquirer.list_input(
        "Please select an assistant:",
        choices=[*[assistant.name for assistant in assistants], "Back"],
        carousel=True,
    )
    if selected_assistant == "Back":
        return dashboard(api)
    selected_assistant = [
        assistant for assistant in assistants if assistant.name == selected_assistant
    ][0]
    api.assistant = selected_assistant
    assistant_dashboard(api)
