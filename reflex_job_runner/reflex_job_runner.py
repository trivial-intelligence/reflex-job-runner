import asyncio
import shlex

import reflex as rx


NOT_FINISHED = -257


class CommandResult(rx.Base):
    """The result of a command."""

    command: list[str] = []
    stdout: str = ""
    stderr: str = ""
    returncode: int = NOT_FINISHED
    pid: int = -1


COMMANDS = [
    ["sh", "-c", "echo 'hello world' && sleep 1 && echo 'goodbye world' >&2"],
    ["uptime"],
    ["ls", "-l"],
    [
        "sh",
        "-c",
        "sleep 5 && echo '5 hello world' && sleep 5 && echo '10 goodbye world' >&2",
    ],
]


class State(rx.State):
    result: CommandResult = CommandResult()
    _proc: asyncio.subprocess.Process = None
    selected_command: int = -1

    @rx.background
    async def run_command(self):
        async with self:
            if self.result.pid > -1 and self.result.returncode == NOT_FINISHED:
                return
            if self.selected_command < 0 or self.selected_command >= len(COMMANDS):
                return
            self.result = CommandResult(command=COMMANDS[self.selected_command], pid=0)
        
        proc = await asyncio.create_subprocess_exec(
            *self.result.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async with self:
            self._proc = proc
            self.result.pid = proc.pid

        stdout, stderr = await proc.communicate()

        async with self:
            self.result.stdout = stdout.decode()
            self.result.stderr = stderr.decode()
            self.result.returncode = proc.returncode
            self._proc = None

    def terminate_command(self):
        if self._proc is not None:
            self._proc.terminate()


PROCESS_HAS_EXITED = State.result.returncode != NOT_FINISHED
PROCESS_NOT_STARTED = State.result.pid < 0


def command_selector() -> rx.Component:
    return rx.fragment(
        rx.select(
            rx.option("Select a command", value=-1),
            *[
                rx.option(shlex.join(command), value=i)
                for i, command in enumerate(COMMANDS)
            ],
            value=State.selected_command.to(str),
            on_change=State.set_selected_command,
        ),
        rx.button("Run", on_click=State.run_command),
    )


def index() -> rx.Component:
    return rx.vstack(
        rx.cond(
            State.is_hydrated & PROCESS_HAS_EXITED | PROCESS_NOT_STARTED,
            command_selector(),
            rx.fragment(
                rx.spinner(),
                rx.button("Terminate", on_click=State.terminate_command),
            ),
        ),
        rx.cond(
            PROCESS_HAS_EXITED,
            rx.fragment(
                rx.heading(State.result.command.to_string()),
                rx.text(f"pid={State.result.pid} returncode={State.result.returncode}"),
                rx.text(State.result.stdout),
                rx.text(State.result.stderr),
            ),
        ),
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
app.compile()
