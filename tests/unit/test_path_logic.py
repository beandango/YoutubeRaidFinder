# tests/unit/test_path_logic.py
import importlib.util, sys, pathlib
from pathlib import Path

def test_base_dir_when_frozen(monkeypatch, tmp_path):
    # Pretend we're inside a PyInstaller --onedir bundle
    fake_exe = tmp_path / "dist" / "YTRaidFinder" / "YTRaidFinder.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_text("")                       # empty placeholder file

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    # ---- import a *new* copy of app.py under a throw-away name ----
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    spec = importlib.util.spec_from_file_location("app_frozen_test", app_path)
    app_frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_frozen)          # executes top-level code

    assert app_frozen.base_dir == fake_exe.parent
