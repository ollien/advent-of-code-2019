import collections
import sys
from dataclasses import dataclass
from typing import List, Dict

ROOT_NODE = 'COM'


@dataclass
class Node:
    name: str
    depth: int
    children: List['Node']


# Make a tree of orbits from the input dict, returning the root node (COM)
def make_orbit_tree(raw_orbits: Dict[str, List[str]]) -> Node:
    def add_item(node: Node, new_child: str):
        child_node = Node(new_child, node.depth + 1, [])
        node.children.append(child_node)
        for subchild in raw_orbits[new_child]:
            add_item(child_node, subchild)

    root = Node(ROOT_NODE, 0, [])
    add_item(root, raw_orbits[ROOT_NODE][0])

    return root


def part1(root: Node) -> int:
    orbits = 0

    # Go over all of the children, and add up their depths
    def get_orbit_count(node: Node):
        nonlocal orbits
        orbits += node.depth
        for child in node.children:
            get_orbit_count(child)

    get_orbit_count(root)
    return orbits


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = [line.rstrip() for line in f]

    raw_orbits = collections.defaultdict(list)
    for item in inputs:
        orbiting, orbiter = item.split(")")
        raw_orbits[orbiting].append(orbiter)

    root = make_orbit_tree(raw_orbits)
    print(part1(root))
