"""Image analysis interface."""

import logging
from functools import lru_cache
from typing import Any

import cv2
import easyocr
import numpy as np

from app.plate_validation import find_registration_number, normalize_plate_text


BLUR_THRESHOLD = 100.0
LOW_LIGHT_THRESHOLD = 80.0
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ocr_reader() -> easyocr.Reader:
    """Create the EasyOCR reader once for the application process."""
    return easyocr.Reader(["en"], gpu=False)


def extract_plate_region_text(image: np.ndarray) -> str:
    """Extract text specifically from the license plate region.

    Uses color and position heuristics to isolate the plate area.
    """
    h, w = image.shape[:2]
    reader = get_ocr_reader()

    # License plates are typically in lower half of vehicle images
    # Scan from 60% down to 95% of image height
    plate_roi_start = int(h * 0.6)
    plate_roi_end = int(h * 0.95)
    plate_region = image[plate_roi_start:plate_roi_end, :]

    # Enhance contrast to make plate text more readable
    if len(plate_region.shape) == 3:
        gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_region

    # Apply CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Apply threshold to get clear text
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR on enhanced plate region
    results = reader.readtext(binary, detail=1, paragraph=False)

    texts = []
    for detection in results:
        if len(detection) >= 3:
            text = detection[1].strip()
            confidence = float(detection[2])
            # Filter by confidence
            if text and confidence > 0.4:
                texts.append(text)

    return "\n".join(texts)


def extract_all_text_with_details(filepath: str) -> list[tuple[str, float]]:
    """Extract ALL text from image with confidence scores.

    Returns:
        List of (text, confidence) tuples sorted by confidence descending
    """
    reader = get_ocr_reader()
    results = reader.readtext(filepath, detail=1, paragraph=False)

    detections = []
    for detection in results:
        if len(detection) >= 3:
            text = detection[1].strip()
            confidence = float(detection[2])
            if text:
                detections.append((text, confidence))

    # Sort by confidence descending
    detections.sort(key=lambda x: x[1], reverse=True)
    return detections


def extract_text(filepath: str) -> str:
    """Extract text with focus on license plate region.

    Strategy:
    1. Try to extract from plate region specifically
    2. Fall back to full image extraction
    """
    try:
        image = cv2.imread(filepath)
        if image is None:
            raise ValueError("Unable to read image")

        # Strategy 1: Extract from plate region
        plate_text = extract_plate_region_text(image)
        if plate_text:
            logger.debug(f"Extracted from plate region: {plate_text[:100]}")
            return plate_text

        # Strategy 2: Fall back to full image
        detections = extract_all_text_with_details(filepath)
        if not detections:
            return ""

        # Return all text sorted by confidence (high to low)
        return "\n".join(text for text, _ in detections)
    except Exception as e:
        logger.exception("Text extraction failed: %s", e)
        raise ValueError("Unable to extract text from image") from e


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
    plate_valid = None
    try:
        ocr_text = extract_text(filepath)
        if ocr_text:
            # find_registration_number handles normalization internally
            plate_text = find_registration_number(ocr_text)
            plate_valid = plate_text is not None
            remarks += " Valid registration number." if plate_valid else " Invalid registration number."
        else:
            remarks += " No text detected."
    except Exception:
        logger.exception("OCR failed for image %s.", filepath)
        remarks += " OCR could not be completed."

    return {
        "blur_score": blur_score,
        "is_blurry": is_blurry,
        "brightness_score": brightness_score,
        "low_light": low_light,
        "plate_text": plate_text,
        "plate_valid": plate_valid,
        "duplicate": None,
        "remarks": remarks,
    }
