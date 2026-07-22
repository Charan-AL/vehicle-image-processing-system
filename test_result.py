from datetime import datetime
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Image


class FakeSession:
    def __init__(self, image):
        self.image = image
        self.requested_id = None

    def get(self, model, image_id):
        assert model is Image
        self.requested_id = image_id
        return self.image


def client_for(image):
    session = FakeSession(image)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session


def test_result_returns_analysis_fields():
    result = SimpleNamespace(
        id=12,
        image_id=7,
        blur_score=0.82,
        brightness_score=0.64,
        plate_text="MH12AB1234",
        extracted_text="MH 12 AB 1234",
        plate_valid=True,
        duplicate=False,
        remarks="Valid plate detected successfully",
        completed_at=datetime(2024, 1, 15, 10, 31, 45),
    )
    image = SimpleNamespace(analysis_result=result)
    client, session = client_for(image)

    try:
        response = client.get("/result/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["blur_score"] == 0.82
    assert body["brightness_score"] == 0.64
    assert body["plate_text"] == "MH12AB1234"
    assert body["plate_valid"] is True
    assert body["duplicate"] is False
    assert body["remarks"] == "Valid plate detected successfully"
    assert session.requested_id == 7


def test_result_returns_not_found_when_analysis_is_unavailable():
    client, session = client_for(SimpleNamespace(analysis_result=None))

    try:
        response = client.get("/result/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Analysis result is not available yet."}
    assert session.requested_id == 7


def test_result_returns_not_found_for_unknown_image():
    client, session = client_for(None)

    try:
        response = client.get("/result/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Image not found."}
    assert session.requested_id == 999


@pytest.mark.parametrize("image_id", ["0", "-1", "invalid"])
def test_result_rejects_invalid_image_id(image_id):
    client, _ = client_for(None)

    try:
        response = client.get(f"/result/{image_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
