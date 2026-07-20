"""Image analysis interface."""

from typing import Any

import cv2


BLUR_THRESHOLD = 100.0


def analyze_image(filepath: str) -> dict[str, Any]:
    """Calculate an image blur score using the Variance of Laplacian."""
    grayscale_image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    if grayscale_image is None:
        raise ValueError("Unable to read image for blur detection.")

    blur_score = float(cv2.Laplacian(grayscale_image, cv2.CV_64F).var())
    is_blurry = blur_score < BLUR_THRESHOLD

    return {
        "blur_score": blur_score,
        "is_blurry": is_blurry,
        "brightness_score": None,
        "plate_text": None,
        "plate_valid": None,
        "duplicate": None,
        "remarks": "Image is blurry." if is_blurry else "Image is sharp enough.",
    }
