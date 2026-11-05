import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# The OctoPrint API key comes from the variable API_KEY: from the environment,
# or from a .env file next to this block.
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class PRINT_START:
    """Selects a stored G-code file and starts printing it, through the OctoPrint REST API."""

    def schedule(self, event_name, event_value, octo_url, location, file_path, request_timeout):
        if event_name == 'INIT':
            return [1, None, None, "", ""]

        if event_name == 'START_PRINT':
            if not octo_url or not file_path:
                return [None, None, 1, "Bad configuration: OCTO_URL and FILE_PATH required", ""]

            url = f"{octo_url.rstrip('/')}/api/files/{location}/{quote(file_path, safe='')}"
            api_key = os.getenv('API_KEY')
            headers = {"X-Api-Key": api_key} if api_key else {}
            payload = {"command": "select", "print": True}

            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=request_timeout or 10.0)
            except Exception as e:
                return [None, None, 1, f"Request error: {e}", ""]

            if not resp.ok:
                return [None, None, 1, f"Start failed: {resp.status_code} {resp.text}", ""]

            try:
                reply = str(resp.json())
            except ValueError:
                reply = resp.text or "<no body>"
            return [None, 1, None, "Started", reply]

        return [None, None, None, "", ""]
