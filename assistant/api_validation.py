import time

import openai
from halo import Halo
from openai import OpenAI

from .ui_utils import logger


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
