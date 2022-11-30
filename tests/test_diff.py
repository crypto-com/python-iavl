from typing import NamedTuple

import rocksdb
from iavl.diff import diff_sorted, diff_tree
from iavl.iavl import NodeDB, Tree


def diff_tree_collect(ndb: NodeDB, v1: int, v2: int):
    orphaned = []
    new = []

    for o, n in diff_tree(ndb, ndb.get_root_node(v1), ndb.get_root_node(v2)):
        orphaned += o
        new += n

    return orphaned, new


def test_diff_sorted():
    class MockNode(NamedTuple):
        key: int
        hash: int

    def m(*xs):
        return [MockNode(x, x) for x in xs]

    assert (m(3, 4), m(1, 2), m(5, 6)) == diff_sorted(m(1, 2, 3, 4), m(3, 4, 5, 6))
    assert (m(3, 4), m(1, 2, 7, 8), m(5, 6)) == diff_sorted(
        m(1, 2, 3, 4, 7, 8), m(3, 4, 5, 6)
    )


def test_diff_tree(tmp_path):
    dbpath = tmp_path / "basic_ops"
    dbpath.mkdir()
    print("db", dbpath)
    kvdb = rocksdb.DB(str(dbpath), rocksdb.Options(create_if_missing=True))
    db = NodeDB(kvdb)

    tree = Tree(db, 0)
    assert not tree.set(b"hello", b"world")
    tree.save_version()

    tree = Tree(db, 1)
    assert tree.set(b"hello", b"world1")
    assert not tree.set(b"hello1", b"world1")
    tree.save_version()

    orphaned, new = diff_tree_collect(db, 1, 2)
    assert len(orphaned) == 1
    assert len(new) == 3
