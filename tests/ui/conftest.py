# tests/ui/conftest.py
import threading, socket, time
from pathlib import Path
from unittest.mock import MagicMock
import pytest

import pytest
from app import app as flask_app

PROJECT_DIR = Path(__file__).resolve().parents[2]
TEMPLATES = PROJECT_DIR / "templates"
STATIC    = PROJECT_DIR / "static"

def _free_port() -> int:
    s = socket.socket(); s.bind(("localhost", 0))
    port = s.getsockname()[1]; s.close(); return port

@pytest.fixture()
def live_server_url(monkeypatch):
    # ── 1. Stub the YouTube client ────────────────────────────────────────────
    dummy = MagicMock()

    # search().list(...).execute()
    # Already inside live_server_url(monkeypatch):

    dummy.search.return_value.list.return_value.execute.side_effect = (
        lambda **kw: {
            "items": [{
                "id": {"videoId": "video123"},
                "snippet": {
                    "channelId": "chan1",
                    "title": "Minecraft with friends – VTuber Special!"
                }
            }]
        }
    )


    # channels().list(...).execute()
    dummy.channels.return_value.list.return_value.execute.return_value = {
        "items": [{
            "id": "chan1",
            "snippet": {
                "title": "Demo Channel",
                "thumbnails": {"default": {"url": ""}}
            },
            "statistics": {"subscriberCount": 0}
        }]
    }

    monkeypatch.setattr("app.build", lambda *a, **k: dummy, raising=True)

    # ── 2. Real template / static folders  ────────────────────────────────────
    flask_app.template_folder = str(TEMPLATES)
    flask_app.static_folder   = str(STATIC)
    flask_app.jinja_loader.searchpath[:] = [str(TEMPLATES)]

    # ── 3. Config  ────────────────────────────────────────────────────────────
    flask_app.config.update(
        TESTING=True,
        FAVORITES_FILE=":memory:",   # no disk
        YT_API_KEY="dummy",
    )

    # ── 4. Start Flask  ───────────────────────────────────────────────────────
    port = _free_port()
    thread = threading.Thread(
        target=lambda: flask_app.run(port=port, use_reloader=False),
        daemon=True,
    )
    thread.start()
    time.sleep(1)

    yield f"http://localhost:{port}"

@pytest.fixture(scope="session")
def browser_context_args(tmp_path_factory):
    """
    This special fixture is read by pytest-playwright.
    Everything you return here is passed to browser.new_context(**kwargs).
    """
    video_dir = tmp_path_factory.mktemp("videos")    # e.g. …/pytest-of-gh/video0
    return {
        # Store .webm videos here
        "record_video_dir": str(video_dir),
        # Optional: fix resolution so clips aren’t huge
        "record_video_size": {"width": 1280, "height": 720},
    }

