from app import contains_any_of                   

def test_basic_matches():
    assert contains_any_of(["cat", "dog"], "Cute Dogs")
    assert not contains_any_of(["bird"], "Cute Dogs")
