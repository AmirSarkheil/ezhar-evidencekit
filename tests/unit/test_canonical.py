from evidencekit.canonical import manifest_digest


def test_digest_ignores_existing_self_digest() -> None:
    base = {"schema_version": "1.0", "value": {"b": 2, "a": 1}}
    first = manifest_digest(base)
    base["manifest_sha256"] = "0" * 64
    assert manifest_digest(base) == first


def test_digest_is_key_order_independent() -> None:
    left = {"a": 1, "b": {"x": 2, "y": 3}}
    right = {"b": {"y": 3, "x": 2}, "a": 1}
    assert manifest_digest(left) == manifest_digest(right)
