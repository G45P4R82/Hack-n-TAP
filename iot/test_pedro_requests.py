"""
Simple script to POST the same JSON payload originally sent via curl.

Requires the `requests` library: pip install requests
"""

import json
import sys
from typing import Any, Dict

try:
    import requests
except Exception:
    print("The 'requests' library is required. Install it with: pip install requests", file=sys.stderr)
    raise


URL = "http://127.0.0.1:8000/api/tap/4/"


def make_payload() -> Dict[str, Any]:
    # Recreate the JSON payload from the original curl command.
    return {"device_id": "Card UID: 3A B4 B5 1"}


def post_payload(url: str, payload: Dict[str, Any]) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp


def main() -> None:
    payload = make_payload()
    print("Posting to:\t", URL)
    print("Payload:\t", json.dumps(payload))
    try:
        resp = post_payload(URL, payload)
    except requests.RequestException as exc:
        print("Request failed:\t", exc, file=sys.stderr)
        sys.exit(1)

    print("Response status:\t", resp.status_code)
    try:
        print("Response JSON:\t", resp.json())
    except ValueError:
        print("Response text:\t", resp.text)


if __name__ == "__main__":
    main()
