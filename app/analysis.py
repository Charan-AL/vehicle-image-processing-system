"""Image analysis interface."""

import logging
from functools import lru_cache
from typing import Any

import cv2
import easyocr


BLUR_THRESHOLD = 100.0
LOW_LIGHT_THRESHOLD = 80.0
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ocr_reader() -> easyocr.Reader:
    """Create the EasyOCR reader once for the application process."""
    return easyocr.Reader(["en"], gpu=False)


def extract_text(filepath: str) -> str:
    """Extract and combine every English text region found in an image."""
    text_regions = get_ocr_reader().readtext(filepath, detail=0, paragraph=False)
    return "\n".join(
        normalized_text
        for text in text_regions
        if (normalized_text := " ".join(text.split()))
    )


def analyze_image(filepath: str) -> dict[str, Any]:
    """Calculate quality metrics and extract text from an uploaded image."""
    grayscale_image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    if grayscale_image is None:
        raise ValueError("Unable to read image for analysis.")

    blur_score = float(cv2.Laplacian(grayscale_image, cv2.CV_64F).var())
    is_blurry = blur_score < BLUR_THRESHOLD
    brightness_score = float(grayscale_image.mean())
    low_light = brightness_score < LOW_LIGHT_THRESHOLD

    remarks = "Image is blurry." if is_blurry else "Image is sharp enough."
    if low_light:
        remarks += " Low light detected."

    plate_text = None
    try:
        plate_text = extract_text(filepath)
        remarks += " Text extracted." if plate_text else " No text detected."
    except Exception:
        logger.exception("OCR failed for image %s.", filepath)
        remarks += " OCR could not be completed."

    return {
        "blur_score": blur_score,
        "is_blurry": is_blurry,
        "brightness_score": brightness_score,
        "low_light": low_light,
        "plate_text": plate_text,
        "plate_valid": None,
        "duplicate": None,
        "remarks": remarks,
    }
