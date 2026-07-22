"""Image quality and license plate analysis helpers."""

import logging
from functools import lru_cache
from typing import Any

import cv2
import easyocr
import numpy as np

from app.plate_validation import find_registration_number


BLUR_THRESHOLD = 100.0
LOW_LIGHT_THRESHOLD = 80.0
OCR_CONFIDENCE_THRESHOLD = 0.25
PLATE_OCR_CONFIDENCE_THRESHOLD = 0.1
PLATE_CHARACTER_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
logger = logging.getLogger(__name__)


# Model directory for pre-downloaded weights (avoids runtime HTTP fetch)
_OCR_MODEL_DIR: str | None = None


def configure_ocr_model_dir(model_dir: str) -> None:
    global _OCR_MODEL_DIR
    _OCR_MODEL_DIR = model_dir


@lru_cache(maxsize=1)
def get_ocr_reader() -> easyocr.Reader:
    """Create the EasyOCR reader once for the application process."""
    kwargs: dict = {"gpu": False}
    if _OCR_MODEL_DIR:
        kwargs["model_storage_directory"] = _OCR_MODEL_DIR
        kwargs["download_enabled"] = False
    return easyocr.Reader(["en"], **kwargs)


def detect_blur(image: np.ndarray) -> dict[str, float | bool]:
    """Measure image sharpness using the variance of the Laplacian."""
    blur_score = float(cv2.Laplacian(image, cv2.CV_64F).var())
    return {
        "blur_score": blur_score,
        "is_blurry": blur_score < BLUR_THRESHOLD,
    }


def detect_brightness(image: np.ndarray) -> dict[str, float | bool]:
    """Measure average grayscale brightness and detect low-light images."""
    brightness_score = float(image.mean())
    return {
        "brightness_score": brightness_score,
        "low_light": brightness_score < LOW_LIGHT_THRESHOLD,
    }


def read_ocr_text(
    reader: easyocr.Reader,
    image: np.ndarray,
    confidence_threshold: float = OCR_CONFIDENCE_THRESHOLD,
    allowlist: str | None = None,
) -> list[str]:
    """Return confident OCR detections in their visual reading order."""
    results = reader.readtext(
        image,
        detail=1,
        paragraph=False,
        allowlist=allowlist,
    )
    detections = [
        detection
        for detection in results
        if len(detection) >= 3
        and detection[1].strip()
        and float(detection[2]) > confidence_threshold
    ]
    detections.sort(key=lambda detection: (
        min(point[1] for point in detection[0]),
        min(point[0] for point in detection[0]),
    ))
    return [detection[1].strip() for detection in detections]


def extract_plate_region_text(image: np.ndarray) -> str:
    """Extract OCR text from likely license-plate regions."""
    height, width = image.shape[:2]
    reader = get_ocr_reader()
    lower_image = image[int(height * 0.55):int(height * 0.95), :]
    hsv = cv2.cvtColor(lower_image, cv2.COLOR_BGR2HSV)
    yellow_mask = cv2.inRange(
        hsv,
        np.array([15, 55, 80]),
        np.array([45, 255, 255]),
    )
    contours, _ = cv2.findContours(
        yellow_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

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

    candidates.extend([
        lower_image,
        image[int(height * 0.52):int(height * 0.78), :],
        image[int(height * 0.52):int(height * 0.78), int(width * 0.6):],
        image[int(height * 0.62):int(height * 0.9), :int(width * 0.4)],
        image[int(height * 0.62):int(height * 0.9), int(width * 0.6):],
    ])
    # Cap candidate regions to keep OCR work bounded. Yellow-mask hits are
    # prioritised; the fallback strips are appended last so they are the
    # ones dropped when the list is long.
    MAX_CANDIDATES = 4
    candidates = candidates[:MAX_CANDIDATES]
    texts: list[str] = []
    for candidate in candidates:
        if candidate.size == 0:
            continue
        enlarged = cv2.resize(candidate, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        grayscale = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(grayscale)
        _, binary = cv2.threshold(
            enhanced,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        sharpened = cv2.filter2D(
            enhanced,
            -1,
            np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]),
        )
        for variant in (enlarged, binary, sharpened):
            texts.extend(
                read_ocr_text(
                    reader,
                    variant,
                    PLATE_OCR_CONFIDENCE_THRESHOLD,
                    PLATE_CHARACTER_ALLOWLIST,
                )
            )

    return "\n".join(dict.fromkeys(texts))


def extract_all_text_with_details(filepath: str) -> list[tuple[str, float]]:
    """Extract all OCR text with confidence scores."""
    reader = get_ocr_reader()
    results = reader.readtext(filepath, detail=1, paragraph=False)
    detections: list[tuple[str, float]] = []
    for detection in results:
        if len(detection) < 3:
            continue
        text = detection[1].strip()
        if text:
            detections.append((text, float(detection[2])))

    detections.sort(key=lambda item: item[1], reverse=True)
    return detections


def extract_text(filepath: str) -> str:
    """Extract text from likely plate regions and the full image."""
    try:
        image = cv2.imread(filepath)
        if image is None:
            raise ValueError("Unable to read image")

        plate_text = extract_plate_region_text(image)
        full_image_text = "\n".join(
            text for text, _ in extract_all_text_with_details(filepath)
        )
        extracted_text = "\n".join(
            text for text in (plate_text, full_image_text) if text
        )
        if extracted_text:
            logger.debug("Extracted OCR text: %s", extracted_text[:100])
        return extracted_text
    except Exception as error:
        logger.exception("Text extraction failed: %s", error)
        raise ValueError("Unable to extract text from image") from error


def validate_plate(ocr_text: str) -> dict[str, str | bool | None]:
    """Find and validate a registration number in OCR output."""
    plate_text = find_registration_number(ocr_text) if ocr_text else None
    return {
        "plate_text": plate_text,
        "plate_valid": plate_text is not None,
    }


def build_remarks(
    quality: dict[str, float | bool],
    plate: dict[str, str | bool | None],
) -> str:
    """Build a human-readable summary of the analysis."""
    remarks = "Image is blurry." if quality["is_blurry"] else "Image is sharp enough."
    if quality["low_light"]:
        remarks += " Low light detected."
    if plate["plate_text"]:
        remarks += " Valid registration number."
    else:
        remarks += " Invalid registration number."
    return remarks


def analyze_image(filepath: str) -> dict[str, Any]:
    """Run quality checks, OCR, and plate validation as one analysis."""
    grayscale_image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    if grayscale_image is None:
        raise ValueError("Unable to read image for analysis.")

    quality = {
        **detect_blur(grayscale_image),
        **detect_brightness(grayscale_image),
    }
    extracted_text = extract_text(filepath)
    plate = validate_plate(extracted_text)

    return {
        **quality,
        **plate,
        "extracted_text": extracted_text or None,
        "duplicate": False,
        "remarks": build_remarks(quality, plate),
    }
