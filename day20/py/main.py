import networkx
import matplotlib.pyplot as plt
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

    return node[0] in (min_row, max_row) or node[1] in (min_col, max_col)


def label_portal_nodes(graph: networkx.Graph, input_lines: List[str]):
    for node in graph.nodes:
        row, col = node
        for d_row, d_col in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            portal_id = input_lines[row + d_row][col + d_col] + input_lines[row + 2 * d_row][col + 2 * d_col]
            if not portal_id.isalpha():
                continue

            # We will read nodes backwards if we are going in a negative direction (i.e. up or to the left)
            if d_row < 0 or d_col < 0:
                portal_id = ''.join(reversed(portal_id))

            networkx.set_node_attributes(graph, {node: portal_id}, 'label')
            networkx.set_node_attributes(graph, {node: is_outer_node(graph, node)}, 'outer')


# Add an edge between each portal of the same label
def connect_portal_nodes(graph: networkx.Graph):
    known_portals = {}
    for node, label in graph.nodes.data('label'):
        other_end = known_portals.get(label)
        if other_end is None:
            known_portals[label] = node
        else:
            graph.add_edge(node, other_end, distance=1)


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
    label_portal_nodes(graph, input_lines)
    reduced_graph = reduce_graph_to_labelled_nodes(graph)
    connect_portal_nodes(reduced_graph)

    return reduced_graph


def reduce_graph_to_labelled_nodes(graph: networkx.Graph) -> networkx.Graph:
    reduced_graph = networkx.subgraph(graph, (node for node, label in graph.nodes.data('label') if label is not None))
    reduced_graph = reduced_graph.copy()
    for node1, node2 in itertools.combinations(reduced_graph.nodes, 2):
        try:
            path = networkx.shortest_path(graph, node1, node2)
        except networkx.NetworkXNoPath:
            continue

        distance = len(path) - 1
        reduced_graph.add_edge(node1, node2, distance=distance)

    return reduced_graph


def part1(graph: networkx.Graph) -> int:
    start_node = next(node for node, label in graph.nodes.data('label') if label == START_NODE_LABEL)
    end_node = next(node for node, label in graph.nodes.data('label') if label == END_NODE_LABEL)
    path = networkx.shortest_path(graph, start_node, end_node)
    # print("Doing the stupid thing")
    # print(sum(1 for _ in networkx.all_simple_paths(graph, start_node, end_node)))

    return sum(graph.edges[(node1, node2)]['distance'] for node1, node2 in zip(path, path[1:]))


def part2(graph: networkx.Graph) -> int:
    start_node = next(node for node, label in graph.nodes.data('label') if label == START_NODE_LABEL)
    end_node = next(node for node, label in graph.nodes.data('label') if label == END_NODE_LABEL)

    # Both to_visit and visited hold tuples of (node, level)
    to_visit = [(start_node, 0)]
    visited = set()
    distances = {(start_node, 0): 0}
    parent_nodes = {(start_node, 0): None}
    while len(to_visit) > 0:
        node, depth = to_visit.pop()
        if node == end_node and depth <= 0:
            # Need to subtract 1 to account for the fake "portal" we go through from ZZ to ZZ
            return distances[(node, depth)] - 1

        visited.add((node, depth))

        # Get all nodes that should be on the outer ring. On depth == 0, this is just the start and end nodes.
        outer_neighbors = [candidate_node for candidate_node in graph.neighbors(node)
                           if (graph.nodes[candidate_node]['outer']
                               and ((depth == 0 and graph.nodes[candidate_node]['label'] in (START_NODE_LABEL, END_NODE_LABEL))
                                    or (depth > 0 and graph.nodes[candidate_node]['label'] not in (START_NODE_LABEL, END_NODE_LABEL))
                                    )
                               )
                           ]
        inner_neighbors = [candidate_node for candidate_node in graph.neighbors(node) if not graph.nodes[candidate_node]['outer']]
        # if depth == 10 and graph.nodes[node]['label'] == 'XQ':
            # breakpoint()

        # Go to the outer neighbors first to prioritize getting out
        for neighbor in outer_neighbors + inner_neighbors:
            # We don't want to consider nodes that have already been visited, or other portal ends
            if graph.nodes[neighbor]['label'] == graph.nodes[node]['label']:
                continue
            elif (neighbor, depth) in visited:
                continue

            # Find the opposite end of the portal, which is any node with the same label
            # Awful, I know.
            opposite_end = next(candidate_node for candidate_node, label in graph.nodes.data('label')
                                if ((label == graph.nodes[neighbor]['label'] and candidate_node != neighbor)
                                    or candidate_node == end_node == neighbor))
            next_depth = depth - 1 if graph.nodes[neighbor]['outer'] else depth + 1
            to_explore = (opposite_end, next_depth)

            distance_to_neighbor = distances[(node, depth)] + graph.edges[(node, neighbor)]['distance']
            old_distance = distances.get((neighbor, depth))
            if old_distance is None or old_distance > distance_to_neighbor:
                distances[(neighbor, depth)] = distance_to_neighbor
            distances[to_explore] = distances[(neighbor, depth)] + 1
            parent_nodes[to_explore] = (node, depth)
            if to_explore not in visited:
                to_visit.insert(0, to_explore)


# A debug function used to visualize the drawn graph
def draw_graph(graph: networkx.Graph) -> None:
    positions = networkx.spring_layout(graph)
    networkx.draw_networkx_nodes(graph, positions)
    networkx.draw_networkx_edges(graph, positions)
    networkx.draw_networkx_labels(graph, positions, {node: label for node, label in graph.nodes.data('label')})
    networkx.draw_networkx_edge_labels(graph, positions, {(node1, node2): distance for node1, node2, distance in graph.edges.data('distance')})
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input_lines = [line.rstrip('\n') for line in f.readlines()]

    graph = make_graph_from_input_lines(input_lines)
    print(part1(graph))
    print(part2(graph))
