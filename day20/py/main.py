import networkx
import itertools
import sys
from typing import List, Tuple

START_NODE_LABEL = 'AA'
END_NODE_LABEL = 'ZZ'


# Connect any adjacent nodes in the maze
def connect_adjacent_nodes(graph: networkx.Graph):
    for node in graph.nodes:
        row, col = node
        for d_row, d_col in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            neighbor_candidate = (row + d_row, col + d_col)
            if neighbor_candidate in graph.nodes:
                graph.add_edge(node, neighbor_candidate)


# Check if the node is on the outer edge
def is_outer_node(graph: networkx.Graph, node: Tuple[int, int]) -> bool:
    min_row = min(graph.nodes, key=lambda x: x[0])[0]
    max_row = max(graph.nodes, key=lambda x: x[0])[0]
    min_col = min(graph.nodes, key=lambda x: x[1])[1]
    max_col = max(graph.nodes, key=lambda x: x[1])[1]

    return node[0] in (min_row, max_col) or node[1] in (min_col, max_col)


# Add an edge between each portal of the same label
def add_portal_edges(graph: networkx.Graph, input_lines: List[str]):
    known_portals = {}
    for node in graph.nodes:
        row, col = node
        for d_row, d_col in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            portal_id = input_lines[row + d_row][col + d_col] + input_lines[row + 2 * d_row][col + 2 * d_col]
            if not portal_id.isalpha():
                continue

            # We will read nodes backwards if we are going in a negative direction (i.e. up or to the left)
            if d_row < 0 or d_col < 0:
                portal_id = ''.join(reversed(portal_id))

            other_end = known_portals.get(portal_id, None)
            if other_end is None:
                known_portals[portal_id] = node
                networkx.set_node_attributes(graph, {node: portal_id}, 'label')
                networkx.set_node_attributes(graph, {node: is_outer_node(graph, node)}, 'outer')
            else:
                graph.add_edge(node, other_end)
                networkx.set_node_attributes(graph, {node: portal_id}, 'label')
                networkx.set_node_attributes(graph, {node: is_outer_node(graph, node)}, 'outer')


# Make the maze from the given input
def make_graph_from_input_lines(input_lines: List[str]) -> networkx.Graph:
    OPEN_CHAR = '.'
    graph = networkx.Graph()
    for row, line in enumerate(input_lines):
        for col, char in enumerate(line):
            if char != OPEN_CHAR:
                continue
            graph.add_node((row, col))

    connect_adjacent_nodes(graph)
    add_portal_edges(graph, input_lines)

    return reduce_graph_to_labelled_nodes(graph)


def reduce_graph_to_labelled_nodes(graph: networkx.Graph) -> networkx.Graph:
    reduced_graph = networkx.subgraph(graph, (node for node, label in graph.nodes.data('label') if label is not None))
    reduced_graph = reduced_graph.copy()
    for node1, node2 in itertools.combinations(reduced_graph.nodes, 2):
        path = networkx.shortest_path(graph, node1, node2)
        distance = len(path) - 1
        reduced_graph.add_edge(node1, node2, distance=distance)

    return reduced_graph


def part1(graph: networkx.Graph) -> int:
    start_node = next(node for node, label in graph.nodes.data('label') if label == 'AA')
    end_node = next(node for node, label in graph.nodes.data('label') if label == 'ZZ')
    path = networkx.shortest_path(graph, start_node, end_node)

    return sum(graph.edges[(node1, node2)]['distance'] for node1, node2 in zip(path, path[1:]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input_lines = [line.rstrip('\n') for line in f.readlines()]

    graph = make_graph_from_input_lines(input_lines)
    print(part1(graph))
