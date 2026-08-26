import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path):
    import src.app as app_module

    app_module._DB_PATH = tmp_path / "test.db"

    from src.app import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
