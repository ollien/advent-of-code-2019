import matplotlib.pyplot as plt
import math
import networkx
import sys
import enum
import string
import itertools
from dataclasses import dataclass
from typing import Any, Iterable, Set, List, Tuple, Optional, FrozenSet


class NodeType(enum.Enum):
    WALL = 0
    OPEN = 1
    PLAYER = 2
    KEY = 3
    DOOR = 4

    @staticmethod
    def make_from_input_char(char: str):
        CHAR_MAP = {
            '#': NodeType.WALL,
            '.': NodeType.OPEN,
            '@': NodeType.PLAYER,
        }

        node_type = CHAR_MAP.get(char)
        if node_type is None:
            if char in string.ascii_lowercase:
                node_type = NodeType.KEY
            elif char in string.ascii_uppercase:
                node_type = NodeType.DOOR
            else:
                raise ValueError(f"Invalid NodeType char '{char}'' ")

        return node_type


@dataclass
class Node:
    node_type: NodeType
    char: str


class PathCache(dict):
    @dataclass(frozen=True, eq=True)
    class Key:
        collected_keys: FrozenSet[str]
        src: Tuple[int, int]

        @classmethod
        def make_from_iterable(cls, collected_keys: Iterable[str], src: Tuple[int, int]) -> None:
            return cls(frozenset(collected_keys), src)

    @dataclass
    class Entry:
        cost: int
        path: List[Tuple[int, int]]


# Make a graph from the maze input
def make_graph_from_input(input_lines: List[str]) -> networkx.Graph:
    def connect_adjacent_nodes(node_pos: Tuple[int, int]) -> None:
        for d_row, d_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            row, col = node_pos
            row += d_row
            col += d_col
            if (row, col) in graph.nodes:
                graph.add_edge(node_pos, (row, col))

    graph = networkx.Graph()
    for row, line in enumerate(input_lines):
        for col, char in enumerate(line):
            node_type = NodeType.make_from_input_char(char)
            if node_type == NodeType.WALL:
                continue

            node = Node(node_type, char)
            graph.add_node((row, col), info=node)

    for node in graph.nodes:
        connect_adjacent_nodes(node)

    return graph


def make_reduced_graph(graph: networkx.Graph) -> networkx.Graph:
    interactive_nodes = {node: data for node, data in graph.nodes.data('info') if data.node_type != NodeType.OPEN}
    reduced_graph = networkx.Graph()
    for node1, node2 in itertools.combinations(interactive_nodes.items(), 2):
        pos1, info1 = node1
        pos2, info2 = node2
        reduced_graph.add_node(pos1, info=info1)
        reduced_graph.add_node(pos2, info=info2)

        path = networkx.shortest_path(graph, pos1, pos2)
        # Check if any nodes are interactive and within the path.
        # We don't want to make an edge between node1 and node2 if there are.
        intermediate_interactive_nodes = set(path[1:-1]).intersection(set(interactive_nodes.keys()))
        if len(intermediate_interactive_nodes) > 0:
            continue

        reduced_graph.add_edge(pos1, pos2, distance=len(path)-1)

    return reduced_graph


# Check if we can "clear" a whole path, which is determined by if all keys come before their doors
def path_is_clearable(graph: networkx.Graph, path: Iterable[Tuple[int, int]], collected_keys: Set[str]) -> bool:
    all_collected_keys = collected_keys.copy()
    for node in path:
        node_info = graph.nodes[node]['info']
        if node_info.node_type == NodeType.KEY:
            all_collected_keys.add(node_info.char)
        elif node_info.node_type == NodeType.DOOR and node_info.char.lower() not in all_collected_keys:
            return False

    return True


def find_shortest_path_cost(
        graph: networkx.Graph,
        starting_node: Optional[Tuple[int, int]] = None,
        visited: Optional[Set[str]] = None,
        path_cache: PathCache = None,
        depth: int = 0, prev_dest: str = None) -> Tuple[int, List[Tuple[int, int]]]:
    if starting_node is None:
        # Start at the player node if no starting node is spcified
        starting_node = next(node for node, data in graph.nodes.data('info') if data.node_type == NodeType.PLAYER)
    if visited is None:
        visited = set((starting_node,))
    if path_cache is None:
        path_cache = PathCache()

    # If we have already visited all nodes, we're done, and there's no more cost to it.
    key_nodes = set(node for node in graph.nodes
                    if graph.nodes[node]['info'].char.lower() == graph.nodes[node]['info'].char
                    and graph.nodes[node]['info'].char.isalpha())
    if visited == key_nodes:
        return 0, []

    shortest_paths = networkx.shortest_path(graph)
    collected_keys = set(graph.nodes[node]['info'].char for node in visited
                         if graph.nodes[node]['info'].char.lower() == graph.nodes[node]['info'].char)

    cache_key = PathCache.Key.make_from_iterable(collected_keys, starting_node)
    try:
        cache_entry = path_cache[cache_key]
        return (cache_entry.cost, cache_entry.path)
    except KeyError:
        # If we don't have a cache entry, keep going.
        # We need to do this instead of .get because otherwise __missing__ won't be called.
        pass

    could_check_path = False
    best_path = None
    best_cost = math.inf
    for destination in key_nodes:
        path = shortest_paths[starting_node][destination]
        if destination in visited:
            continue
        elif not path_is_clearable(graph, path, collected_keys):
            continue

        could_check_path = True
        visited_copy = visited.copy()
        visited_copy.update(path)
        cost = sum(graph.edges[(node1, node2)]['distance'] for node1, node2 in zip(path, path[1:]))
        path_cost, rest_of_path = find_shortest_path_cost(graph, destination, visited_copy, path_cache)
        cost += path_cost
        full_path = path + rest_of_path[1:]
        if cost < best_cost:
            best_path = full_path
            best_cost = cost

    # If the loop didn't run, none of the paths are elgible for use.
    if not could_check_path:
        path_cache[cache_key] = PathCache.Entry(0, [])
        return 0, []

    path_cache[cache_key] = PathCache.Entry(best_cost, best_path)

    return (best_cost, best_path)


def part1(graph: networkx.Graph) -> int:
    reduced_graph = make_reduced_graph(graph)
    cost, _ = find_shortest_path_cost(reduced_graph)

    return cost


# A debug function used to print the path as letters
def print_readable_path(graph: networkx.Graph, path: Iterable[Tuple[int, int]]) -> None:
    print([graph.nodes[node]['info'].char for node in path])


# A debug function used to visualize the drawn graph
def draw_graph(graph: networkx.Graph) -> None:
    positions = networkx.spring_layout(graph)
    networkx.draw_networkx_nodes(graph, positions)
    networkx.draw_networkx_edges(graph, positions)
    networkx.draw_networkx_labels(graph, positions, {node: data.char for node, data in graph.nodes.data('info')})
    networkx.draw_networkx_edge_labels(graph, positions, {(node1, node2): data for node1, node2, data in graph.edges.data('distance')})
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input_lines = [line.rstrip('\n') for line in f.readlines()]

    graph = make_graph_from_input(input_lines)
    print(part1(graph))
