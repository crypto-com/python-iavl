from iavl.utils import NODE_KEY_PREFIX, node_key_suffix, parse_node_key

def test_parse_key():
    v = 1234567890123456789
    n = 1
    suffix = node_key_suffix(v, n)
    assert len(suffix) == 12
    assert suffix == b'\x11"\x10\xf4}\xe9\x81\x15\x00\x00\x00\x01'
    assert parse_node_key(NODE_KEY_PREFIX + suffix) == (v, n)
