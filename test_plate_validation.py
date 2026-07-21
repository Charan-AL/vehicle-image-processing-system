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
