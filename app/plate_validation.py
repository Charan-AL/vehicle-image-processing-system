"""Validation helpers for Indian vehicle registration numbers."""

import re
import logging

logger = logging.getLogger(__name__)

# Indian state codes (2 letters)
INDIAN_STATES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN",
    "GA", "GJ", "HP", "HR", "JK", "JH", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB", "PY",
    "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}

STATE_CODE_PATTERN = "|".join(sorted(INDIAN_STATES, key=len, reverse=True))

# Standard Indian registration plate format: MH02AB1234 or MH12M09556
# State code (2 letters) + District code (2 digits) + Category (0-3 letters) + Serial (1-5 digits)
STANDARD_PLATE_PATTERN = rf"(?:{STATE_CODE_PATTERN})\d{{1,2}}[A-Z]{{0,3}}\d{{1,5}}"

# Bharat series: 01BH1234AB
BHARAT_SERIES_PATTERN = r"\d{2}BH\d{1,5}[A-Z]{1,2}"

# Combined pattern for searching
INDIAN_PLATE_SEARCH_PATTERN = re.compile(
    rf"({STANDARD_PLATE_PATTERN}|{BHARAT_SERIES_PATTERN})"
)

STANDARD_PLATE_VALIDATE_PATTERN = re.compile(
    rf"^(?:{STATE_CODE_PATTERN})\d{{1,2}}[A-Z]{{0,3}}\d{{4}}$"
)
BHARAT_SERIES_VALIDATE_PATTERN = re.compile(r"^\d{2}BH\d{4}[A-Z]{1,2}$")

# Remove non-alphanumeric and common OCR separators
SEPARATORS_PATTERN = re.compile(r"[\s\-./·|]+")

# Map of common OCR character misreadings
OCR_CORRECTIONS = {
    # Letters confused with numbers
    "O": "0",  # O (letter) → 0 (zero)
    "I": "1",  # I (letter) → 1 (one)
    "L": "1",  # L (letter) → 1 (one)
    "S": "5",  # S (letter) → 5 (five)
    "Z": "2",  # Z (letter) → 2 (two)
    "B": "8",  # B (letter) → 8 (eight) - sometimes
}


def normalize_plate_text(ocr_text: str | None) -> str | None:
    """Normalize OCR text: remove separators and convert to uppercase."""
    if not ocr_text:
        return None

    # Remove common separators and extra whitespace
    text = SEPARATORS_PATTERN.sub("", ocr_text).upper().strip()

    # Filter out purely numeric or purely alphabetic garbage
    if not text or len(text) < 5:
        return None

    return text


def correct_ocr_misreadings(text: str) -> str:
    """Correct ambiguous characters only in the numeric sections of one plate."""
    normalized = normalize_plate_text(text)
    if not normalized or normalized[:2] not in INDIAN_STATES:
        return text

    for series_length in range(4):
        serial_start = 4 + series_length
        if len(normalized) != serial_start + 4:
            continue

        district = normalized[2:4].translate(str.maketrans(OCR_CORRECTIONS))
        series = normalized[4:serial_start]
        serial = normalized[serial_start:].translate(str.maketrans(OCR_CORRECTIONS))
        corrected = f"{normalized[:2]}{district}{series}{serial}"
        if STANDARD_PLATE_VALIDATE_PATTERN.fullmatch(corrected):
            return corrected

    return normalized


def find_valid_plate_match(text: str) -> str | None:
    for match in INDIAN_PLATE_SEARCH_PATTERN.finditer(text):
        plate = match.group(0)
        if is_valid_registration_number(plate):
            return plate
    return None


def find_registration_number(ocr_text: str | None) -> str | None:
    """Find the first valid Indian registration number in OCR text.

    Tries multiple strategies:
    1. Search in normalized combined text (strips all whitespace)
    2. Apply OCR corrections to combined text
    3. Search individual lines with direct and corrected patterns
    4. Sliding-window of consecutive line pairs/triplets (handles split plates)
    """
    if not ocr_text:
        logger.debug("No text to extract registration from")
        return None

    logger.info(f"Input OCR text: {repr(ocr_text[:300])}")

    # Strategy 1: Direct search on combined text (all separators stripped)
    normalized_combined = normalize_plate_text(ocr_text)
    logger.debug(f"Normalized combined: {repr(normalized_combined[:100] if normalized_combined else None)}")

    if normalized_combined:
        plate = find_valid_plate_match(normalized_combined)
        if plate:
            logger.info(f"Found plate (direct): {plate}")
            return plate

    # Strategy 2: Try OCR corrections on combined text
    if normalized_combined:
        corrected_combined = correct_ocr_misreadings(normalized_combined)
        logger.debug(f"Corrected combined: {repr(corrected_combined[:100] if corrected_combined else None)}")

        if corrected_combined != normalized_combined:
            plate = find_valid_plate_match(corrected_combined)
            if plate:
                logger.info(f"Found plate (corrected): {plate}")
                return plate

    # Strategy 3: Search individual lines/words
    lines = [l for l in (ocr_text.split("\n") if ocr_text else []) if l.strip()]
    logger.debug(f"Searching {len(lines)} lines individually")

    for idx, line in enumerate(lines):
        normalized_line = normalize_plate_text(line)
        if normalized_line:
            logger.debug(f"Line {idx} normalized: {repr(normalized_line)}")
            plate = find_valid_plate_match(normalized_line)
            if plate:
                logger.info(f"Found plate (line {idx} direct): {plate}")
                return plate

            corrected_line = correct_ocr_misreadings(normalized_line)
            if corrected_line != normalized_line:
                logger.debug(f"Line {idx} corrected: {repr(corrected_line)}")
                plate = find_valid_plate_match(corrected_line)
                if plate:
                    logger.info(f"Found plate (line {idx} corrected): {plate}")
                    return plate

    # Strategy 4: sliding window of consecutive lines (handles OCR splitting a
    # plate like "MH12N" / "W8556" onto separate detection lines with other text
    # in between when the full-image OCR reads token-by-token).
    for window in (2, 3):
        for start in range(len(lines) - window + 1):
            combined = " ".join(lines[start:start + window])
            normalized_window = normalize_plate_text(combined)
            if normalized_window:
                plate = find_valid_plate_match(normalized_window)
                if plate:
                    logger.info(f"Found plate (window {start}+{window}): {plate}")
                    return plate
                corrected_window = correct_ocr_misreadings(normalized_window)
                if corrected_window != normalized_window:
                    plate = find_valid_plate_match(corrected_window)
                    if plate:
                        logger.info(f"Found plate (window {start}+{window} corrected): {plate}")
                        return plate

    logger.warning("No registration number found in OCR text")
    return None


def is_valid_registration_number(ocr_text: str | None) -> bool:
    """Check whether text exactly matches a supported Indian plate format."""
    normalized_text = normalize_plate_text(ocr_text)
    if not normalized_text:
        return False

    if STANDARD_PLATE_VALIDATE_PATTERN.fullmatch(normalized_text):
        return True
    if BHARAT_SERIES_VALIDATE_PATTERN.fullmatch(normalized_text):
        return True

    corrected = correct_ocr_misreadings(normalized_text)
    return bool(
        STANDARD_PLATE_VALIDATE_PATTERN.fullmatch(corrected)
        or BHARAT_SERIES_VALIDATE_PATTERN.fullmatch(corrected)
    )
