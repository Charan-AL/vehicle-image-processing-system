"""Validation helpers for Indian vehicle registration numbers."""

import re


INDIAN_STATE_CODE_PATTERN = "AN|AP|AR|AS|BR|CH|CG|DD|DL|DN|GA|GJ|HP|HR|JK|JH|KA|KL|LA|LD|MH|ML|MN|MP|MZ|NL|OD|OR|PB|PY|RJ|SK|TN|TR|TS|UK|UP|WB"
STANDARD_PLATE_PATTERN = rf"(?:{INDIAN_STATE_CODE_PATTERN})\d{{1,2}}[A-Z]{{0,3}}\d{{1,4}}"
BHARAT_SERIES_PLATE_PATTERN = r"\d{2}BH\d{1,4}[A-Z]{1,2}"
INDIAN_PLATE_PATTERN = re.compile(
    rf"^(?:{STANDARD_PLATE_PATTERN}|{BHARAT_SERIES_PLATE_PATTERN})$"
)
INDIAN_PLATE_SEARCH_PATTERN = re.compile(
    rf"(?:{STANDARD_PLATE_PATTERN}|{BHARAT_SERIES_PLATE_PATTERN})"
)
OCR_SEPARATORS_PATTERN = re.compile(r"[\s\-./]+")


def normalize_plate_text(ocr_text: str | None) -> str | None:
    """Normalize OCR casing and common plate separators."""
    if not ocr_text:
        return None

    normalized_text = OCR_SEPARATORS_PATTERN.sub("", ocr_text.upper())
    return normalized_text or None


def find_registration_number(ocr_text: str | None) -> str | None:
    """Find the first supported registration number in combined OCR text."""
    normalized_text = normalize_plate_text(ocr_text)
    if not normalized_text:
        return None

    match = INDIAN_PLATE_SEARCH_PATTERN.search(normalized_text)
    return match.group(0) if match else None


def is_valid_registration_number(ocr_text: str | None) -> bool:
    """Return whether OCR text matches a supported Indian plate format."""
    normalized_text = normalize_plate_text(ocr_text)
    return bool(normalized_text and INDIAN_PLATE_PATTERN.fullmatch(normalized_text))
