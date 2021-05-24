"""``pytest`` configuration."""

import pytest
from starlette.testclient import TestClient


@pytest.fixture(autouse=True)
def env(monkeypatch):
    pass

@pytest.fixture
def app() -> TestClient:
    """Make sure we use monkeypatch env."""

    from mosaic_api.main import app

    return TestClient(app)
