class RUL_THRESHOLD:
    """Emits PRINT once when the estimated RUL falls below THRESHOLD.

    The block re-arms only when the RUL rises above THRESHOLD + HYSTERESIS_H, for
    example after the part has been replaced, so that fluctuations of the estimate
    around the threshold do not issue repeated orders. A negative VALUE means that
    no estimate is available yet: it is ignored and never fires.
    """

    HYSTERESIS_H = 0.5

    def __init__(self):
        self.armed = True

    def schedule(self, event_name, event_value, value, threshold):
        if event_name == 'INIT':
            self.armed = True
            return [1, None, None, "Initialized (armed)"]

        if event_name == 'RUN':
            if value is None or threshold is None:
                return [None, 1, None, "Error: VALUE and THRESHOLD are required"]
            try:
                rul, thr = float(value), float(threshold)
            except (TypeError, ValueError) as e:
                return [None, 1, None, f"Error: could not convert inputs to float: {e}"]

            if rul < 0:
                return [None, 1, None, "WAITING: no RUL estimate yet"]

            print_order = None
            rearm = thr + self.HYSTERESIS_H
            if self.armed and rul < thr:
                self.armed = False
                print_order = 1
                status = f"PRINT ORDER: RUL {rul:.2f} h < threshold {thr:.2f} h"
            elif not self.armed and rul >= rearm:
                self.armed = True
                status = f"RE-ARMED: RUL {rul:.2f} h >= {rearm:.2f} h"
            elif not self.armed:
                status = f"ORDER ISSUED: RUL {rul:.2f} h (waiting for RUL >= {rearm:.2f} h to re-arm)"
            else:
                status = f"OK: RUL {rul:.2f} h >= threshold {thr:.2f} h"
            return [None, 1, print_order, status]

        return [None, None, None, ""]
