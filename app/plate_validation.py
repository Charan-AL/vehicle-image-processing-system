"""Validation helpers for Indian vehicle registration numbers."""

import re


STANDARD_PLATE_PATTERN = r"[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{1,4}"
BHARAT_SERIES_PLATE_PATTERN = r"\d{2}BH\d{1,4}[A-Z]{1,2}"
INDIAN_PLATE_PATTERN = re.compile(
    rf"^(?:{STANDARD_PLATE_PATTERN}|{BHARAT_SERIES_PLATE_PATTERN})$"
)
OCR_SEPARATORS_PATTERN = re.compile(r"[\s\-./]+")


def normalize_plate_text(ocr_text: str | None) -> str | None:
    """Normalize OCR casing and common plate separators."""
    if not ocr_text:
        return None

    normalized_text = OCR_SEPARATORS_PATTERN.sub("", ocr_text.upper())
    return normalized_text or None


def is_valid_registration_number(ocr_text: str | None) -> bool:
    """Return whether OCR text matches a supported Indian plate format."""
    normalized_text = normalize_plate_text(ocr_text)
    return bool(normalized_text and INDIAN_PLATE_PATTERN.fullmatch(normalized_text))
