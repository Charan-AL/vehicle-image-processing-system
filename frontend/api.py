import os
from typing import Any

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 30


class APIError(Exception):
    """Raised when the backend cannot complete a frontend request."""


def _request_json(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    try:
        response = requests.request(
            method,
            f"{BACKEND_URL}{path}",
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.ConnectionError as error:
        raise APIError(
            "Could not connect to the backend. Make sure the FastAPI server is running."
        ) from error
    except requests.Timeout as error:
        raise APIError("The backend request timed out. Please try again.") from error
    except requests.RequestException as error:
        raise APIError("The backend request failed. Please try again.") from error

    if response.ok:
        try:
            return response.json()
        except ValueError as error:
            raise APIError("The backend returned an invalid response.") from error

    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    message = detail or f"Backend request failed with status {response.status_code}."
    raise APIError(message)


def upload_image(file: Any) -> dict[str, Any]:
    """Upload an image file to the backend."""
    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type or "application/octet-stream",
        )
    }
    return _request_json("POST", "/upload", files=files)


def get_status(processing_id: int | str) -> dict[str, Any]:
    """Fetch the current processing status for an image."""
    return _request_json("GET", f"/status/{processing_id}")


def get_result(processing_id: int | str) -> dict[str, Any]:
    """Fetch the completed analysis result for an image."""
    return _request_json("GET", f"/result/{processing_id}")
