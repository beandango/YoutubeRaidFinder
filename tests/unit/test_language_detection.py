# tests/unit/test_language_detection.py
import pytest
from app import clean_title_for_detection, model   # model is fasttext.FastText

def test_language_filter_english(mocker):
    # Arrange: stub model.predict to return English
    mocker.patch.object(model, "predict",
        return_value=(["__label__en"], [0.97])
    )

    text = "[Minecraft] chicken jocky!!! (send help)"
    cleaned = clean_title_for_detection(text)
    label, conf = model.predict(cleaned)
    assert label[0] == "__label__en"
    assert conf[0] > 0.9

def test_language_filter_japanese(mocker):
    mocker.patch.object(model, "predict",
        return_value=(["__label__jp"], [0.97])
    )

    text = "[Minecraft] チケンジョッキー (助けて)"
    cleaned = clean_title_for_detection(text)
    label, conf = model.predict(cleaned)
    assert label[0] == "__label__jp"
    assert conf[0] > 0.9
