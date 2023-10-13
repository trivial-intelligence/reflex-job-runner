import asyncio

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
MAX_TASKS_PER_STATE = 2


class State(rx.State):
    results: dict[int, CommandResult] = {}
    _procs: dict[int, asyncio.subprocess.Process] = {}
    _n_tasks: int = 0
    _pending_task_counter: int = -1
    selected_command: int = -1

    @rx.cached_var
    def pending_tasks(self) -> list[int]:
        # sort pending commands in the order they will run
        return sorted(pid for pid in self.results if pid < 0)

    @rx.cached_var
    def results_keys(self) -> list[int]:
        # display commands with valid pids in the order they started
        running_or_completed_commands = reversed(
            [pid for pid in self.results if pid >= 0]
        )
        return [
            *self.pending_tasks,
            *running_or_completed_commands,
        ]

    async def _queue_for_execution(self, command: list[str]) -> CommandResult | None:
        pending_task_id = None
        result = CommandResult(command=command)

        async with self:
            if self._n_tasks >= MAX_TASKS_PER_STATE:
                result.pid = pending_task_id = self._pending_task_counter
                self._pending_task_counter -= 1
                self.results[pending_task_id] = result

        if pending_task_id is not None:
            # wait for task to finish
            while True:
                async with self:
                    if pending_task_id not in self.results:
                        return None
                    if (
                        self._n_tasks < MAX_TASKS_PER_STATE
                        and (not self.pending_tasks or pending_task_id >= max(self.pending_tasks))
                    ):
                        break
                await asyncio.sleep(0.1)
            async with self:
                del self.results[pending_task_id]

        return result

    async def _track_process(self, result: CommandResult):
        proc = await asyncio.create_subprocess_exec(
            *result.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async with self:
            self._procs[proc.pid] = proc
            self.results[proc.pid] = result
            result.pid = proc.pid

        stdout, stderr = await proc.communicate()

        async with self:
            result.stdout = stdout.decode()
            result.stderr = stderr.decode()
            result.returncode = proc.returncode
            self.results[proc.pid] = result
            del self._procs[proc.pid]

    @rx.background
    async def run_command(self):
        async with self:
            if self.selected_command < 0 or self.selected_command >= len(COMMANDS):
                return
            command = COMMANDS[self.selected_command]

        result = await self._queue_for_execution(command)
        if result is None:
            return

        async with self:
            self._n_tasks += 1
        try:
            await self._track_process(result)
        finally:
            async with self:
                self._n_tasks -= 1

    def terminate_command(self, pid: int):
        if pid < 0:
            del self.results[pid]
        else:
            if self._procs.get(pid):
                self._procs[pid].terminate()


def command_selector() -> rx.Component:
    return rx.fragment(
        rx.select(
            rx.option("Select a command", value=-1),
            *[
                rx.option(repr(command), value=i)
                for i, command in enumerate(COMMANDS)
            ],
            value=State.selected_command.to(str),
            on_change=State.set_selected_command,
        ),
        rx.button("Run", on_click=State.run_command),
    )


def command_output(result: CommandResult) -> rx.Component:
    return rx.cond(
        result.returncode != NOT_FINISHED,
        rx.fragment(
            rx.heading(result.command.to_string()),
            rx.text(f"pid={result.pid} returncode={result.returncode}"),
            rx.text(result.stdout),
            rx.text(result.stderr),
        ), 
        rx.fragment(
            rx.spinner(),
            rx.button("Terminate", on_click=State.terminate_command(result.pid)),
        ),
    )


def index() -> rx.Component:
    return rx.vstack(
        command_selector(),
        rx.foreach(
            State.results_keys,
            lambda pid: command_output(State.results[pid]),
        ),
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
app.compile()
