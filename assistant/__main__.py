import json
import logging
import os
import time
from typing import Callable

import _messages
import inquirer
import openai
from _api_wrapper import AssistantAPIWrapper
from halo import Halo
from openai import OpenAI
from rich import print as rprint
from rich.console import Console
from rich.prompt import Prompt

# Constants and Setup
CONFIG_FILE = os.path.expanduser("~/.assistant-gpt-key.json")
THREAD_HISTORY = os.path.expanduser("~/.assistant-gpt-threads.json")
console = Console()
logger = logging.getLogger(__name__)


def check_api_key(api_key):
    spinner = Halo(text="Checking API key", spinner="dots")
    spinner.start()
    client = OpenAI(api_key=api_key)
    try:
        client.models.list()
    except openai.AuthenticationError as e:
        spinner.fail("Invalid API key!")
        logger.error(e)
        return False
    else:
        spinner.succeed("API key is valid 🎉")
        time.sleep(1)

        return True


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


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
    rprint(_messages.ascii_logo)


def welcome_user(name):
    rprint(f"[bold green]Welcome, {name}![/bold green]")


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


def dashboard(api: AssistantAPIWrapper):
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


def handleError(e: Exception, screen: Callable, function_args: list = []):
    console.print(f"[bold red]Error: {e}[/bold red]")
    # Press enter to continue
    input("Press enter to continue...")
    clear_screen()
    screen(*function_args)


def create_assistant(api):
    assistant_model = Prompt.ask(
        "Please enter assistant model", default="gpt-4-1106-preview"
    )
    assistant_name = Prompt.ask("Please enter assistant name")
    assistant_description = Prompt.ask("Please enter assistant description")
    assistant_instructions = Prompt.ask("Please enter assistant instructions")
    try:
        api.create_assistant(
            assistant_name,
            assistant_description,
            assistant_model,
            assistant_instructions,
        )
    except Exception as e:
        handleError(e, dashboard, [api])

    console.print(
        f"[bold green]Assistant '{assistant_name}' created successfully.[/bold green]"
    )
    time.sleep(1)
    clear_screen()
    assistant_dashboard(api)


def thread_history_read():
    if os.path.exists(THREAD_HISTORY):
        with open(THREAD_HISTORY, "r") as f:
            return json.load(f)
    return []


def thread_history_write(new_thread):
    thread_history = thread_history_read()
    thread_history.append(new_thread)
    with open(THREAD_HISTORY, "w") as f:
        json.dump(thread_history, f)


def threads_dashboard(api):
    clear_screen()
    assert api.assistant is not None, "No assistant selected"
    list_threads = thread_history_read()
    list_threads_ids = [
        thread["thread"]
        for thread in list_threads
        if thread["assistant"] == api.assistant.id
    ]
    list_threads_names = [
        thread["thread_name"]
        for thread in list_threads
        if thread["assistant"] == api.assistant.id
    ]
    choices = ["New Chat", "Back", *list_threads_names]
    selected_option = inquirer.list_input(
        "Please select an option", choices=choices, carousel=True
    )

    if selected_option == "New Chat":
        clear_screen()
        thread_name = Prompt.ask("Please enter thread name")
        api.thread_name = thread_name
        api.create_thread()
        thread_history_write(
            {
                "assistant": api.assistant.id,
                "thread": api.thread.id,
                "thread_name": api.thread_name,
                "user": api.username,
            }
        )
        chat(api)
    elif selected_option == "Back":
        api.assistant = None
        dashboard(api)
    else:
        selected_option_id = [
            thread["thread"]
            for thread in list_threads
            if thread["thread_name"] == selected_option
        ][0]
        thread = api.get_thread(selected_option_id)
        api.thread = thread
        api.thread_name = selected_option
        chat(api)


def log_message_history(message_history):
    console.print("Message history:")
    for message_object in message_history[::-1]:
        logger.info(message_object)
        message = message_object.content[0].text.value
        if message_object.role == "user":
            console.print(f"\n[bold green]User:[/bold green]")
            console.print(f"[bold green]{message}[/bold green]")
        else:
            console.print(f"\n[bold blue]Assistant:[/bold blue]")
            console.print(f"[bold blue]{message}[/bold blue]")


def chat(api):
    assert api.assistant is not None, "No assistant selected"
    assert api.thread is not None, "No thread selected"
    clear_screen()
    console.print(
        f"[bold yellow]Assistant[/bold yellow]: [yellow]{api.assistant.name}[/yellow]"
    )
    console.print(
        f"[bold yellow]Thread[/bold yellow]: [yellow]{api.thread_name}[/yellow]\n"
    )

    log_message_history(api.get_messages().data)
    console.print("\n")
    selected_option = inquirer.list_input(
        "Please select an option",
        choices=[
            "Add message",
            "Send message",
            "Rename thread",
            "Delete thread",
            "Back",
        ],
        carousel=True,
    )

    if selected_option == "Add message":
        message = Prompt.ask("Please enter your message")
        check_attach_file = inquirer.list_input(
            "Would you like to attach a file?",
            choices=["Yes", "No"],
            carousel=True,
        )
        if check_attach_file == "Yes":
            list_of_files = [
                api.client.files.retrieve(file_id).filename
                for file_id in api.assistant.file_ids
            ]
            if list_of_files == []:
                console.print("[yellow]No files available to attach.[/yellow]")
                time.sleep(1)
                chat(api)

            attached_file = inquirer.list_input(
                "Please select a file", choices=list_of_files, carousel=True
            )
            attached_files = [attached_file]
        else:
            attached_files = []
        try:
            api.add_message_to_thread(message, files=attached_files)
        except Exception as e:
            handleError(e, chat, [api])
        chat(api)

    elif selected_option == "Send message":
        try:
            api.send_message()
        except Exception as e:
            handleError(e, chat, [api])

        api.check_run_status()
        chat(api)
    elif selected_option == "Back":
        api.thread_id = None
        threads_dashboard(api)
    elif selected_option == "Rename thread":
        new_name = Prompt.ask("Please enter new thread name", default=api.thread_name)
        try:
            # Rename thread from the json file
            thread_history = thread_history_read()
            thread_history = [
                thread
                if thread["thread"] != api.thread.id
                else {**thread, "thread_name": new_name}
                for thread in thread_history
            ]
            with open(THREAD_HISTORY, "w") as f:
                json.dump(thread_history, f)

        except Exception as e:
            handleError(e, chat, [api])

        api.thread_name = new_name
        chat(api)
    elif selected_option == "Delete thread":
        try:
            # Delete thread from the json file
            thread_history = thread_history_read()
            thread_history = [
                thread for thread in thread_history if thread["thread"] != api.thread.id
            ]
            with open(THREAD_HISTORY, "w") as f:
                json.dump(thread_history, f)
            # Delete thread from OpenAI
            api.client.beta.threads.delete(thread_id=api.thread.id)
        except Exception as e:
            handleError(e, chat, [api])
        console.print(
            f"[bold green]Thread '{api.thread_name}' deleted successfully![/bold green]"
        )
        api.thread = None
        api.thread_name = None
        time.sleep(1)
        threads_dashboard(api)


def app_exit():
    os.system("cls" if os.name == "nt" else "clear")
    rprint(_messages.ascii_goodbye)
    time.sleep(1)
    os.system("cls" if os.name == "nt" else "clear")
    exit()


def select_assistant(api):
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
            return dashboard(api)
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


def assistant_dashboard(api):
    clear_screen()

    console.print(f"[bold green]Assistant[/bold green]: {api.assistant.name}")
    console.print(f"[bold green]Description[/bold green]: {api.assistant.description}")
    console.print(f"[bold green]Model[/bold green]: {api.assistant.model}")
    console.print(
        f"[bold green]Instructions[/bold green]: {api.assistant.instructions}"
    )
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

        try:
            api.edit_assistant(name, description, model, instructions)
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
        dashboard(api)
    elif selected_option == options[4]:
        api.assistant = None
        dashboard(api)


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
            api.client.beta.assistants.update(
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


if __name__ == "__main__":
    # Print welcome message
    rprint(_messages.ascii_welcome)
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
