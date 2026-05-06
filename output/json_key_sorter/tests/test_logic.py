from src.logic import sort_dict_recursive

def test_sort_dict_recursive_flat():
    d = {"c": 3, "a": 1, "b": 2}
    sorted_d = sort_dict_recursive(d)
    assert list(sorted_d.keys()) == ["a", "b", "c"]

def test_sort_dict_recursive_nested():
    d = {"b": {"y": 2, "x": 1}, "a": 0}
    sorted_d = sort_dict_recursive(d)
    assert list(sorted_d.keys()) == ["a", "b"]
    assert list(sorted_d["b"].keys()) == ["x", "y"]

def test_sort_dict_recursive_with_list():
    d = {"b": [{"z": 2, "a": 1}], "a": 0}
    sorted_d = sort_dict_recursive(d)
    assert list(sorted_d.keys()) == ["a", "b"]
    assert list(sorted_d["b"][0].keys()) == ["a", "z"]

def test_sort_dict_recursive_non_dict():
    assert sort_dict_recursive("string") == "string"
    assert sort_dict_recursive(123) == 123
    assert sort_dict_recursive(["b", "a"]) == ["b", "a"]
