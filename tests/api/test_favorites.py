import app

def test_add_favorite_returns_ok(client):
    resp = client.post("/add_favorite", data={
        "channel_id": "12345",
        "channel_title": "Very Cool Channel"
    })
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["status"] == "ok"
    assert data["favorites"][1]["id"] == "12345" # index 0 is always dango's youtube lol
