import binascii
from typing import List

from graphviz import Digraph
from hexbytes import HexBytes

from .utils import Node, decode_node, node_key, store_prefix


def label(node: Node):
    s = binascii.hexlify(node.key).decode()
    if len(s) > 10:
        s = s[:4] + "..." + s[-4:]
    s += f"({node.version})"
    if node.is_leaf():
        s += f"\nvalue len: {len(node.value)}"
    return s


def visualize_iavl(db, store: str, root_hash: bytes, version: int) -> Digraph:
    g = Digraph(comment="IAVL Tree")
    prefix = store_prefix(store)

    def get_node(hash: bytes) -> Node:
        n, _ = decode_node(db.get(prefix + node_key(hash)))
        return n

    def vis_node(hash: bytes, n: Node):
        style = "solid" if n.version == version else "filled"
        g.node(HexBytes(hash).hex(), label=label(node), style=style)

    stack: List[bytes] = [root_hash]
    while stack:
        hash = stack.pop()
        node = get_node(hash)

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
    return g
