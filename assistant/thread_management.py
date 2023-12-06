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
    """
    Reads the thread history from a JSON file.

    Returns:
        list: A list of thread history records.
    """
    if os.path.exists(THREAD_HISTORY):
        with open(THREAD_HISTORY, "r") as file:
            return json.load(file)
    return []


def thread_history_write(new_thread):
    """
    Writes a new thread record to the thread history JSON file.

    Args:
        new_thread (dict): The new thread record to be added.
    """
    thread_history = thread_history_read()
    thread_history.append(new_thread)
    with open(THREAD_HISTORY, "w") as file:
        json.dump(thread_history, file)


def threads_dashboard(api):
    """
    Displays the threads dashboard, allowing the user to manage chat threads.

    Args:
        api: API object to interact with the backend.
    """
    from .assistant_operations import assistant_dashboard

    clear_screen()
    manage_thread_options(api)


def manage_thread_options(api):
    """
    Manages the options in the thread dashboard.

    Args:
        api: API object to interact with the backend.
    """
    from .assistant_operations import assistant_dashboard

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
        handle_new_chat(api)
    elif selected_option == "Back":
        clear_screen()
        assistant_dashboard(api)
    else:
        handle_existing_chat(api, list_threads, selected_option)


def handle_new_chat(api):
    """
    Handles the creation of a new chat thread.

    Args:
        api: API object to interact with the backend.
    """
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


def handle_existing_chat(api, list_threads, selected_option):
    """
    Handles interaction with an existing chat thread.

    Args:
        api: API object to interact with the backend.
        list_threads: List of existing threads.
        selected_option: The selected thread name.
    """
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
    """
    Logs the message history of a chat thread.

    Args:
        message_history: The history of messages in the thread.
        api: API object to interact with the backend.
    """
    console.print("Message history:")
    for message_object in message_history[::-1]:
        logger.info(message_object)
        display_message_content(message_object, api)


def chat(api):
    """
    Manages the chat interface for the selected thread.

    Args:
        api: API object to interact with the backend.
    """
    assert api.assistant is not None, "No assistant selected"
    assert api.thread is not None, "No thread selected"

    clear_screen()
    display_chat_header(api)
    log_message_history(api.get_messages().data, api)

    handle_chat_options(api)


def display_chat_header(api):
    """
    Displays the header information for the chat interface.

    Args:
        api: API object to interact with the backend.
    """
    console.print(
        f"[bold yellow]Assistant[/bold yellow]: [yellow]{api.assistant.name}[/yellow]"
    )
    console.print(
        f"[bold yellow]Thread[/bold yellow]: [yellow]{api.thread_name}[/yellow]\n"
    )


def handle_chat_options(api):
    """
    Presents and handles the different chat options like adding messages, sending messages, etc.

    Args:
        api: API object to interact with the backend.
    """
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
        handle_add_message(api)
    elif selected_option == "Send message":
        handle_send_message(api)
    elif selected_option == "Rename thread":
        handle_rename_thread(api)
    elif selected_option == "Delete thread":
        handle_delete_thread(api)
    elif selected_option == "Back":
        api.thread_id = None
        threads_dashboard(api)


def display_message_content(message_object, api):
    """
    Displays the content of a message in the chat.

    Args:
        message_object: The message object to be displayed.
        api: API object to interact with the backend.
    """
    # Display message based on its type
    if message_object.role == "user":
        display_user_message(message_object, api)
    else:
        display_assistant_message(message_object, api)


def display_user_message(message_object, api):
    """
    Displays a message sent by the user.

    Args:
        message_object: The message object to be displayed.
        api: API object to interact with the backend.
    """
    console.print(f"\n[bold green]User:[/bold green]")
    for message_content in message_object.content:
        if message_content.type == "text":
            console.print(f"[italic green]{message_content.text.value}[/italic green]")
            display_attached_files(message_object, api)


def display_assistant_message(message_object, api):
    """
    Displays a message sent by the assistant.

    Args:
        message_object: The message object to be displayed.
        api: API object to interact with the backend.
    """
    console.print(f"\n[bold blue]Assistant:[/bold blue]")
    for message_content in message_object.content:
        if message_content.type == "text":
            console.print(f"[italic blue]{message_content.text.value}[/italic blue]")
        elif message_content.type == "image_file":
            display_image_file(message_content, api)


def handle_add_message(api):
    """
    Handles adding a new message to the chat thread.

    Args:
        api: API object to interact with the backend.
    """
    message = Prompt.ask("Please enter your message")
    attached_files = handle_file_attachment(api)

    try:
        api.add_message_to_thread(message, files=attached_files)
        console.print(
            f"[bold green]Message '{message}' added successfully![/bold green]"
        )
    except Exception as e:
        handleError(e, chat, [api])
    finally:
        time.sleep(1)
        chat(api)


def handle_file_attachment(api):
    """
    Handles the attachment of files to a message.

    Args:
        api: API object to interact with the backend.

    Returns:
        List: A list of attached file IDs.
    """
    check_attach_file = inquirer.list_input(
        "Would you like to attach a file?",
        choices=["Yes", "No"],
        carousel=True,
    )
    if check_attach_file == "Yes":
        return select_file_to_attach(api)
    return []


def select_file_to_attach(api):
    """
    Allows the user to select a file to attach.

    Args:
        api: API object to interact with the backend.

    Returns:
        List: A list containing the selected file ID.
    """
    list_of_files = [
        api.client.files.retrieve(file_id).filename
        for file_id in api.assistant.file_ids
    ]
    if not list_of_files:
        console.print("[yellow]No files available to attach.[/yellow]")
        time.sleep(1)
        return []

    attached_file = inquirer.list_input(
        "Please select a file", choices=list_of_files, carousel=True
    )
    return [
        file_id
        for file_id in api.assistant.file_ids
        if api.client.files.retrieve(file_id).filename == attached_file
    ]


def handle_send_message(api):
    """
    Handles sending the composed message in the chat thread.

    Args:
        api: API object to interact with the backend.
    """
    try:
        api.send_message()
        api.check_run_status()
    except Exception as e:
        handleError(e, chat, [api])
    finally:
        chat(api)


def handle_rename_thread(api):
    """
    Handles renaming the current chat thread.

    Args:
        api: API object to interact with the backend.
    """
    new_name = Prompt.ask("Please enter new thread name", default=api.thread_name)
    try:
        update_thread_history(api.thread.id, new_name)
        api.thread_name = new_name
    except Exception as e:
        handleError(e, chat, [api])
    finally:
        chat(api)


def update_thread_history(thread_id, new_name):
    """
    Updates the thread name in the thread history.

    Args:
        thread_id (str): The ID of the thread to be updated.
        new_name (str): The new name for the thread.
    """
    thread_history = thread_history_read()
    thread_history = [
        thread if thread["thread"] != thread_id else {**thread, "thread_name": new_name}
        for thread in thread_history
    ]
    with open(THREAD_HISTORY, "w") as file:
        json.dump(thread_history, file)


def handle_delete_thread(api):
    """
    Handles the deletion of the current chat thread.

    Args:
        api: API object to interact with the backend.
    """
    try:
        delete_thread_from_history(api.thread.id)
        api.client.beta.threads.delete(thread_id=api.thread.id)
        api.thread = None
        api.thread_name = None
        console.print(
            f"[bold green]Thread '{api.thread_name}' deleted successfully![/bold green]"
        )
    except Exception as e:
        handleError(e, chat, [api])
    finally:
        time.sleep(1)
        threads_dashboard(api)


def delete_thread_from_history(thread_id):
    """
    Deletes a thread from the thread history.

    Args:
        thread_id (str): The ID of the thread to be deleted.
    """
    thread_history = thread_history_read()
    thread_history = [
        thread for thread in thread_history if thread["thread"] != thread_id
    ]
    with open(THREAD_HISTORY, "w") as file:
        json.dump(thread_history, file)


def display_attached_files(message_object, api):
    """
    Displays the list of files attached to a message.

    Args:
        message_object: The message object containing the files.
        api: API object to interact with the backend.
    """
    if message_object.file_ids:
        filenames = [
            api.client.files.retrieve(file_id).filename
            for file_id in message_object.file_ids
        ]
        console.print(
            f"([bold green]Files attached:[/bold green] {', '.join(filenames)})"
        )


def display_image_file(message_content, api):
    """
    Displays an image file attached to a message.

    Args:
        message_content: The content of the message containing the image file.
        api: API object to interact with the backend.
    """
    if message_content.type == "image_file":
        console.print(f"\n[bold blue]Assistant:[/bold blue]")
        console.print(
            f"[italic blue]Image file: {message_content.image_file.file_id}.png[/italic blue]"
        )
        download_and_show_image(message_content.image_file.file_id, api)


def download_and_show_image(file_id, api):
    """
    Downloads and shows an image file.

    Args:
        file_id (str): The ID of the file to download.
        api: API object to interact with the backend.
    """
    try:
        file_content = api.client.files.with_raw_response.retrieve_content(
            file_id=file_id
        ).content
        file_path = f"{file_id}.png"
        save_image_file(file_content, file_path)
        open_image(file_path)
    except Exception as e:
        handleError(e, "Error handling image file")


def save_image_file(file_content, file_path):
    """
    Saves the image file to the local filesystem.

    Args:
        file_content: The content of the image file.
        file_path (str): The path where the image will be saved.
    """
    with open(file_path, "wb") as file:
        file.write(file_content)


def open_image(file_path):
    """
    Opens and displays an image file.

    Args:
        file_path (str): The path of the image file to open.
    """
    try:
        image = Image.open(file_path)
        image.show()
    except IOError as e:
        print(f"Unable to open image: {e}")
