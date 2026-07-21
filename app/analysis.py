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


def read_ocr_text(reader: easyocr.Reader, image: np.ndarray) -> list[str]:
    results = reader.readtext(image, detail=1, paragraph=False)
    return [
        detection[1].strip()
        for detection in results
        if len(detection) >= 3 and detection[1].strip() and float(detection[2]) > 0.25
    ]


def extract_plate_region_text(image: np.ndarray) -> str:
    """Extract text from likely license-plate regions."""
    height, width = image.shape[:2]
    reader = get_ocr_reader()
    lower_image = image[int(height * 0.55):int(height * 0.95), :]
    hsv = cv2.cvtColor(lower_image, cv2.COLOR_BGR2HSV)
    yellow_mask = cv2.inRange(hsv, np.array([15, 55, 80]), np.array([45, 255, 255]))
    contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[np.ndarray] = []
    for contour in contours:
        x, y, candidate_width, candidate_height = cv2.boundingRect(contour)
        aspect_ratio = candidate_width / candidate_height if candidate_height else 0
        if candidate_width < width * 0.08 or not 1.5 <= aspect_ratio <= 6:
            continue

        padding_x = max(4, int(candidate_width * 0.08))
        padding_y = max(4, int(candidate_height * 0.2))
        left = max(0, x - padding_x)
        top = max(0, y - padding_y)
        right = min(lower_image.shape[1], x + candidate_width + padding_x)
        bottom = min(lower_image.shape[0], y + candidate_height + padding_y)
        candidates.append(lower_image[top:bottom, left:right])

    candidates.append(lower_image)
    texts: list[str] = []
    for candidate in candidates:
        enlarged = cv2.resize(candidate, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        grayscale = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(grayscale)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        texts.extend(read_ocr_text(reader, enlarged))
        texts.extend(read_ocr_text(reader, binary))

    return "\n".join(dict.fromkeys(texts))


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

        plate_text = extract_plate_region_text(image)
        detections = extract_all_text_with_details(filepath)
        full_image_text = "\n".join(text for text, _ in detections)
        extracted_text = "\n".join(text for text in (plate_text, full_image_text) if text)
        if extracted_text:
            logger.debug("Extracted OCR text: %s", extracted_text[:100])
        return extracted_text
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
