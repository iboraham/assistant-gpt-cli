import logging
import os
import time

from rich.console import Console
from . import ascii_art

console = Console()
logger = logging.getLogger(__name__)


def clear_screen():
    """
    Clears the terminal screen and displays the ASCII logo.
    """
    _clear_terminal()
    console.print(ascii_art.ascii_logo)


def welcome_user(name):
    """
    Displays a welcome message to the user.

    Args:
        name (str): The name of the user.
    """
    console.print(f"[bold green]Welcome, {name}![/bold green]")


def app_exit():
    """
    Clears the terminal screen, displays a goodbye message, and exits the application.
    """
    _clear_terminal()
    console.print(ascii_art.ascii_goodbye)
    time.sleep(1)
    _clear_terminal()
    exit()


def _clear_terminal():
    """
    Clears the terminal screen based on the operating system.
    """
    os.system("cls" if os.name == "nt" else "clear")
