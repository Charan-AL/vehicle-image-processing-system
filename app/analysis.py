"""Image analysis interface."""

from typing import Any


def analyze_image(filepath: str) -> dict[str, Any]:
    """Return the current analysis result shape without processing image data."""
    return {
        "blur_score": None,
        "brightness_score": None,
        "plate_text": None,
        "plate_valid": None,
        "duplicate": None,
        "remarks": "Analysis not implemented.",
    }
