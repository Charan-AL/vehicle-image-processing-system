from app.plate_validation import (
    find_registration_number,
    is_valid_registration_number,
    normalize_plate_text,
)


def test_standard_plate_with_ocr_separators_is_normalized_and_valid():
    ocr_text = "mh-12 ab 1234"

    assert normalize_plate_text(ocr_text) == "MH12AB1234"
    assert is_valid_registration_number(ocr_text) is True


def test_standard_plate_without_series_is_valid():
    assert is_valid_registration_number("MH 12 1234") is True


def test_registration_number_is_found_in_combined_ocr_text():
    ocr_text = "PUNE FC ROAD 7755900813 MH 12 NW 8556 CNG"

    assert find_registration_number(ocr_text) == "MH12NW8556"


def test_complete_plate_is_preferred_over_truncated_match():
    assert find_registration_number("MH8556 MH 12 NH 8556") == "MH12NH8556"


def test_plate_series_letters_are_not_rewritten_as_digits():
    assert find_registration_number("MH 12 N H 8556") == "MH12NH8556"
    assert is_valid_registration_number("MH12NH8556") is True


def test_mh12n8556_is_valid():
    assert is_valid_registration_number("MH12N8556") is True


def test_mh12n8556_found_in_ocr_context():
    ocr_text = "PUNE FC ROAD 7755900813 MH 12 N 8556 CNG"
    assert find_registration_number(ocr_text) == "MH12N8556"


def test_noisy_easyocr_tokens_are_reconstructed():
    ocr_text = "MHIZN\nCNG\nAQ4EWH\n48556\nMHI2N\nH8556\nPUNE-FCROAD"
    assert find_registration_number(ocr_text) == "MH12N8556"


def test_split_plate_tokens_across_lines_are_merged():
    # Simulates EasyOCR returning plate parts on separate detection lines
    # Strategy 4 (sliding-window) must reassemble them.
    ocr_text = "PUNE FC ROAD\n7755900813\nMH12N\n8556\nCNG"
    assert find_registration_number(ocr_text) == "MH12N8556"


def test_split_plate_with_intervening_token_merged_by_window():
    # Three-line window: "MH12N" + "W" + "8556" → "MH12NW8556"
    ocr_text = "MH12N\nW\n8556"
    assert find_registration_number(ocr_text) == "MH12NW8556"


def test_ocr_corrections_only_change_numeric_plate_sections():
    assert find_registration_number("MH 1Z NH 8S56") == "MH12NH8556"


def test_truncated_plate_match_is_rejected():
    assert find_registration_number("MH8556") is None


def test_unrecognized_state_code_is_invalid():
    assert is_valid_registration_number("RY775590") is False
    assert find_registration_number("PUNE FC ROAD 7755900813 RY775590") is None


def test_delhi_style_plate_with_single_letter_series_is_valid():
    assert is_valid_registration_number("DL01C1234") is True


def test_bharat_series_plate_is_valid():
    assert is_valid_registration_number("22 BH 1234 AA") is True


def test_invalid_plate_formats_are_rejected():
    invalid_plates = (
        "MH12AB12345",
        "MH12AB",
        "M12AB1234",
        "MH12AB1234!",
        "not a plate",
    )

    assert all(not is_valid_registration_number(plate) for plate in invalid_plates)


def test_empty_ocr_text_is_invalid():
    assert normalize_plate_text(None) is None
    assert normalize_plate_text("   ") is None
    assert is_valid_registration_number(None) is False
