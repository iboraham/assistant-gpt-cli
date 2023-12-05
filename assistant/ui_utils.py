import logging
import os
import time

from rich.console import Console

from . import ascii_art

console = Console()
logger = logging.getLogger(__name__)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
    console.print(ascii_art.ascii_logo)


def welcome_user(name):
    console.print(f"[bold green]Welcome, {name}![/bold green]")


def app_exit():
    os.system("cls" if os.name == "nt" else "clear")
    console.print(ascii_art.ascii_goodbye)
    time.sleep(1)
    os.system("cls" if os.name == "nt" else "clear")
    exit()
