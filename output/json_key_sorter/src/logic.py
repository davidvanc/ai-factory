from typing import Any

def sort_dict_recursive(obj: Any) -> Any:
    """
    Recursively sorts the keys of a dictionary.
    Also iterates through lists to sort nested dictionaries.
    """
    if isinstance(obj, dict):
        return {k: sort_dict_recursive(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [sort_dict_recursive(item) for item in obj]
    else:
        return obj
