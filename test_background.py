"""Tests for the background processing lifecycle, including timeout and failure paths."""

import concurrent.futures
from unittest.mock import MagicMock, patch

import pytest

from app.background import _mark_failed, process_image, recover_stale_processing_jobs


def _make_image(image_id=1, status="pending", filepath="/tmp/test.jpg", result=None):
    image = MagicMock()
    image.id = image_id
    image.status = status
    image.filepath = filepath
    image.analysis_result = result
    return image


def _make_db(image):
    db = MagicMock()
    db.get.return_value = image
    return db


# ---------------------------------------------------------------------------
# process_image: happy path
# ---------------------------------------------------------------------------

@patch("app.background.SessionLocal")
@patch("app.background._executor")
@patch("app.background.analyze_image")
def test_process_image_completes(mock_analyze, mock_executor, mock_session_local):
    image = _make_image()
    db = _make_db(image)
    mock_session_local.return_value = db

    future = concurrent.futures.Future()
    future.set_result({"blur_score": 0.9, "brightness_score": 120.0, "plate_text": "MH12AB1234",
                       "extracted_text": "MH 12 AB 1234", "plate_valid": True,
                       "duplicate": False, "remarks": "Valid plate."})
    mock_executor.submit.return_value = future

    process_image(1)

    assert image.status == "completed"
    db.commit.assert_called()


# ---------------------------------------------------------------------------
# process_image: analysis raises → should set status to "failed"
# ---------------------------------------------------------------------------

@patch("app.background._mark_failed")
@patch("app.background.SessionLocal")
@patch("app.background._executor")
def test_process_image_fails_on_exception(mock_executor, mock_session_local, mock_mark_failed):
    image = _make_image()
    db = _make_db(image)
    mock_session_local.return_value = db

    future = concurrent.futures.Future()
    future.set_exception(ValueError("OCR broke"))
    mock_executor.submit.return_value = future

    process_image(1)

    mock_mark_failed.assert_called_once()
    call_args = mock_mark_failed.call_args[0]
    assert call_args[0] == 1
    assert "failed" in call_args[1].lower() or "server" in call_args[1].lower()


# ---------------------------------------------------------------------------
# process_image: timeout → should set status to "failed" with timeout message
# ---------------------------------------------------------------------------

@patch("app.background._mark_failed")
@patch("app.background.SessionLocal")
@patch("app.background._executor")
@patch("app.background.PROCESSING_TIMEOUT_SECONDS", 1)
def test_process_image_times_out(mock_executor, mock_session_local, mock_mark_failed):
    image = _make_image()
    db = _make_db(image)
    mock_session_local.return_value = db

    future = MagicMock()
    future.result.side_effect = concurrent.futures.TimeoutError()
    mock_executor.submit.return_value = future

    process_image(1)

    mock_mark_failed.assert_called_once()
    call_args = mock_mark_failed.call_args[0]
    assert call_args[0] == 1
    assert "timed out" in call_args[1].lower()


# ---------------------------------------------------------------------------
# recover_stale_processing_jobs: stuck rows become "failed"
# ---------------------------------------------------------------------------

@patch("app.background.SessionLocal")
def test_recover_stale_jobs(mock_session_local):
    stale_image = _make_image(status="processing")
    stale_image.analysis_result = None

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [stale_image]
    mock_session_local.return_value = db

    recover_stale_processing_jobs()

    assert stale_image.status == "failed"
    db.commit.assert_called_once()


@patch("app.background.SessionLocal")
def test_recover_no_stale_jobs_is_noop(mock_session_local):
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    mock_session_local.return_value = db

    recover_stale_processing_jobs()

    db.commit.assert_not_called()
