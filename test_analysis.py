from unittest.mock import patch

import numpy as np
import pytest

from app.analysis import analyze_image


@patch("app.analysis.extract_text", return_value="PUNE FC ROAD\nMH 12 N 8556")
@patch("app.analysis.cv2.imread", return_value=np.zeros((20, 20), dtype=np.uint8))
def test_analysis_returns_raw_text_and_normalized_plate(_read_image, _extract_text):
    analysis = analyze_image("vehicle.jpg")

    assert analysis["extracted_text"] == "PUNE FC ROAD\nMH 12 N 8556"
    assert analysis["plate_text"] == "MH12N8556"
    assert analysis["plate_valid"] is True


@patch("app.analysis.extract_text", side_effect=ValueError("OCR unavailable"))
@patch("app.analysis.cv2.imread", return_value=np.zeros((20, 20), dtype=np.uint8))
def test_analysis_raises_when_ocr_fails(_read_image, _extract_text):
    with pytest.raises(ValueError, match="OCR unavailable"):
        analyze_image("vehicle.jpg")
