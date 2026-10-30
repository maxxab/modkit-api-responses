import pytest

from modkit_api_responses import make_etag, matches_if_none_match


def test_final_bytes():
    assert make_etag(b"abc") == '"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"'
    assert make_etag("é".encode()) != make_etag(b"e")


@pytest.mark.parametrize("header", ['"a"', 'W/"a"', '"b", "a"', ', "a",,', "*"])
def test_match(header):
    assert matches_if_none_match(header, '"a"')


def test_tag_grammar():
    assert matches_if_none_match('"a,b"', '"a,b"')
    assert matches_if_none_match('""', '""')
    assert matches_if_none_match('"a\\b"', '"a\\b"')
    assert not matches_if_none_match("*", '"a"', representation_exists=False)
    assert not matches_if_none_match('"A"', '"a"')


@pytest.mark.parametrize(
    "header", [None, "", ",,", '*, "a"', '"a", *', 'w/"a"', "a", '"a", garbage', '"a"\r\n', '"unterminated', '"a" "b"']
)
def test_malformed_or_absent(header):
    assert not matches_if_none_match(header, '"a"')


def test_bounds():
    with pytest.raises(ValueError):
        matches_if_none_match('"abc"', '"abc"', max_header_bytes=4)
    with pytest.raises(ValueError):
        matches_if_none_match('"a", "b"', '"a"', max_tags=1)
    with pytest.raises(ValueError):
        matches_if_none_match('"a"', '"a"', max_tags=0)


def test_oversized_header_rejected_before_encoding():
    class Header(str):
        def encode(self, *args, **kwargs):
            raise AssertionError("oversized header must not allocate encoded copy")

    with pytest.raises(ValueError):
        matches_if_none_match(Header("x" * 8193), '"a"')
