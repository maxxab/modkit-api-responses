import pytest

from modkit_api_responses import EnvelopeConfig, build_meta, failure, strip_fields, success, unwrap_data


def test_envelope_shapes_and_ownership():
    cfg = EnvelopeConfig(data_key="value", error_key="problem", meta_key="info")
    data = {"x": []}
    result = success(data, config=cfg)
    assert result == {"value": data, "info": {}}
    assert result["value"] is data
    assert failure("MISSING", "Missing", config=cfg) == {
        "problem": {"code": "MISSING", "message": "Missing", "details": {}},
        "info": {},
    }
    marker = object()
    assert success(marker)["data"] is marker


@pytest.mark.parametrize("kwargs", [{"data_key": ""}, {"data_key": "meta"}, {"meta_key": 4}])
def test_bad_config(kwargs):
    with pytest.raises(ValueError):
        EnvelopeConfig(**kwargs)


def test_meta():
    base = {"contract": "my-app"}
    assert build_meta(base=base, extra={"count": 3, "absent": None}) == {"contract": "my-app", "count": 3}
    assert base == {"contract": "my-app"}
    with pytest.raises(ValueError):
        build_meta(base=base, extra={"contract": "override"})


def test_transforms():
    data = {"data": {"public": 1, "secret": "s", "nested": [{"secret": "s", "ok": True}]}}
    assert strip_fields(unwrap_data(data), names={"secret"}) == {"public": 1, "nested": [{"ok": True}]}
    assert "secret" in data["data"]
    assert unwrap_data({"data": 1, "other": 2}) == {"data": 1, "other": 2}
    assert unwrap_data({"value": 3}, data_key="value") == 3


def test_transform_bounds_and_hostile_objects():
    class Hostile:
        def __str__(self):
            raise AssertionError("must not stringify")

        __repr__ = __str__

    cycle = []
    cycle.append(cycle)
    for data in (cycle, {Hostile(): 1}, Hostile(), float("nan")):
        with pytest.raises(ValueError):
            strip_fields(data, names={"secret"})
    with pytest.raises(ValueError):
        strip_fields([[1]], names=[], max_depth=1)
    with pytest.raises(ValueError):
        strip_fields([1, 2], names=[], max_items=2)
