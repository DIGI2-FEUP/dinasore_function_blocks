# Sensor integration

## IMU_STREAM

Runs a command-line sampling utility and, optionally, streams its output over MQTT, one message per line. It is meant for sampling rates that a Python block cannot sustain, using a utility written in a compiled language.

The utility runs with `sudo` and is called as:

```
sudo <EXEC_PATH> [-s SAVE_FILE] [-f FREQ] -t DURATION
```

| Event | Effect |
|---|---|
| `INIT` -> `INIT_O` | Initializes the block |
| `START` -> `STARTED` or `START_FAILED` | Launches the utility |
| `STOP` -> `STOPPED`, or `START_FAILED` if it cannot be stopped | Stops the utility and the stream |

| Input | Meaning | Example |
|---|---|---|
| `EXEC_PATH` | Utility, relative to the folder from which DINASORE runs, or absolute | `./adxl345spi` |
| `SAVE_FILE` | Output file. To stream, use the standard output | `/dev/stdout` |
| `FREQ` | Sampling rate in Hz. Omitted if empty | `3200` |
| `DURATION` | Duration in seconds. Empty or negative: runs until `STOP` | `-1` |
| `TARGET_IP`, `TARGET_PORT`, `TOPIC` | Broker and topic. Empty: no stream | `192.168.1.20`, `1883`, `ACCEL` |

`STATUS` (output) has the command that was launched, or the error.

### Usage

1. Copy the `.py` and `.fbt` files to `dinasore/resources/function_blocks/`.
2. Build your utility. [adxl345spi](https://github.com/nagimov/adxl345spi) has this command line; a version for long recordings and a utility for the MPU9250 are in [iiot-autonomous-maintenance](https://github.com/pedrodsmota/iiot-autonomous-maintenance/tree/main/acquisition).
3. To stream, install `mosquitto-clients`.
4. The user that runs DINASORE needs `sudo` without a password, as on Raspberry Pi OS by default.
5. Fire `START`.

With a quality of service of 0, messages are not confirmed, which keeps up with high rates but does not guarantee delivery.
