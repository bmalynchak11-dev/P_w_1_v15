def subset_errors(actual, expected, path=""):
    """Порівнює expected як підмножину actual (словники — за ключами, списки й скаляри — точно)."""
    errs = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: очікувано словник, отримано {actual!r}"]
        for k, v in expected.items():
            if k not in actual:
                errs.append(f"{path}.{k}: немає в {sorted(actual)}")
            else:
                errs += subset_errors(actual[k], v, f"{path}.{k}")
    elif isinstance(expected, list) and expected and all(isinstance(x, dict) for x in expected):
        if not isinstance(actual, list) or len(actual) != len(expected):
            errs.append(f"{path}: очікувано {len(expected)} елементів, отримано {actual!r}")
        else:
            for i, (a, e) in enumerate(zip(actual, expected)):
                errs += subset_errors(a, e, f"{path}[{i}]")
    elif expected is None and actual in (None, False):
        pass
    elif actual != expected:
        errs.append(f"{path}: очікувано {expected!r}, отримано {actual!r}")
    return errs
