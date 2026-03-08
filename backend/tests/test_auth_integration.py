import pytest
from app.main import app
from app.db import get_db


@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "TestPassword123"})
    assert r.status_code == 200
    data = r.json()
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
    r2 = client.post("/auth/login", json={"email": "test@example.com", "password": "TestPassword123"})
    assert r2.status_code == 200
    assert "set-cookie" in r2.headers or r2.cookies


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "TestPassword123"})
    r = client.post("/auth/register", json={"email": "dup@example.com", "password": "OtherPass123"})
    assert r.status_code == 409


def test_password_policy(client):
    r = client.post("/auth/register", json={"email": "short@x.co", "password": "short"})
    assert r.status_code == 400
