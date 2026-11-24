"""Checks every status code the brief asks for. Run: pytest -q"""

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client():
    main.reset()  # each test starts from the 3 example tasks
    return TestClient(main.app)


def test_root_and_health(client):
    assert client.get("/").json()["name"] == "Task API"
    assert client.get("/health").json() == {"status": "ok"}


def test_list_and_get(client):
    r = client.get("/tasks")
    assert r.status_code == 200 and len(r.json()) == 3
    assert client.get("/tasks/1").json()["id"] == 1


def test_unknown_id_is_404_with_error(client):
    r = client.get("/tasks/99")
    assert r.status_code == 404
    assert r.json() == {"error": "Task 99 not found"}


def test_non_numeric_id_is_400(client):
    assert client.get("/tasks/abc").status_code == 400


def test_create(client):
    r = client.post("/tasks", json={"title": "  Buy milk  "})
    assert r.status_code == 201
    assert r.json() == {"id": 4, "title": "Buy milk", "done": False}
    assert len(client.get("/tasks").json()) == 4


@pytest.mark.parametrize("body", [{}, {"title": ""}, {"title": "   "}, {"title": 123}])
def test_create_rejects_bad_title(client, body):
    r = client.post("/tasks", json=body)
    assert r.status_code == 400
    assert "error" in r.json()


def test_update(client):
    r = client.put("/tasks/2", json={"done": True})
    assert r.status_code == 200 and r.json()["done"] is True
    r = client.put("/tasks/2", json={"title": "Renamed"})
    assert r.json() == {"id": 2, "title": "Renamed", "done": True}


@pytest.mark.parametrize("body", [{}, {"title": ""}, {"done": "yes"}])
def test_update_rejects_bad_body(client, body):
    assert client.put("/tasks/2", json=body).status_code == 400


def test_update_unknown_is_404(client):
    assert client.put("/tasks/99", json={"done": True}).status_code == 404


def test_delete(client):
    assert client.delete("/tasks/1").status_code == 204
    assert client.get("/tasks/1").status_code == 404
    assert client.delete("/tasks/1").status_code == 404


def test_ids_are_not_reused_after_delete(client):
    created = client.post("/tasks", json={"title": "Temp"}).json()["id"]
    client.delete(f"/tasks/{created}")
    assert client.post("/tasks", json={"title": "New"}).json()["id"] == created + 1


def test_filters_and_stats(client):
    assert [t["id"] for t in client.get("/tasks?done=true").json()] == [1]
    assert [t["id"] for t in client.get("/tasks?search=github").json()] == [3]
    assert client.get("/stats").json() == {"total": 3, "done": 1, "open": 2}
