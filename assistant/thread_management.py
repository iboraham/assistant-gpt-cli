import json
import os
import time

import inquirer
from PIL import Image
from rich.prompt import Prompt

from .error_handling import handleError
from .ui_utils import clear_screen, console, logger

THREAD_HISTORY = os.path.expanduser("~/.assistant-gpt-threads.json")


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
    from .assistant_operations import assistant_dashboard

    clear_screen()
    list_threads = thread_history_read()
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
        clear_screen()
        assistant_dashboard(api)
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


def log_message_history(message_history, api):
    console.print("Message history:")
    for message_object in message_history[::-1]:
        logger.info(message_object)
        for message_content in message_object.content:
            if message_content.type == "text":
                if message_object.role == "user":
                    console.print(f"\n[bold green]User:[/bold green]")
                    console.print(
                        f"[italic green]{message_content.text.value}[/italic green]"
                    )
                    if message_object.file_ids != []:
                        filenames = [
                            api.client.files.retrieve(file_id).filename
                            for file_id in message_object.file_ids
                        ]
                        console.print(
                            f"([bold green]Files attached:[/bold green] {', '.join(filenames)})"
                        )
                else:
                    console.print(f"\n[bold blue]Assistant:[/bold blue]")
                    console.print(
                        f"[italic blue]{message_content.text.value}[/italic blue]"
                    )
            elif message_content.type == "image_file":
                console.print(f"\n[bold blue]Assistant:[/bold blue]")
                console.print(
                    f"[italic blue]Image file: {message_content.image_file.file_id}.png[/italic blue]"
                )
                file_content = api.client.files.with_raw_response.retrieve_content(
                    file_id=message_content.image_file.file_id
                ).content
                # Convert file content to bytes from string
                open(f"{message_content.image_file.file_id}.png", "wb").write(
                    file_content
                )

                # Open image
                image = Image.open(f"{message_content.image_file.file_id}.png")
                image.show()


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

    log_message_history(api.get_messages().data, api)
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
            # Convert filename to file_id
            attached_files = [
                file_id
                for file_id in api.assistant.file_ids
                if api.client.files.retrieve(file_id).filename == attached_file
            ]
            console.print(
                f"[bold green]File '{attached_file}' attached successfully![/bold green]"
            )
        else:
            attached_files = []
        try:
            api.add_message_to_thread(message, files=attached_files)
            console.print(
                f"[bold green]Message '{message}' added successfully![/bold green]"
            )
            time.sleep(1)
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
