import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db").replace("\\", "/")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def signup(client, email="a@test.com"):
    r = client.post("/auth/signup", json={"email": email, "password": "password1", "name": "홍길동"})
    assert r.status_code == 201
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_curriculum_public(client):
    course = client.get("/courses/1").json()
    assert len(course["weeks"]) == 8
    assert client.get("/courses/1/weeks/3").json()["practices"][0]["steps"]
    assert client.get("/courses/1/weeks/9").status_code == 404


def test_signup_duplicate_and_login(client):
    signup(client, "b@test.com")
    dup = client.post("/auth/signup", json={"email": "b@test.com", "password": "password1", "name": "x"})
    assert dup.status_code == 409
    bad = client.post("/auth/login", json={"email": "b@test.com", "password": "wrongpass"})
    assert bad.status_code == 401
    ok = client.post("/auth/login", json={"email": "b@test.com", "password": "password1"})
    assert ok.status_code == 200


def test_password_byte_limit(client):
    korean_ok = "가" * 24  # 72바이트: 허용 한계
    korean_long = "가" * 25  # 75바이트: 초과
    r = client.post("/auth/signup", json={"email": "kr@test.com", "password": korean_ok, "name": "홍길동"})
    assert r.status_code == 201
    assert client.post("/auth/login", json={"email": "kr@test.com", "password": korean_ok}).status_code == 200
    too_long = client.post("/auth/signup", json={"email": "kr2@test.com", "password": korean_long, "name": "홍길동"})
    assert too_long.status_code == 400
    assert "너무 깁니다" in too_long.json()["detail"]
    # 길이 초과 비밀번호로 로그인해도 500이 아니라 401
    assert client.post("/auth/login", json={"email": "kr@test.com", "password": korean_long}).status_code == 401


def test_enrollment_rules(client):
    h = signup(client, "c@test.com")
    assert client.post("/enrollments", json={"cohort_id": 1}).status_code == 401
    r = client.post("/enrollments", json={"cohort_id": 1}, headers=h)
    assert r.status_code == 201
    assert client.post("/enrollments", json={"cohort_id": 1}, headers=h).status_code == 409
    seats = {c["id"]: c["seats_left"] for c in client.get("/cohorts?status=open").json()}
    assert seats[1] == 19
    eid = r.json()["id"]
    assert client.patch(f"/enrollments/{eid}/cancel", headers=h).json()["status"] == "canceled"
    assert {c["id"]: c["seats_left"] for c in client.get("/cohorts").json()}[1] == 20
    assert client.post("/enrollments", json={"cohort_id": 1}, headers=h).status_code == 201


def test_progress_admin_only(client):
    h = signup(client, "d@test.com")
    eid = client.post("/enrollments", json={"cohort_id": 2}, headers=h).json()["id"]
    assert client.patch(f"/enrollments/{eid}/progress", json={"current_week": 2}, headers=h).status_code == 403
    admin = client.post("/auth/login", json={"email": "admin@myaiedu.local", "password": "admin1234"}).json()
    ah = {"Authorization": "Bearer " + admin["access_token"]}
    assert client.patch(f"/enrollments/{eid}/progress", json={"current_week": 2}, headers=ah).json()["current_week"] == 2
    assert client.patch(f"/enrollments/{eid}/progress", json={"current_week": 9}, headers=ah).status_code == 422
