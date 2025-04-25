import app

def test_search_returns_results(client, youtube_stub):
    resp = client.post("/", data={
        "search_terms": "minecraft",
        "sort_by": "viewers",
        "sort_order": "asc"
    })
    assert resp.status_code == 200
    # HTML response contains the mock video title
    assert b"Mock Live" in resp.data
