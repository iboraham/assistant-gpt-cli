from pyfiglet import Figlet


def generate_ascii_art(text, font="slant"):
    """
    Generates ASCII art for the given text using the specified font.

    Args:
        text (str): The text to be converted into ASCII art.
        font (str, optional): The font style to use. Defaults to "slant".

    Returns:
        str: The ASCII art representation of the input text.
    """
    figlet = Figlet(font=font)
    return figlet.renderText(text)


ascii_logo = generate_ascii_art("Assistant-GPT")
ascii_welcome = generate_ascii_art("Welcome!")
ascii_goodbye = generate_ascii_art("Goodbye!")
