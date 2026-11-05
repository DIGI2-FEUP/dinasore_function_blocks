import os
import time

import requests
from dotenv import load_dotenv

# The OctoPrint API key comes from the variable API_KEY: from the environment,
# or from a .env file next to this block.
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class PRINT_CHECK:
    """Reads the state and progress of the print job from the OctoPrint REST API.

    Each READ waits one second, to limit the rate at which the API is polled, and
    always fires READ_O, so that a polling loop keeps running. It also fires:
      PRINT_ERROR      if the request fails or OctoPrint reports an error;
      PRINT_DONE       if the job is complete, or if the printer is idle;
      PROGRESS_UPDATE  while a job is in progress.
    """

    def schedule(self, event_name, event_value, octo_url, request_timeout):
        if event_name == 'INIT':
            return [1, None, None, None, None, "", -1.0, ""]

        if event_name == 'READ':
            time.sleep(1)

            if not octo_url:
                return [None, 1, None, 1, None, "", -1.0, "OCTO_URL missing"]

            api_key = os.getenv('API_KEY')
            headers = {"X-Api-Key": api_key} if api_key else {}

            try:
                resp = requests.get(f"{octo_url.rstrip('/')}/api/job", headers=headers,
                                    timeout=request_timeout or 5.0)
            except Exception as e:
                return [None, 1, None, 1, None, "", -1.0, str(e)]

            if not resp.ok:
                return [None, 1, None, 1, None, "", -1.0, f"HTTP {resp.status_code}: {resp.text}"]

            job = resp.json()
            job_state = job.get("state", "")

            if job.get("error"):
                return [None, 1, None, 1, None, job_state, -1.0, job.get("error")]

            job_info = str(job)
            completion = (job.get("progress") or {}).get("completion")

            if isinstance(completion, (int, float)):
                completion = float(completion)
                if completion >= 99.9:  # OctoPrint reports the completion in percent
                    return [None, 1, 1, None, None, job_state, completion, job_info]
                return [None, 1, None, None, 1, job_state, completion, job_info]

            if job_state.lower() == "operational":
                return [None, 1, 1, None, None, job_state, -1.0, job_info]

            return [None, 1, None, None, None, job_state, -1.0, job_info]

        return [None, None, None, None, None, "", -1.0, ""]
