from app import clean_title_for_detection  

def test_strips_brackets_hashtags_and_brand_names():
    raw = "【LIVE】Epic #Minecraft Stream [this is a cry for help]"
    assert clean_title_for_detection(raw) == "epic stream"
