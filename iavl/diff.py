"""
tree diff algorithm between two versions
"""
from .iavl import NodeDB


class Layer:
    """
    Represent one layer of nodes at the same height

    pending_nodes: because one of the children's height could be height-2, need to keep
    it in the pending list temporarily.
    """

    def __init__(self, nodes, pending_nodes):
        """
        Contract:
        - nodes are not empty
        - pending_nodes are at one layer below nodes
        """
        self.height = nodes[0].height
        self.nodes = nodes
        self.pending_nodes = pending_nodes

    @classmethod
    def root(cls, root):
        return cls([root], [])

    def next_layer(self, ndb):
        """
        travel to next layer
        """
        assert self.height > 0
        nodes = []
        pending_nodes = []
        for node in self.nodes:
            left = ndb.get(node.left_node_ref)
            if left.height == self.height - 1:
                nodes.append(left)
            else:
                pending_nodes.append(left)

            right = ndb.get(node.right_node_ref)
            if right.height == self.height - 1:
                nodes.append(right)
            else:
                pending_nodes.append(right)

        self.height -= 1

        # merge sorted lists
        self.nodes = nodes
        self.nodes += self.pending_nodes
        self.nodes.sort(key=lambda n: n.key)
        self.pending_nodes = pending_nodes


def diff_sorted(nodes1, nodes2):
    """
    Contract: input list is sorted by node.key
    return: (common, orphaned, new)
    """
    i1 = i2 = 0
    common = []
    orphaned = []
    new = []
    while True:
        if i1 > len(nodes1) - 1:
            new += nodes2[i2:]
            break
        if i2 > len(nodes2) - 1:
            orphaned += nodes1[i1:]
            break
        k1 = nodes1[i1].key
        k2 = nodes2[i2].key
        if nodes1[i1].hash == nodes2[i2].hash:
            common.append(nodes1[i1])
            i1 += 1
            i2 += 1
        elif k1 == k2:
            # overriden by same key
            orphaned.append(nodes1[i1])
            new.append(nodes2[i2])
            i1 += 1
            i2 += 1
        elif k1 < k2:
            # proceed to next node in nodes1 until catch up with nodes2
            orphaned.append(nodes1[i1])
            i1 += 1
        else:
            # proceed to next node in nodes2 until catch up with nodes1
            new.append(nodes2[i2])
            i2 += 1
    return common, orphaned, new


def diff_tree(ndb: NodeDB, root1: int, root2: int):
    """
    diff two versions of the iavl tree.
    yields (orphaned, new)
    """
    l1 = Layer.root(root1)
    l2 = Layer.root(root2)

    while l1.height > l2.height:
        yield l1.nodes, []
        l1.next_layer(ndb)

    while l2.height > l1.height:
        yield [], l2.nodes
        l2.next_layer(ndb)

    while True:
        # l1 l2 at the same height now
        _, orphaned, new = diff_sorted(l1.nodes, l2.nodes)
        yield orphaned, new

        if l1.height == 0:
            break

        # don't visit the common sub-trees
        l1.nodes = orphaned
        l2.nodes = new

        l1.next_layer(ndb)
        l2.next_layer(ndb)
