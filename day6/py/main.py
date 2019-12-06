import collections
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import math

ROOT_NODE = 'COM'
YOU_NODE = 'YOU'
TARGET_NODE = 'SAN'


@dataclass
class Node:
    name: str
    depth: int
    children: List['Node']
    parent: 'Node'

    # Apply a function to this node and all nodes underneath it
    def apply_to_tree(self, f: Callable[['Node'], None]) -> None:
        f(self)
        for child in self.children:
            child.apply_to_tree(f)

    # Search for a node in the tree consisting of this node and all nodes underneath it
    def find(self, target_name: str) -> Optional['Node']:
        # Find the target in the child list
        for child in self.children:
            if child.name == target_name:
                return child

        for child in self.children:
            res = child.find(target_name)
            if res is not None:
                return res
        else:
            return None


# Make a tree of orbits from the input dict, returning the root node (COM)
def make_orbit_tree(raw_orbits: Dict[str, List[str]]) -> Node:
    def add_item(node: Node, new_child: str):
        child_node = Node(name=new_child, depth=node.depth + 1, children=[], parent=node)
        node.children.append(child_node)
        # Process the orbits of the nodes that are orbiting this one
        for subchild in raw_orbits[new_child]:
            add_item(child_node, subchild)

    root = Node(name=ROOT_NODE, depth=0, children=[], parent=None)
    # Start with the root, adding its only child
    add_item(root, raw_orbits[ROOT_NODE][0])

    return root


def part1(root: Node) -> int:
    orbits = 0

    # Go over all of the children, and add up their depths
    def add_depth(node: Node):
        nonlocal orbits
        orbits += node.depth

    root.apply_to_tree(add_depth)

    return orbits


# Search the tree using Dikjstra's algorithm
def part2(root: Node):
    # Get all of the nodes in the tree as a dict
    unvisited = {}

    def collect_node(node):
        nonlocal unvisited
        unvisited[node.name] = node

    root.apply_to_tree(collect_node)
    # Get our source and target: the parent of the YOU and SAN nodes
    cursor_node = root.find(YOU_NODE).parent
    target_node = root.find(TARGET_NODE).parent
    if cursor_node is None or target_node is None:
        raise ValueError("Could not find source or destination in graph")

    # Run Dikjstra's algorithm
    # Using a default dict, we set all initial distances to infinity
    distances = collections.defaultdict(lambda: math.inf)
    distances[cursor_node.name] = 0
    while len(unvisited) > 0:
        neighbors = cursor_node.children + ([cursor_node.parent] if cursor_node.parent is not None else [])

        for child in neighbors:
            if child.name not in unvisited:
                continue

            # The distance to all nodes is 1
            new_distance = distances[cursor_node.name] + 1
            if new_distance < distances[child.name]:
                distances[child.name] = new_distance

        del unvisited[cursor_node.name]
        # If we've used our target, we're done.
        if cursor_node == target_node:
            break

        # Get the next cursor
        try:
            new_cursor_name = min(unvisited, key=lambda name: distances[name])
            cursor_node = unvisited[new_cursor_name]
        except ValueError:
            # There are no nodes left to check
            break

    return distances[target_node.name]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = [line.rstrip() for line in f]

    # Make a dict of planet => planets that are orbiting it
    raw_orbits = collections.defaultdict(list)
    for item in inputs:
        orbiting, orbiter = item.split(")")
        raw_orbits[orbiting].append(orbiter)

    root = make_orbit_tree(raw_orbits)
    print(part1(root))
    print(part2(root))
