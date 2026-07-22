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


@pytest.mark.parametrize("image_status", ["pending", "processing", "completed", "failed"])
def test_status_returns_persisted_lifecycle_state(image_status):
    image = SimpleNamespace(
        id=7,
        filename="vehicle.jpg",
        status=image_status,
        created_at=datetime(2024, 1, 15, 10, 30),
        analysis_result=None,
    )
    client, session = client_for(image)

    try:
        response = client.get("/status/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "filename": "vehicle.jpg",
        "status": image_status,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": None,
    }
    assert session.requested_id == 7


def test_status_returns_not_found_for_unknown_image():
    client, session = client_for(None)

    try:
        response = client.get("/status/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Image not found."}
    assert session.requested_id == 999


@pytest.mark.parametrize("image_id", ["0", "-1", "invalid"])
def test_status_rejects_invalid_image_id(image_id):
    client, _ = client_for(None)

    try:
        response = client.get(f"/status/{image_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
