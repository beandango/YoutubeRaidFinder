import importlib, sys, types, pathlib, importlib.util

def test_base_dir_when_frozen(monkeypatch):
    # Pretend we are inside a PyInstaller bundle
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable",
        str(pathlib.Path(r"C:\dist\YTRaidFinder\YTRaidFinder.exe")))

    # Reload the module so top-level code re-runs
    import app as app_module
    importlib.reload(app_module)

    expected = pathlib.Path(r"C:\dist\YTRaidFinder")
    assert app_module.base_dir == expected
