import time

from halo import Halo
from openai import OpenAI


class AssistantAPIWrapper:
    def __init__(self, api_key, username, assistant_id=None):
        self.client = OpenAI(api_key=api_key)
        self.thread = None
        self.assistant = None
        self.run = None
        self.username = username

    def create_assistant(
        self, name, description=None, model="gpt-4-vision-preview", instructions=None
    ):
        self.assistant = self.client.beta.assistants.create(
            name=name,
            description=description,
            model=model,
            instructions=instructions,
        )

    def edit_assistant(
        self,
        name,
        description=None,
        model="gpt-4-vision-preview",
        instructions=None,
    ):
        self.assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant.id,
            name=name,
            description=description,
            model=model,
            instructions=instructions,
        )

    def list_assistants(self):
        return self.client.beta.assistants.list()

    def get_thread(self, thread_id):
        return self.client.beta.threads.retrieve(thread_id=thread_id)

    def create_thread(self):
        self.thread = self.client.beta.threads.create()

    def send_message(self, message):
        # Send a message to the Assistant
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=message,
        )

        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )

    def get_messages(self):
        # Get the messages from the Assistant
        return self.client.beta.threads.messages.list(thread_id=self.thread.id)

    def check_run_status(self):
        # Check the status of the Assistant
        run = self.client.beta.threads.runs.retrieve(
            thread_id=self.thread.id,
            run_id=self.run.id,
        )
        spinner = Halo(text="Thinking...", spinner="dots")
        spinner.start()
        while run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=self.run.id,
            )
            time.sleep(3)

        if run.status == "completed":
            spinner.stop()
        else:
            spinner.fail("Error")
            raise Exception("Error: ", run)
