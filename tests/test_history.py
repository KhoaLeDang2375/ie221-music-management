"""[NGƯỜI B] Kiểm thử cho nhóm API Lịch sử nghe nhạc (UC-13)."""

from fastapi.testclient import TestClient


def test_history_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/me/history").status_code == 401
    assert client.post("/api/v1/me/history", json={"track_id": 1}).status_code == 401


def test_get_recent_history_default_and_limit_validation(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    res = client.get("/api/v1/me/history", headers=user_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 20
    assert all(item["user_id"] == 2 for item in items)
    assert all("track" in item and item["track"]["name"] for item in items)
    timestamps = [item["listened_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)

    res_5 = client.get("/api/v1/me/history?limit=5", headers=user_headers)
    assert res_5.status_code == 200
    assert len(res_5.json()) == 5

    assert client.get("/api/v1/me/history?limit=0", headers=user_headers).status_code == 422
    assert client.get("/api/v1/me/history?limit=51", headers=user_headers).status_code == 422


def test_record_listen_repeated_and_nonexistent_track(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    assert (
        client.post(
            "/api/v1/me/history", headers=user_headers, json={"track_id": 999999}
        ).status_code
        == 404
    )

    first = client.post("/api/v1/me/history", headers=user_headers, json={"track_id": 5})
    assert first.status_code == 201
    assert first.json()["track_id"] == 5

    second = client.post("/api/v1/me/history", headers=user_headers, json={"track_id": 5})
    assert second.status_code == 201
    assert second.json()["history_id"] != first.json()["history_id"]

    recent = client.get("/api/v1/me/history?limit=2", headers=user_headers)
    assert recent.status_code == 200
    assert [item["history_id"] for item in recent.json()] == [
        second.json()["history_id"],
        first.json()["history_id"],
    ]
