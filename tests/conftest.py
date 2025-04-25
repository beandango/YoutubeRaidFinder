# tests/conftest.py
import sys, types

# If the real package isn't present, create a dummy module *now*
if "fasttext" not in sys.modules:
    dummy = types.ModuleType("fasttext")

    class _DummyModel:
        def predict(self, text):
            # Always return English with high confidence
            return ["__label__en"], [0.99]

    def load_model(path):
        return _DummyModel()

    dummy.load_model = load_model
    sys.modules["fasttext"] = dummy
