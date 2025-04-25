# tests/conftest.py
import sys, types, pytest

@pytest.fixture(scope="session", autouse=True)
def fasttext_stub():
    """
    Make a fake 'fasttext' that satisfies app.py during tests.
    Runs before collection because it's session+autouse.
    """
    if "fasttext" in sys.modules:          # real fasttext already imported?
        return                             # then model file must exist locally

    dummy = types.ModuleType("fasttext")

    class _DummyModel:
        def predict(self, text):
            return ["__label__en"], [0.99]

    def load_model(path):
        # Ignore 'path' and return lightweight stub
        return _DummyModel()

    dummy.load_model = load_model
    sys.modules["fasttext"] = dummy        # inject into import system
