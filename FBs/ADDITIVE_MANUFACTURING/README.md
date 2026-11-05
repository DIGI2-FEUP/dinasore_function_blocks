# Additive manufacturing

Function blocks that control a 3D printer through the REST API of [OctoPrint](https://octoprint.org/): they queue print requests, start the print, and monitor it.

| Function block | What it does |
|---|---|
| `PRINT_QUEUE` | FIFO queue of requests, for a printer shared by several clients |
| `PRINT_START` | Selects a file stored in OctoPrint and starts printing it |
| `PRINT_CHECK` | Reads the state and progress of the print job |

```
 request (e.g. READ_MQTT.RUN_O) ----> REQUEST [PRINT_QUEUE] START_PRINT ----> START_PRINT [PRINT_START]
                                       CHECK ^     ^ START_FAILED <---------------- START_FAILED
                                             |
                  READ [PRINT_CHECK] READ_O -+     PRINT_CHECK.JOB_STATE ----> PRINT_QUEUE.JOB_STATE
                    ^                  |           PRINT_QUEUE.FILE_PATH ----> PRINT_START.FILE_PATH
                    +------------------+
```

`PRINT_START` can also be used on its own, with `FILE_PATH` as a fixed parameter.

## Setup

1. Copy the `.py` and `.fbt` files to `dinasore/resources/function_blocks/`.
2. Install the dependencies in the environment of DINASORE: `pip install requests python-dotenv`.
3. Generate an API key in OctoPrint (User Settings > Application Keys) and give it to the blocks, in one of two ways:
   - as an environment variable, before starting DINASORE: `export API_KEY=<key>`;
   - in a file `resources/function_blocks/.env` with the line `API_KEY=<key>`.

   Never put the key in a parameter of the application, which is stored in the `.sys` file.
4. Upload the sliced G-code file to OctoPrint.

## PRINT_QUEUE

| Event | Effect |
|---|---|
| `INIT` -> `INIT_O` | Initializes the block |
| `REQUEST` -> `START_PRINT` or `QUEUED` | Adds `REQUEST_FILE`. If the printer is available, it starts right away; otherwise, it waits |
| `CHECK` -> `START_PRINT` | Updates the state of the printer with `JOB_STATE`. If it is available, it sends the next request |
| `START_FAILED` -> `DROPPED` | Retries the job on the next `CHECK`; drops it after 3 attempts |

The state of the printer is unknown until the first `CHECK`, so a request received before it waits in the queue. After `START_PRINT`, the next request waits until the printer has gone busy and become available again, or until `START_TIMEOUT` expires (seconds, 30 by default).

| Output | Meaning |
|---|---|
| `FILE_PATH` | File to print |
| `QUEUE_SIZE` | Requests waiting |
| `STATUS` | Text with the state |

## PRINT_START

| Event | Effect |
|---|---|
| `INIT` -> `INIT_O` | Initializes the block |
| `START_PRINT` -> `STARTED` or `START_FAILED` | Requests the print |

| Data | Meaning | Example |
|---|---|---|
| `OCTO_URL` (input) | Address of OctoPrint | `http://localhost` |
| `LOCATION` (input) | Where the file is stored in OctoPrint | `local` |
| `FILE_PATH` (input) | File to print | `part.gcode` |
| `REQUEST_TIMEOUT` (input) | Timeout in seconds; 10 by default | |
| `STATUS`, `START_REPLY` (outputs) | Result, and reply of OctoPrint | |

## PRINT_CHECK

Each `READ` waits one second, to limit the rate of requests, and always fires `READ_O`. Connect `READ_O` to `READ` to poll in a loop.

| Output event | Fires when |
|---|---|
| `PROGRESS_UPDATE` | A job is in progress |
| `PRINT_DONE` | The job has reached 99.9%, or the printer is idle. It fires on every `READ` in these states, so use it as a state and not as a single event |
| `PRINT_ERROR` | The request fails, or OctoPrint reports an error |

| Data | Meaning |
|---|---|
| `OCTO_URL`, `REQUEST_TIMEOUT` (inputs) | As in `PRINT_START`; the timeout is 5 s by default |
| `JOB_STATE` (output) | State reported by OctoPrint, e.g. `Operational`, `Printing` |
| `COMPLETION` (output) | Progress in percent; -1 if unknown |
| `JOB_INFO` (output) | Full reply, or the error message |
