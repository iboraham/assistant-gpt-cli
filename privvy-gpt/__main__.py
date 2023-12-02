import json
import logging
import os
import time
from typing import Callable

import inquirer
import messages
import openai
from _api_wrapper import AssistantAPIWrapper
from halo import Halo
from openai import OpenAI
from rich import print as rprint
from rich.console import Console
from rich.prompt import Prompt

# Constants and Setup
CONFIG_FILE = os.path.expanduser("~/.privvy-gpt.json")
THREAD_HISTORY = os.path.expanduser("~/.privvy-gpt-threads.json")
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
    rprint(messages.ascii_logo)


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
    options = ["Create Assistant", "Select Existent Assistant", "Quit"]
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
    threads_dashboard(api)


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
    list_threads_ids = [thread["thread"] for thread in list_threads]
    choices = ["New Chat", "Back", *list_threads_ids]
    selected_option = inquirer.list_input(
        "Please select an option", choices=choices, carousel=True
    )

    if selected_option == "New Chat":
        clear_screen()
        api.create_thread()
        thread_history_write(
            {
                "assistant": api.assistant.id,
                "thread": api.thread.id,
                "user": api.username,
            }
        )
        chat(api)
    elif selected_option == "Back":
        api.assistant = None
        dashboard(api)
    else:
        thread = api.get_thread(selected_option)
        api.thread = thread
        chat(api)


def log_message_history(message_history):
    console.print("Message history:")
    for message_object in message_history:
        logger.info(message_object)
        message = message_object.content[0].text.value
        if message_object.role == "user":
            console.print(f"[bold green]User:[/bold green]")
            console.print(f"[bold green]{message}[/bold green]")
        else:
            console.print(f"[bold blue]Assistant:[/bold blue]\n")
            console.print(f"[bold blue]{message}[/bold blue]\n")


def chat(api):
    assert api.assistant is not None, "No assistant selected"
    assert api.thread is not None, "No thread selected"
    clear_screen()
    log_message_history(api.get_messages().data)
    selected_option = inquirer.list_input(
        "Please select an option",
        choices=["Send message", "Back", "(Run)"],
        carousel=True,
    )

    if selected_option == "Send message":
        message = Prompt.ask("Please enter your message")
        try:
            api.send_message(message)
        except Exception as e:
            handleError(e, chat, [api])

        api.check_run_status()
        chat(api)
    elif selected_option == "Back":
        api.thread_id = None
        threads_dashboard(api)
    elif selected_option == "(Run)":
        run = api.client.beta.threads.runs.create(
            thread_id=api.thread.id,
            assistant_id=api.assistant.id,
        )
        spinner = Halo(text="Thinking...", spinner="dots")
        spinner.start()
        counter = 0
        while run.status in ["in_progress", "queued"]:
            if counter % 10 == 0:
                run = api.client.beta.threads.runs.retrieve(
                    thread_id=api.thread.id,
                    run_id=run.id,
                )
                logger.info(run)
                time.sleep(5)
            counter += 1

        if run.status == "completed":
            spinner.succeed("Done!")
            chat(api)

        elif run.status == "failed":
            spinner.fail("Failed!")
            handleError(Exception(f"Run failed: run:{run}"), chat, [api])

        else:
            spinner.fail("Error")
            print(run)
            handleError(Exception(f"Run failed: run:{run}"), chat, [api])


def app_exit():
    rprint(messages.ascii_goodbye)
    return


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
        choices=[assistant.name for assistant in assistants],
        carousel=True,
    )
    selected_assistant = [
        assistant for assistant in assistants if assistant.name == selected_assistant
    ][0]
    api.assistant = selected_assistant
    threads_dashboard(api)


if __name__ == "__main__":
    # Print welcome message
    rprint(messages.ascii_welcome)
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
