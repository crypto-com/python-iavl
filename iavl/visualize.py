import binascii
from typing import List, Optional

from graphviz import Digraph
from hexbytes import HexBytes

from .iavl import NodeDB
from .utils import PersistedNode, get_node


def label(node: PersistedNode):
    s = binascii.hexlify(node.key).decode()
    if len(s) > 10:
        s = s[:4] + "..." + s[-4:]
    s = f"{node.version}: {s}"
    if node.is_leaf():
        s += f"\nvalue len: {len(node.value)}"
    else:
        s += f"\nheight: {node.height}"
    return s


def visualize_iavl(
    db, root_hash: bytes, version: int, root_hash2=None, store: Optional[str] = None,
) -> Digraph:
    g = Digraph(comment="IAVL Tree")

    def vis_node(hash: bytes, n: PersistedNode):
        style = "solid" if n.version == version else "filled"
        g.node(HexBytes(hash).hex(), label=label(n), style=style)

    if root_hash2 is not None:
        stack: List[bytes] = [root_hash2]
        while stack:
            hash = stack.pop()
            node = get_node(db, hash, store)

            vis_node(hash, node)

            if not node.is_leaf():
                stack.append(node.right_node_ref)
                stack.append(node.left_node_ref)

                g.edges(
                    [
                        (HexBytes(hash).hex(), HexBytes(node.right_node_ref).hex()),
                        (HexBytes(hash).hex(), HexBytes(node.left_node_ref).hex()),
                    ]
                )

    stack: List[bytes] = [root_hash]
    while stack:
        hash = stack.pop()
        node = get_node(db, hash, store)

        # don't duplicate nodes in compare mode
        if root_hash2 is None or node.version == version:
            vis_node(hash, node)

        if not node.is_leaf():
            stack.append(node.right_node_ref)
            stack.append(node.left_node_ref)

            # don't duplicate edges in compare mode
            if root_hash2 is None or node.version == version:
                g.edges(
                    [
                        (HexBytes(hash).hex(), HexBytes(node.right_node_ref).hex()),
                        (HexBytes(hash).hex(), HexBytes(node.left_node_ref).hex()),
                    ]
                )

    return g


def visualize_pruned_nodes(successor, hashes, pruned, ndb: NodeDB):
    g = Digraph(comment="IAVL Tree")

    def vis_node(n: PersistedNode):
        if n.version == successor:
            style = "solid"
        elif n.hash in pruned:
            style = "dotted,filled"
        else:
            style = "filled"
        g.node(HexBytes(n.hash).hex(), label=label(node), style=style)

    def vis_placeholder(hash: bytes):
        g.node(HexBytes(hash).hex(), label="", style="solid")

    nodes = [ndb.get(hash) for hash in hashes]
    nodes.sort(key=lambda n: n.version)
    for node in nodes:
        vis_node(node)
        if not node.is_leaf():
            if node.left_node_ref not in hashes:
                vis_placeholder(node.left_node_ref)
            if node.right_node_ref not in hashes:
                vis_placeholder(node.right_node_ref)
            g.edges(
                [
                    (HexBytes(node.hash).hex(), HexBytes(node.right_node_ref).hex()),
                    (HexBytes(node.hash).hex(), HexBytes(node.left_node_ref).hex()),
                ]
            )
    return g
