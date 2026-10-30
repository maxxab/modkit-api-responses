import runpy
from pathlib import Path

import modkit_api_responses as api


def test_documented_public_api():
    for name in (
        "EnvelopeConfig",
        "success",
        "failure",
        "build_meta",
        "strip_fields",
        "unwrap_data",
        "make_etag",
        "matches_if_none_match",
        "ReadRepresentation",
        "CachePolicy",
        "ConditionalResponse",
        "conditional_response",
    ):
        assert name in api.__all__ and hasattr(api, name)


def test_unrelated_example():
    runpy.run_path(str(Path(__file__).parents[1] / "examples" / "sample_app.py"), run_name="__main__")
