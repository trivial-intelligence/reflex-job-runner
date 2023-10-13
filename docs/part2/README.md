# `reflex-job-runner` Part 2

In this video, I will cover

* Selection drop down of hardcoded commands to run
  * Create COMMANDS global with additional sample commands
  * Create selected command state var
  * Extraction of the select_command component with run button
  * Update CommandResult to store the command to run
  * Update run_command to use the command in the result
* Track multiple concurrent processes on the backend
  * change `result` and `_proc` into dicts keyed on the process ID
  * Add `_n_tasks` and `_pending_task_counter` backend state vars
  * Add `MAX_TASKS_PER_STATE` constant
  * Add `pending_tasks` cached var to get queued pending_task_id
  * Implement queueing logic in helper function that returns a `CommandResult`
  * Extract process execution into helper function `_track_process` that accepts a `CommandResult` as an argument
  * Update `terminate_command` to remove queued commands or terminate running commands
* Why tracking _proc in state is a bad idea: redis and future plans
* Render multiple concurrent processes on the frontend
  * Create `results_keys` cached var to return sorted list of results for rendering
  * Extraction of the command_output component