import asyncio

import reflex as rx


NOT_FINISHED = -257

class CommandResult(rx.Base):
    """The result of a command."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = NOT_FINISHED
    pid: int = -1


COMMAND = ["sh", "-c", "echo 'hello world' && sleep 1 && echo 'goodbye world' >&2"]


class State(rx.State):
    result: CommandResult = CommandResult()
    _proc: asyncio.subprocess.Process = None

    @rx.background
    async def run_command(self):
        async with self:
            if self.result.pid > -1 and self.result.returncode == NOT_FINISHED:
                return
            self.result = CommandResult(pid=0)
        
        proc = await asyncio.create_subprocess_exec(
            *COMMAND,
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


def index() -> rx.Component:
    return rx.vstack(
        rx.cond(
            State.is_hydrated & PROCESS_HAS_EXITED | PROCESS_NOT_STARTED,
            rx.button("Run", on_click=State.run_command),
            rx.fragment(
                rx.spinner(),
                rx.button("Terminate", on_click=State.terminate_command),
            ),
        ),
        rx.cond(
            PROCESS_HAS_EXITED,
            rx.fragment(
                rx.heading(f"pid={State.result.pid} returncode={State.result.returncode}"),
                rx.text(State.result.stdout),
                rx.text(State.result.stderr),
            ),
        ),
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
app.compile()
