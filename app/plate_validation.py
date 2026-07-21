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
BHARAT_SERIES_PATTERN = r"\d{{2}}BH\d{{1,5}}[A-Z]{{1,2}}"

# Combined pattern for searching
INDIAN_PLATE_SEARCH_PATTERN = re.compile(
    rf"({STANDARD_PLATE_PATTERN}|{BHARAT_SERIES_PATTERN})"
)

INDIAN_PLATE_VALIDATE_PATTERN = re.compile(
    rf"^(?:{STANDARD_PLATE_PATTERN}|{BHARAT_SERIES_PATTERN})$"
)

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
    """Attempt to fix common OCR character confusions.

    Apply corrections character by character in context-aware ways.
    """
    corrected = text

    # Generic character replacements - the most common OCR errors
    # Do multiple passes for better coverage
    for _ in range(2):
        for wrong, right in OCR_CORRECTIONS.items():
            corrected = corrected.replace(wrong, right)

    # Try to find and fix partially correct state codes
    # Look for 2-letter patterns that are close to valid state codes
    for state in sorted(INDIAN_STATES, key=len, reverse=True):
        for i in range(max(0, len(corrected) - 2)):
            if i + 2 <= len(corrected):
                two_chars = corrected[i:i+2]
                if len(two_chars) == 2 and two_chars not in INDIAN_STATES:
                    # Count matching characters
                    score = sum(1 for a, b in zip(two_chars, state) if a.upper() == b)
                    if score == 2:  # Exact match - skip
                        continue
                    if score == 1:  # One char matches - likely a corruption, try fixing
                        # Check if replacing improves things
                        test_corrected = corrected[:i] + state + corrected[i+2:]
                        # Verify it makes sense (next char should match pattern)
                        corrected = test_corrected

    return corrected


def find_registration_number(ocr_text: str | None) -> str | None:
    """Find the first valid Indian registration number in OCR text.

    Tries multiple strategies:
    1. Search in normalized combined text
    2. Apply OCR corrections to combined text
    3. Search individual lines with both direct and corrected patterns
    4. Return best match found
    """
    if not ocr_text:
        logger.debug("No text to extract registration from")
        return None

    logger.debug(f"Input OCR text: {repr(ocr_text[:100])}")

    # Strategy 1: Direct search on combined text
    normalized_combined = normalize_plate_text(ocr_text)
    logger.debug(f"Normalized combined: {repr(normalized_combined[:100] if normalized_combined else None)}")

    if normalized_combined:
        match = INDIAN_PLATE_SEARCH_PATTERN.search(normalized_combined)
        if match:
            plate = match.group(0)
            logger.info(f"Found plate (direct): {plate}")
            return plate

    # Strategy 2: Try OCR corrections on combined text
    if normalized_combined:
        corrected_combined = correct_ocr_misreadings(normalized_combined)
        logger.debug(f"Corrected combined: {repr(corrected_combined[:100] if corrected_combined else None)}")

        if corrected_combined != normalized_combined:
            match = INDIAN_PLATE_SEARCH_PATTERN.search(corrected_combined)
            if match:
                plate = match.group(0)
                logger.info(f"Found plate (corrected): {plate}")
                return plate

    # Strategy 3: Search individual lines/words
    lines = ocr_text.split("\n") if ocr_text else []
    logger.debug(f"Searching {len(lines)} lines individually")

    for idx, line in enumerate(lines):
        if not line.strip():
            continue

        # Try direct pattern on each line
        normalized_line = normalize_plate_text(line)
        if normalized_line:
            logger.debug(f"Line {idx} normalized: {repr(normalized_line)}")
            match = INDIAN_PLATE_SEARCH_PATTERN.search(normalized_line)
            if match:
                plate = match.group(0)
                logger.info(f"Found plate (line {idx} direct): {plate}")
                return plate

            # Try with corrections on each line
            corrected_line = correct_ocr_misreadings(normalized_line)
            if corrected_line != normalized_line:
                logger.debug(f"Line {idx} corrected: {repr(corrected_line)}")
                match = INDIAN_PLATE_SEARCH_PATTERN.search(corrected_line)
                if match:
                    plate = match.group(0)
                    logger.info(f"Found plate (line {idx} corrected): {plate}")
                    return plate

    logger.warning(f"No registration number found in OCR text")
    return None


def is_valid_registration_number(ocr_text: str | None) -> bool:
    """Check if text exactly matches a valid Indian plate format."""
    normalized_text = normalize_plate_text(ocr_text)
    if not normalized_text:
        return False

    # Must match the pattern
    if not INDIAN_PLATE_VALIDATE_PATTERN.fullmatch(normalized_text):
        # Try with corrections
        corrected = correct_ocr_misreadings(normalized_text)
        if not INDIAN_PLATE_VALIDATE_PATTERN.fullmatch(corrected):
            return False
        normalized_text = corrected

    # Additional validation: check for typical Indian plate characteristics
    # Standard plates usually have: StateCode (2) + District (1-2 digits) + Letters (0-3) + Serial (4-5 digits)
    # They should have at least 8 characters total and no more than 12
    if not (8 <= len(normalized_text) <= 12):
        return False

    # At least 4 digits in the serial number portion (last part)
    # Extract the last contiguous digit sequence
    last_digits = ""
    for char in reversed(normalized_text):
        if char.isdigit():
            last_digits = char + last_digits
        else:
            break

    if len(last_digits) < 4:
        return False

    return True
