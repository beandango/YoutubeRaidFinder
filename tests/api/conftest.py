import pytest
from app import app as flask_app 
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]          # …/YoutubeRaidFinder
TEMPLATES   = PROJECT_DIR / "templates"
STATIC      = PROJECT_DIR / "static"

@pytest.fixture()
def client():
    flask_app.template_folder = str(PROJECT_DIR / "templates")
    flask_app.static_folder   = str(PROJECT_DIR / "static")
    flask_app.jinja_loader.searchpath[:] = [str(TEMPLATES)]


    flask_app.config.update(
        TESTING=True,
        FAVORITES_FILE=":memory:",   # don’t touch disk
        YT_API_KEY="dummy"
    )
    with flask_app.test_client() as c:
        yield c

@pytest.fixture()
def youtube_stub(mocker):
    """Patch app.build() so route handlers use fake data."""
    fake = mocker.MagicMock()
    sample_search = {
        "items": [{
            "id": {"videoId": "vid1"},
            "snippet": {"channelId": "chan1", "title": "Mock Live"}
        }]
    }
    fake.search.return_value.list.return_value.execute.return_value = sample_search
    mocker.patch("app.build", return_value=fake)
    return fake