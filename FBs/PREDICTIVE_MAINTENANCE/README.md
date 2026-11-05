# Predictive maintenance

Function blocks that estimate the health of a component on an edge device and decide when to act.

| Function block | What it does |
|---|---|
| `RUL_ESTIMATION` | Runs an online estimation script in its own virtual environment and exposes the Health Index (HI) and the Remaining Useful Life (RUL) |
| `RUL_THRESHOLD` | Fires an event, once, when the RUL falls below a threshold |

```
                          +--------------------------+
                          |                          |
                          v                          |
                POLL [RUL_ESTIMATION] DATA ----------+
                          | RUL      DATA
                          v           |
              VALUE [RUL_THRESHOLD] RUN
                          |
                        PRINT ----> e.g. WRITE_MQTT.RUN (order to the printer)
```

A complete system that uses these blocks, including online scripts for three vibration sensors and trained models, is in [iiot-autonomous-maintenance](https://github.com/pedrodsmota/iiot-autonomous-maintenance).

## RUL_ESTIMATION

DINASORE runs on older Python versions than those required by recent machine learning libraries. This block keeps the model out of the runtime: it launches a script in a separate virtual environment and reads the estimates from a file that the script rewrites.

### Interface

| Event | Effect |
|---|---|
| `INIT` -> `INIT_O` | Initializes the block |
| `START` -> `STARTED` or `START_FAILED` | Launches the script |
| `POLL` -> `DATA` | Reads the latest estimate, at most every 0.5 s |
| `STOP` -> `STOPPED` | Stops the script and closes the log |

| Input | Meaning | Example |
|---|---|---|
| `ENV_PATH` | Virtual environment, absolute or relative to the DINASORE folder | `myenv` |
| `SCRIPT_PATH` | Script, absolute or relative to `resources/function_blocks` | `online_rul_adxl.py` |
| `PORT` | A number: MQTT port of the local broker, with the stream sent to the script's standard input. Otherwise: passed to the script as `--port` | `1883` or `/dev/ttyACM0` |
| `TOPIC` | MQTT topic of the stream. Required if `PORT` is a number | `ARM1` |
| `MODE` | Passed as `--mode` in the MQTT case. Optional | `stdin` |
| `MODEL_PATH`, `SCALER_PATH` | Passed as `--model` and `--scaler`, absolute or relative to `resources/function_blocks`. Optional | `model_adxl.pt` |

| Output | Meaning |
|---|---|
| `HI` | Latest Health Index (starts at 1.0) |
| `RUL` | Latest RUL in hours; -1 while there is no estimate |
| `STATUS` | Text with the state; it flags `STALE` after 10 s without a new estimate |

### What the script must implement

It is called with `--rul-file FILE --quiet`, plus `--dump-features FILE` and the optional arguments above. After each estimate, it must atomically replace `FILE` (write a temporary file, then `os.replace`) with three lines:

```
0.734512      <- Health Index
OK            <- status text
21874.3       <- RUL in seconds, -1 if unknown
```

If it is given `--dump-features FILE`, it should write the features of each window to that file.

### Usage

1. Copy the `.py` and `.fbt` files to `dinasore/resources/function_blocks/`, with your script, model, and scaler.
2. In the DINASORE folder, create the virtual environment and install what the script needs: `python3 -m venv myenv`.
3. For the MQTT case, install the tools used in the command: `sudo apt install mosquitto mosquitto-clients pv`.
4. Connect `DATA` to `POLL`, and `STARTED` to `POLL` to start the loop, or fire `POLL` once from the 4diac IDE.
5. Fire `START`.

Estimates are logged to `resources/logs/rul_log_<port>_<date>.csv`.

## RUL_THRESHOLD

Fires `PRINT` once when `VALUE` falls below `THRESHOLD`. It re-arms only when `VALUE` rises above `THRESHOLD` + 0.5 h, for example after the part has been replaced, so that fluctuations around the threshold do not issue repeated orders. Negative values mean "no estimate yet" and are ignored.

| Event | Effect |
|---|---|
| `INIT` -> `INIT_O` | Arms the block |
| `RUN` -> `RUN_O`, and `PRINT` if the order is issued | Compares `VALUE` with `THRESHOLD` |

| Data | Meaning |
|---|---|
| `VALUE` (input) | Estimated RUL in hours; connect it to `RUL_ESTIMATION.RUL` |
| `THRESHOLD` (input) | Threshold in hours: the time needed to act plus a safety margin |
| `STATUS` (output) | Text with the state |
