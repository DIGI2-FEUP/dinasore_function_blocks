import atexit
import csv
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime


class RUL_ESTIMATION:
    """Runs an online health estimation script and exposes its HI and RUL to the application.

    The script runs as a background process, in its own Python virtual environment, so
    that the model can use libraries that need a newer Python than DINASORE. After each
    estimate, it atomically rewrites a file with the Health Index (HI), a status, and the
    RUL in seconds. POLL reads this file and fires DATA, with the RUL in hours. Connect
    DATA back to POLL to read it in a loop.

    RUL = -1 while there is no estimate yet, or if the script cannot compute one. While
    there is no estimate, or if a read fails, DATA still fires with the last valid values,
    so that the DATA -> POLL loop does not stop.

    Every new estimate is logged to resources/logs/rul_log_<port>_<date>.csv, and the
    script is asked to write the features of every window to features_<port>_<date>.csv.
    See the README of this folder for what the script must implement.
    """

    FSYNC_EVERY_N_ROWS = 10   # limits the rows lost if the power fails during a long run
    STALE_AFTER_S = 10.0      # flags the script as silent after this time without a new estimate
    POLL_INTERVAL_S = 0.5     # minimum interval between reads of the file

    def __init__(self):
        self.process = None
        self.rul_file = None
        self._pgid = None     # captured at launch: the shell may exit before the pipeline

        self.log_fh = None
        self._csv_writer = None
        self._log_lock = threading.Lock()
        self._session_start = None
        self._last_mtime = None
        self._last_update_wall = None
        self._rows_since_fsync = 0
        self._was_stale = False
        self._last_poll = 0.0
        self._last_hi = 1.0
        self._last_rul_h = -1.0
        self._features_path = None

        # signal.signal() only works in the main thread, and this block runs in a worker thread.
        atexit.register(self._cleanup)

    def _kill_group(self, sig=signal.SIGTERM):
        if self._pgid is None:
            return
        try:
            os.killpg(self._pgid, sig)
        except ProcessLookupError:
            pass

    def _close_log(self):
        with self._log_lock:
            if self.log_fh is not None:
                try:
                    self.log_fh.flush()
                    os.fsync(self.log_fh.fileno())
                except OSError:
                    pass
                try:
                    self.log_fh.close()
                except OSError:
                    pass
            self.log_fh = None
            self._csv_writer = None
            self._rows_since_fsync = 0

    def _log_row(self, hi, rul_s, status):
        """Append one row to the log. A logging failure must never stop the estimates."""
        if self.log_fh is None:
            return
        now = time.time()
        try:
            with self._log_lock:
                self._csv_writer.writerow([
                    datetime.fromtimestamp(now).isoformat(timespec="milliseconds"),
                    f"{now:.3f}",
                    f"{(now - self._session_start):.3f}" if self._session_start else "",
                    f"{hi:.6f}" if hi is not None else "",
                    f"{rul_s:.1f}" if rul_s is not None else "",
                    status,
                ])
                self.log_fh.flush()
                self._rows_since_fsync += 1
                if self._rows_since_fsync >= self.FSYNC_EVERY_N_ROWS:
                    os.fsync(self.log_fh.fileno())
                    self._rows_since_fsync = 0
        except OSError:
            pass

    def _cleanup(self):
        """Stop the script (SIGTERM, then SIGKILL after about 2 s) and close the log."""
        if self._pgid is None and self.log_fh is None:
            return
        self._kill_group(signal.SIGTERM)
        if self.process is not None:
            for _ in range(20):
                try:
                    pid, _ = os.waitpid(self.process.pid, os.WNOHANG)
                    if pid != 0:
                        break
                except ChildProcessError:
                    break
                time.sleep(0.1)
            else:
                self._kill_group(signal.SIGKILL)

        self._pgid = None
        self.process = None
        self.rul_file = None
        self._close_log()

    def _open_log(self, log_dir, safe_port):
        """Returns a note for STATUS. The log is not kept in /tmp, which is lost on a reboot."""
        try:
            os.makedirs(log_dir, exist_ok=True)
            session_ts = time.strftime('%Y%m%dT%H%M%S')
            log_path = os.path.join(log_dir, f"rul_log_{safe_port}_{session_ts}.csv")
            self.log_fh = open(log_path, 'a', newline='', buffering=1)
            self._csv_writer = csv.writer(self.log_fh)
            if self.log_fh.tell() == 0:
                self._csv_writer.writerow(["timestamp_iso", "unix_time", "elapsed_s", "hi", "rul_s", "status"])
                self.log_fh.flush()
            self._session_start = time.time()
            self._last_mtime = None
            self._last_update_wall = self._session_start
            self._rows_since_fsync = 0
            self._was_stale = False
            self._features_path = os.path.join(log_dir, f"features_{safe_port}_{session_ts}.csv")
            return f" | logging every estimate to {log_path} and features to {self._features_path}"
        except OSError as e:
            self.log_fh = None
            self._features_path = None
            return f" | WARNING: could not open the log ({e}): estimates will NOT be saved to disk"

    def _start(self, env_path, script_path, port, mode, model_path, scaler_path, topic):
        if not env_path or not script_path:
            return [None, None, 1, None, None, "Bad configuration: ENV_PATH and SCRIPT_PATH are required", 1.0, -1.0]

        is_mqtt = port and port.strip().isdigit()
        if is_mqtt and not topic:
            return [None, None, 1, None, None, "Bad configuration: TOPIC is required for MQTT mode", 1.0, -1.0]

        base_path = os.path.dirname(sys.path[0])
        fb_dir = os.path.join(base_path, 'resources', 'function_blocks')
        res_env = os.path.join(base_path, env_path) if not os.path.isabs(env_path) else env_path
        res_script = os.path.join(fb_dir, script_path)   # os.path.join keeps absolute paths

        safe_port = port.replace('/', '_') if port else 'serial_default'
        self.rul_file = f"/tmp/online_rul_{safe_port}.txt"
        self._last_hi = 1.0
        self._last_rul_h = -1.0
        for stale in (self.rul_file, self.rul_file + ".tmp"):   # never reuse an estimate of a previous run
            try:
                os.remove(stale)
            except FileNotFoundError:
                pass

        log_note = self._open_log(os.path.join(base_path, 'resources', 'logs'), safe_port)

        if is_mqtt:
            # The broker runs on this device. The loop restarts mosquitto_sub if it exits.
            cmd = (
                f"source {res_env}/bin/activate && "
                f"while true; do mosquitto_sub -h localhost -p {port} -t {topic} -q 0; done "
                f"| pv -l -a "
                f"| python3 {res_script}"
                f" --rul-file {self.rul_file} --quiet"
            )
            if mode:
                cmd += f" --mode {mode}"
        else:
            cmd = (
                f"source {res_env}/bin/activate && "
                f"python3 {res_script}"
                f" --rul-file {self.rul_file} --quiet"
            )
            if port:
                cmd += f" --port {port}"

        if self._features_path:
            cmd += f" --dump-features {self._features_path}"
        if model_path:
            cmd += f" --model {os.path.join(fb_dir, model_path)}"
        if scaler_path:
            cmd += f" --scaler {os.path.join(fb_dir, scaler_path)}"

        try:
            self.process = subprocess.Popen(cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid)
            self._pgid = os.getpgid(self.process.pid)
        except Exception as e:
            self._close_log()
            return [None, None, 1, None, None, f"Process error: {e}", 1.0, -1.0]
        return [None, 1, None, None, None, f"Started (pgid={self._pgid}): {cmd}{log_note}", 1.0, -1.0]

    def _poll(self):
        wait = self.POLL_INTERVAL_S - (time.time() - self._last_poll)
        if wait > 0:
            time.sleep(wait)
        self._last_poll = time.time()

        if not self.rul_file or not os.path.isfile(self.rul_file):
            return [None, None, None, None, 1, "WAITING: no estimate yet", self._last_hi, self._last_rul_h]

        try:
            mtime = os.path.getmtime(self.rul_file)
            with open(self.rul_file, 'r') as fh:
                lines = fh.read().splitlines()
            hi = float(lines[0])
            status = lines[1] if len(lines) > 1 else "OK"
            rul_s = float(lines[2]) if len(lines) > 2 else None
        except (ValueError, OSError, IndexError) as e:
            return [None, None, None, None, 1, f"Error reading RUL file: {e}", self._last_hi, self._last_rul_h]

        if rul_s is not None and rul_s >= 0:
            rul = rul_s / 3600.0
            status += f" | RUL >= {rul:.2f} h (healthy)" if hi >= 0.999 else f" | RUL {rul:.2f} h"
        else:
            rul_s, rul = None, -1.0
            status += " | RUL unavailable"
        self._last_hi = hi
        self._last_rul_h = rul

        now = time.time()
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            self._last_update_wall = now
            if self._was_stale:
                status += " | RECOVERED"
                self._was_stale = False
            self._log_row(hi, rul_s, status)
        else:
            gap = now - (self._last_update_wall or now)
            if gap > self.STALE_AFTER_S:
                status += f" | STALE: no new estimate for {gap:.1f}s"
                if not self._was_stale:
                    self._was_stale = True
                    self._log_row(hi, rul_s, status)

        return [None, None, None, None, 1, status, hi, rul]

    def schedule(self, event_name, event_value, env_path, script_path, port, mode,
                 model_path, scaler_path, topic):
        if event_name == 'INIT':
            return [1, None, None, None, None, "Initialized", 1.0, -1.0]

        if event_name == 'START':
            return self._start(env_path, script_path, port, mode, model_path, scaler_path, topic)

        if event_name == 'STOP':
            if self._pgid is None and self.process is None and self.log_fh is None:
                return [None, None, None, 1, None, "No process currently running", 1.0, -1.0]
            self._cleanup()
            return [None, None, None, 1, None, "Process successfully stopped", 1.0, -1.0]

        if event_name == 'POLL':
            return self._poll()

        return [None, None, None, None, None, "", 1.0, -1.0]
