import matplotlib.pyplot as plt
import math
import networkx
import sys
import enum
import string
import itertools
from dataclasses import dataclass
from typing import Any, Iterable, Dict, Set, List, Tuple, Optional, FrozenSet


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
    ignore: bool = False


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

    def __setitem__(self, key: Any, value: Any) -> None:
        if not isinstance(key, PathCache.Key):
            raise ValueError('Key must be of type PathCache.Key')
        elif not isinstance(value, PathCache.Entry):
            raise ValueError('Value must be of type PathCache.Entry')

        super().__setitem__(key, value)


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


# Convert the input string to one that can be used in part 2
def convert_input_to_part2(input_lines: List[str]) -> List[str]:
    player_line_index, player_line = next((i, line) for i, line in enumerate(input_lines) if '@' in line)
    player_index = player_line.index('@')
    res = input_lines.copy()
    # Place player chars at the positions of the robots
    for d_line, d_index in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        new_index = player_index + d_index
        line_to_update = res[player_line_index + d_line]
        res[player_line_index + d_line] = line_to_update[:new_index] + '@' + line_to_update[new_index + 1:]

    # Fill in the entire horizontal with wall chars
    res[player_line_index] = '#' * len(player_line)
    # Fill in the "plus sign" of wall chars
    for d_line, d_index in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        new_index = player_index + d_index
        line_to_update = res[player_line_index + d_line]
        res[player_line_index + d_line] = line_to_update[:new_index] + '#' + line_to_update[new_index + 1:]

    return res


# Reduce the graph to remove the open nodes
def make_reduced_graph(graph: networkx.Graph) -> networkx.Graph:
    interactive_nodes = {node: data for node, data in graph.nodes.data('info') if data.node_type != NodeType.OPEN}
    reduced_graph = networkx.Graph()
    for node1, node2 in itertools.combinations(interactive_nodes.items(), 2):
        pos1, info1 = node1
        pos2, info2 = node2
        reduced_graph.add_node(pos1, info=info1)
        reduced_graph.add_node(pos2, info=info2)

        try:
            path = networkx.shortest_path(graph, pos1, pos2)
        except networkx.NetworkXNoPath:
            continue
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
        elif (node_info.node_type == NodeType.DOOR and not node_info.ignore
              and node_info.char.lower() not in all_collected_keys):
            return False

    return True


def find_shortest_path_cost(
        graph: networkx.Graph,
        starting_node: Optional[Tuple[int, int]] = None,
        visited: Optional[Set[str]] = None,
        path_cache: Optional[PathCache] = None,
        shortest_paths: Optional[Dict[Tuple[int, int], Tuple[int, int]]] = None) -> int:
    if starting_node is None:
        # Start at the player node if no starting node is spcified
        starting_node = next(node for node, data in graph.nodes.data('info') if data.node_type == NodeType.PLAYER)
    if visited is None:
        visited = set((starting_node,))
    if path_cache is None:
        path_cache = PathCache()
    if shortest_paths is None:
        shortest_paths = networkx.shortest_path(graph)

    # If we have already visited all nodes, we're done, and there's no more cost to it.
    key_nodes = set(node for node in graph.nodes
                    if graph.nodes[node]['info'].char.lower() == graph.nodes[node]['info'].char
                    and graph.nodes[node]['info'].char.isalpha())
    if visited == key_nodes:
        return 0

    collected_keys = set(graph.nodes[node]['info'].char for node in visited
                         if graph.nodes[node]['info'].char.lower() == graph.nodes[node]['info'].char)

    cache_key = PathCache.Key.make_from_iterable(collected_keys, starting_node)
    cache_entry = path_cache.get(cache_key)
    if cache_entry is not None:
        return cache_entry.cost

    could_check_path = False
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
        path_cost = find_shortest_path_cost(graph, destination, visited_copy, path_cache, shortest_paths)
        cost += path_cost
        if cost < best_cost:
            best_cost = cost

    # If the loop didn't run, none of the paths are elgible for use.
    if not could_check_path:
        path_cache[cache_key] = PathCache.Entry(0)
        return 0

    path_cache[cache_key] = PathCache.Entry(best_cost)

    return best_cost


# Mark any doors within the graph that don't have paths as ignored
def mark_unopenable_doors_as_ignored(graph: networkx.Graph):
    for node, data in graph.nodes.data('info'):
        have_key = next((True for _, candidate_data in graph.nodes.data('info')
                         if candidate_data.char == data.char.lower()),
                        False)
        if not have_key:
            data.ignore = True


def part1(graph: networkx.Graph) -> int:
    reduced_graph = make_reduced_graph(graph)
    cost = find_shortest_path_cost(reduced_graph)

    return cost


def part2(graph: networkx.Graph) -> int:
    reduced_graph = make_reduced_graph(graph)
    subgraphs = [reduced_graph.subgraph(component) for component in networkx.connected_components(reduced_graph)]
    for subgraph in subgraphs:
        # Because timing doesn't matter, we can assume that another robot will eventually collect a key within our path
        # Therefore, we can just ignore all of the doors that we can't open within our path
        mark_unopenable_doors_as_ignored(subgraph)

    return sum(find_shortest_path_cost(subgraph) for subgraph in subgraphs)


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

    part1_graph = make_graph_from_input(input_lines)
    print(part1(part1_graph))

    part2_input = input_lines
    num_players = sum(line.count('@') for line in input_lines)
    if num_players == 1:
        part2_input = convert_input_to_part2(input_lines)

    part2_graph = make_graph_from_input(part2_input)
    print(part2(part2_graph))
