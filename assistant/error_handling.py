from typing import Callable

from .ui_utils import clear_screen, console


def handleError(e: Exception, screen: Callable, function_args: list = []):
    console.print(f"[bold red]Error: {e}[/bold red]")
    # Press enter to continue
    input("Press enter to continue...")
    clear_screen()
    screen(*function_args)
