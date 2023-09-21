# `reflex-job-runner` Part 1

In this video, I will cover

* Creation of a new reflex project
* UI for starting and displaying the result of subprocess
* Background task event handler for tracking execution of hard-coded subprocess
* Terminating a running process

# Creation of a new Reflex project

* Create a python3.11 virtualenv and activate it
* Change to `reflex-job-runner` directory
* Create `requirements.txt` and `pip install -r requirements.txt`
* Execute `reflex init` to create template app

# UI for starting and displaying the result of subprocess

* Create custom var for storing the result of a subprocess
  * `stdout`, `stderr`, `returncode`
  * `pid`
* Create a special `NOT_FINISHED` constant that will never be a real returncode as default returncode
* Add `result` var and dummy `run_command` event handler to `State`
* Define conditional helpers
  * `PROCESS_HAS_EXITED = State.result.returncode != NOT_FINISHED`
  * `PROCESS_NOT_STARTED = State.result.pid < 0`
* Remove content from default `index` component.
* Conditionally render start button when
  * `State.is_hydrated`: "state has latest values"
  * AND `PROCESS_HAS_EXITED`
  * OR `PROFCESS_NOT_STARTED`
  * otherwise render a loading spinner
* Conditionally render output when `PROCESS_HAS_EXITED`

# Background task event handler

* import asyncio
* Create `COMMAND` constant at top level
* Create `_proc` backend var to store the running process
* Create `run_command` background task
  * Inside `async with self` context
    * If `result` already has a positive pid and returncode is NOT_FINISHED, `return` early
    * Reset `result` and set `pid = 0` to save our place
  * Create a new subprocess
  * Inside `async with self` context, assign `pid` and `_proc`.
  * Wait for `_proc` to exit and collect `stdout` and `stderr`
  * Inside `async with self` context, update `result` and clear `_proc`

# Terminating a running process

* Create `terminate_command` event handler
* Call `_proc.terminate` if proc is set
* Add a new "Terminate" button to the UI linked to event handler