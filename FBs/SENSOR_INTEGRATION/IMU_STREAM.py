import atexit
import os
import subprocess


class IMU_STREAM:
    """Runs a command-line sampling utility and, optionally, streams its output over MQTT.

    The utility (EXEC_PATH) runs with sudo and is called as
        <EXEC_PATH> [-s SAVE_FILE] [-f FREQ] -t DURATION
    With TARGET_IP, TARGET_PORT, and TOPIC, its standard output goes to mosquitto_pub,
    one MQTT message per line, so the utility must write its samples there (usually
    with SAVE_FILE = /dev/stdout).
    """

    def __init__(self):
        self.process = None
        atexit.register(self._cleanup)

    def _cleanup(self):
        if self.process:
            self._kill_process()

    def _kill_process(self):
        if not self.process:
            return True, "No process running"

        try:
            pgid = os.getpgid(self.process.pid)
        except ProcessLookupError:
            self.process = None
            return True, "Process was not running"

        subprocess.run(f"sudo kill -TERM -{pgid}", shell=True)
        try:
            self.process.wait(timeout=5)
            self.process = None
            return True, "Process stopped (SIGTERM)"
        except subprocess.TimeoutExpired:
            pass

        subprocess.run(f"sudo kill -KILL -{pgid}", shell=True)
        try:
            self.process.wait(timeout=3)
            self.process = None
            return True, "Process stopped (SIGKILL)"
        except subprocess.TimeoutExpired:
            self.process = None
            return False, "Process may still be running after SIGKILL"
        except Exception as e:
            self.process = None
            return False, f"Error during SIGKILL wait: {e}"

    @staticmethod
    def _to_int(value):
        try:
            return int(value) if value else 0
        except ValueError:
            return 0

    def schedule(self, event_name, event_value, exec_path, save_file, duration, freq,
                 target_ip, target_port, topic):
        if event_name == 'INIT':
            return [1, None, None, None, "Initialized"]

        if event_name == 'START':
            if not exec_path:
                return [None, None, 1, None, "Bad configuration: EXEC_PATH is required"]
            if target_ip and target_port and not topic:
                return [None, None, 1, None, "Bad configuration: TOPIC is required to publish over MQTT"]

            duration_s = self._to_int(duration)
            freq_hz = self._to_int(freq)

            cmd = f"sudo {exec_path}"
            if save_file:
                cmd += f" -s {save_file}"
            if freq_hz > 0:
                cmd += f" -f {freq_hz}"
            cmd += f" -t {duration_s if duration_s > 0 else 2147483647}"  # no duration: run until STOP

            if target_ip and target_port and topic:
                # -l: one MQTT message per line; -q 0: keeps up with high sampling rates.
                cmd += f" | mosquitto_pub -h {target_ip} -p {target_port} -t {topic} -l -q 0"

            try:
                self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
            except Exception as e:
                return [None, None, 1, None, f"Process error: {e}"]
            return [None, 1, None, None, f"Started: {cmd}"]

        if event_name == 'STOP':
            success, message = self._kill_process()
            if success:
                return [None, None, None, 1, message]
            return [None, None, 1, None, message]

        return [None, None, None, None, ""]
