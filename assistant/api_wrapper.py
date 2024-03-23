import time

from halo import Halo
from openai import AssistantEventHandler, OpenAI
from typing_extensions import override

from .ui_utils import clear_screen, console


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        clear_screen()
        console.print(
            f"\n[bold blue]Assistant:[/bold blue]\n",
            end="",
        )

    @override
    def on_text_delta(self, delta, snapshot):
        console.print(
            f"[italic blue]{delta.value}[/italic blue]",
            end="",
        )

    def on_tool_call_created(self, tool_call):
        console.print(
            f"\n[bold blue]Assistant:[/bold blue] {tool_call.type}\n",
        )

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                console.print(
                    delta.code_interpreter.input,
                    end="",
                )
            if delta.code_interpreter.outputs:
                console.print(
                    f"\n\noutput >",
                )
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        console.print(
                            f"\n{output.logs}",
                        )


class AssistantAPIWrapper:
    """
    A wrapper class for the OpenAI API, managing the assistant, threads, and messages.
    """

    def __init__(self, api_key, username, assistant_id=None):
        """
        Initializes the API client and sets up basic parameters.
        """
        self.client = OpenAI(api_key=api_key)
        self.thread = None
        self.assistant = None
        self.run = None
        self.username = username

    def create_assistant(
        self,
        name,
        description=None,
        model="gpt-4-vision-preview",
        instructions=None,
        tools=None,
    ):
        """
        Creates a new assistant with the specified parameters.
        """
        if tools is None:
            tools = []
        self.assistant = self.client.beta.assistants.create(
            name=name,
            description=description,
            model=model,
            instructions=instructions,
            tools=tools,
        )

    def edit_assistant(
        self,
        name,
        description=None,
        model="gpt-4-vision-preview",
        instructions=None,
        tools=None,
    ):
        """
        Edits the existing assistant with new parameters.
        """
        if tools is None:
            tools = []
        self.assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant.id,
            name=name,
            description=description,
            model=model,
            instructions=instructions,
            tools=tools,
        )

    def list_assistants(self):
        """
        Retrieves a list of all assistants.
        """
        return self.client.beta.assistants.list()

    def get_assistants(self, assistant_id):
        """
        Retrieves a assistants.
        """
        return self.client.beta.assistants.retrieve(assistant_id=assistant_id)

    def get_thread(self, thread_id):
        """
        Retrieves a specific thread by its ID.
        """
        return self.client.beta.threads.retrieve(thread_id=thread_id)

    def create_thread(self):
        """
        Creates a new thread and stores it in the instance variable.
        """
        self.thread = self.client.beta.threads.create()

    def add_message_to_thread(self, message, role="user", files=[]):
        """
        Adds a message to the current thread.
        """
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=message,
            file_ids=files,
        )

    def send_message(self):
        """
        Sends a message via the assistant in the current thread.
        """
        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )

    def send_message_and_stream(self):
        """
        Sends a message via the assistant in the current thread and streams the response.
        """
        with self.client.beta.threads.runs.create_and_stream(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()

    def get_messages(self):
        """
        Retrieves all messages from the current thread.
        """
        return self.client.beta.threads.messages.list(thread_id=self.thread.id)

    def _check_run_status(self):
        """
        !Depreciated: Use send_message_and_stream instead.

        Checks and waits for the run status to complete, with a spinner for user feedback.
        """
        run = self.client.beta.threads.runs.retrieve(
            thread_id=self.thread.id,
            run_id=self.run.id,
        )
        spinner = Halo(text="Thinking...", spinner="dots")
        spinner.start()

        counter = 0
        while run.status in ["in_progress", "queued"]:
            if counter % 10 == 0:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id,
                )
                time.sleep(5)
            counter += 1

        if run.status == "completed":
            spinner.succeed("Done")
        else:
            spinner.fail("Error")
            raise Exception(f"Run failed: {run}")
