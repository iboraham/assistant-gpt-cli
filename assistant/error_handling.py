from typing import Callable, Any
from .ui_utils import clear_screen, console


def handleError(exception: Exception, recovery_function: Callable, args: list = None):
    """
    Handles exceptions by displaying an error message and then calling a recovery function.

    Args:
        exception (Exception): The exception that occurred.
        recovery_function (Callable): A function to call to recover from the error.
        args (list, optional): A list of arguments to pass to the recovery function. Defaults to None.

    Note:
        The recovery function is intended to be a screen or similar callable that can reset the
        user's context and allow them to continue using the application after an error.
    """
    # Display the error message
    console.print(f"[bold red]Error: {str(exception)}[/bold red]")

    # Wait for user acknowledgment
    input("Press enter to continue...")

    # Clear the screen and call the recovery function
    clear_screen()
    if args is None:
        args = []
    recovery_function(*args)
