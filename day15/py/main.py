import collections
import enum
import sys
from typing import List, Iterable, Tuple, Optional, Set


# Halt indicates that the assembled program should terminate
class Halt(Exception):
    pass


class Memory(collections.OrderedDict):
    def __missing__(self, address):
        if address < 0:
            raise KeyError("Address cannot be < 0")
        return 0


# Operation represents an operation that the intcode computer should do
class Operation:
    OPCODE_TERMINATE = 99
    OPCODE_ADD = 1
    OPCODE_MULTIPLY = 2
    OPCODE_INPUT = 3
    OPCODE_OUTPUT = 4
    OPCODE_JUMP_IF_TRUE = 5
    OPCODE_JUMP_IF_FALSE = 6
    OPCODE_LESS_THAN = 7
    OPCODE_EQUALS = 8
    OPCODE_SET_REL_BASE = 9
    MODE_POSITION = 0
    MODE_IMMEDIATE = 1
    MODE_RELATIVE = 2
    ALL_OPCODES = (OPCODE_TERMINATE, OPCODE_ADD, OPCODE_MULTIPLY, OPCODE_INPUT, OPCODE_OUTPUT,
                   OPCODE_JUMP_IF_TRUE, OPCODE_JUMP_IF_FALSE, OPCODE_LESS_THAN, OPCODE_EQUALS, OPCODE_SET_REL_BASE)
    # Opcodes that write to memory as their last parameter
    MEMORY_OPCODES = (OPCODE_ADD, OPCODE_MULTIPLY, OPCODE_INPUT, OPCODE_LESS_THAN, OPCODE_EQUALS)

    def __init__(self, instruction: int, rel_base: int = 0):
        # The opcode is the first two digits of the number, the rest are parameter modes
        self.opcode: int = instruction % 100
        if self.opcode not in Operation.ALL_OPCODES:
            raise ValueError(f"Bad opcode: {self.opcode}")
        self.modes: Tuple[int, ...] = self._extract_parameter_modes(instruction//100)
        self.output = None
        self.rel_base = rel_base

    def _extract_parameter_modes(self, raw_modes) -> Tuple[int, ...]:
        PARAMETER_COUNTS = {
            Operation.OPCODE_TERMINATE: 0,
            Operation.OPCODE_ADD: 3,
            Operation.OPCODE_MULTIPLY: 3,
            Operation.OPCODE_INPUT: 1,
            Operation.OPCODE_OUTPUT: 1,
            Operation.OPCODE_JUMP_IF_TRUE: 2,
            Operation.OPCODE_JUMP_IF_FALSE: 2,
            Operation.OPCODE_LESS_THAN: 3,
            Operation.OPCODE_EQUALS: 3,
            Operation.OPCODE_SET_REL_BASE: 1,
        }

        num_parameters = PARAMETER_COUNTS[self.opcode]
        modes = [Operation.MODE_POSITION for i in range(num_parameters)]
        mode_str = str(raw_modes)
        # Iterate over the modes digits backwards, assigning them to the parameter list until we exhaust the modes
        # The rest must be leading zeroes
        for mode_index, digit in zip(range(num_parameters), reversed(mode_str)):
            modes[mode_index] = int(digit)

        return tuple(modes)

    # Run the given operation, starting at the given instruction pointer
    # Returns the address that the instruction pointer should become
    def run(self, memory: Memory, instruction_pointer: int, program_input: Optional[int] = None) -> int:
        OPERATION_FUNCS = {
            # nop for terminate
            Operation.OPCODE_TERMINATE: Operation.terminate,
            Operation.OPCODE_ADD: Operation.add,
            Operation.OPCODE_MULTIPLY: Operation.multiply,
            Operation.OPCODE_INPUT: Operation.input,
            Operation.OPCODE_OUTPUT: Operation.output,
            Operation.OPCODE_JUMP_IF_TRUE: Operation.jump_if_true,
            Operation.OPCODE_JUMP_IF_FALSE: Operation.jump_if_false,
            Operation.OPCODE_LESS_THAN: Operation.less_than,
            Operation.OPCODE_EQUALS: Operation.equals,
            Operation.OPCODE_SET_REL_BASE: Operation.set_rel_base
        }

        # Reset the output and rel base of a previous run
        self.output = None

        args = []
        for i, mode in enumerate(self.modes):
            # Add 1 to move past the opcode itself
            pointer = instruction_pointer + i + 1
            arg = memory[pointer]
            # The last argument (the address parameter) must always act as an immediate
            # The problem statement is misleading in this regard. You do NOT want to get an address to store the value
            # at from another address.
            if mode != self.MODE_IMMEDIATE and i == len(self.modes) - 1 and self.opcode in Operation.MEMORY_OPCODES:
                if mode == Operation.MODE_RELATIVE:
                    arg = self.rel_base + arg
                # Position mode is already handled since it would be arg = arg here.
            elif mode == Operation.MODE_POSITION:
                arg = memory[arg]
            elif mode == Operation.MODE_RELATIVE:
                arg = memory[self.rel_base + arg]
            elif mode != Operation.MODE_IMMEDIATE:
                raise ValueError(f"Invalid parameter mode {mode}")

            args.append(arg)

        func = OPERATION_FUNCS[self.opcode]
        if program_input is None:
            jump_addr = func(self, memory, *args)
        else:
            jump_addr = func(self, memory, program_input, *args)

        out_addr = instruction_pointer + len(self.modes) + 1
        if jump_addr is not None:
            out_addr = jump_addr

        return out_addr

    def terminate(self, memory: Memory) -> None:
        raise Halt("catch fire")

    def add(self, memory: Memory, a: int, b: int, loc: int) -> None:
        memory[loc] = a + b

    def multiply(self, memory: Memory, a: int, b: int, loc: int) -> None:
        memory[loc] = a * b

    def input(self, memory: Memory, program_input: int, loc: int) -> None:
        memory[loc] = program_input

    def output(self, memory: Memory, value: int) -> None:
        self.output = value

    def jump_if_true(self, memory: Memory, test_value: int, new_instruction_pointer: int) -> Optional[int]:
        return new_instruction_pointer if test_value != 0 else None

    def jump_if_false(self, memory: Memory, test_value: int, new_instruction_pointer: int) -> Optional[int]:
        return new_instruction_pointer if test_value == 0 else None

    def less_than(self, memory: Memory, a: int, b: int, loc: int) -> None:
        memory[loc] = int(a < b)

    def equals(self, memory: Memory, a: int, b: int, loc: int) -> None:
        memory[loc] = int(a == b)

    def set_rel_base(self, memory: Memory, base_delta: int) -> None:
        self.rel_base += base_delta


# Executes the program, returning the instruction pointer to continue at (if the program paused), the relative base,
# and a list of all outputs that occurred during the program's execution
def execute_program(memory: Memory, program_inputs: List[int], initial_instruction_pointer: int = 0, initial_rel_base: int = 0) -> Tuple[Optional[int], int, List[int]]:
    i = initial_instruction_pointer
    input_cursor = 0
    outputs = []
    rel_base = initial_rel_base
    # Go up to the maximum address, not the number of addresses
    while i < max(memory.keys()):
        operation = Operation(memory[i], rel_base)
        program_input = None
        # If we're looking for input
        if operation.opcode == Operation.OPCODE_INPUT:
            # If we are out of input, don't fail out, but rather just pause execution
            if input_cursor >= len(program_inputs):
                return i, rel_base, outputs
            program_input = program_inputs[input_cursor]
            input_cursor += 1

        try:
            i = operation.run(memory, i, program_input)
            output = operation.output
            rel_base = operation.rel_base
        except Halt:
            break

        if output is not None:
            outputs.append(output)

    # The program is finished, and we are saying there is no instruction pointer
    return None, rel_base, outputs


# Problem specific code stats here

class Direction(enum.IntEnum):
    NORTH = 1
    SOUTH = 2
    EAST = 3
    WEST = 4

    @staticmethod
    def move_coords_in_direction(direction: 'Direction', row: int, col: int) -> Tuple[int, int]:
        D_ROWS = {
            Direction.NORTH: -1,
            Direction.SOUTH: 1,
            Direction.EAST: 0,
            Direction.WEST: 0
        }

        D_COLS = {
            Direction.NORTH: 0,
            Direction.SOUTH: 0,
            Direction.EAST: -1,
            Direction.WEST: 1
        }

        return (row + D_ROWS[direction], col + D_COLS[direction])

    @staticmethod
    def get_opposite(direction: 'Direction'):
        OPPOSITES = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }

        return OPPOSITES[direction]


class Node:
    class Type(enum.Enum):
        WALL = 0
        OPEN = 1
        TARGET = 2
        OXYGEN = 3

    def __init__(self, row: int, col: int, node_type: Type):
        self.row = row
        self.col = col
        self.node_type = node_type
        # Store as a dict of NORTH, SOUTH, WEST, EAST to the node, corresponding to the directions gievn
        self.neighbors = {}
        self.distance = None

    def __repr__(self) -> str:
        return f'<Node: row={self.row}, col={self.col}, type={self.node_type}, num_neighbors={len(self.neighbors)}>'


def build_graph_with_dfs(memory: Memory, root: Node) -> None:
    next_ip = 0
    rel_base = 0
    visited = set()

    def explore_in_direction(direction: Direction) -> Node.Type:
        nonlocal next_ip
        nonlocal rel_base

        next_ip, rel_base, outputs = execute_program(memory, [direction], next_ip, rel_base)
        if next_ip is None:
            raise Exception("Program terminated unexpectedly")

        return Node.Type(outputs[0])

    def dfs(node: Node):
        visited.add(node)
        neighbors = {
            Direction.NORTH: None,
            Direction.SOUTH: None,
            Direction.EAST: None,
            Direction.WEST: None
        }

        neighbors = {**neighbors, **node.neighbors}

        for direction, neighbor in neighbors.items():
            if neighbor in visited:
                continue

            node_type = explore_in_direction(direction)
            if neighbor is None:
                neighbor_coords = Direction.move_coords_in_direction(direction, node.row, node.col)
                neighbor = Node(neighbor_coords[0], neighbor_coords[1], node_type)
                neighbor.neighbors[Direction.get_opposite(direction)] = node
                neighbors[direction] = neighbor
                node.neighbors[direction] = neighbor

            # If the node type is a wall, we can't explore it.
            if node_type != Node.Type.WALL:
                dfs(neighbor)
                # Make sure we backtrack after weexplore a node so that we don't lose track of the robot's position
                explore_in_direction(Direction.get_opposite(direction))

    dfs(root)


# Find the distance to all nodes in the graph, returning a set of the nodes explored
def populate_graph_distances(root: Node) -> Set[Node]:
    root.distance = 0
    to_visit = [root]
    visited = set()
    while len(to_visit) > 0:
        node = to_visit.pop(0)
        if node in visited:
            continue

        visited.add(node)
        for neighbor in node.neighbors.values():
            if neighbor.node_type == Node.Type.WALL:
                continue

            neighbor.distance = node.distance + 1
            to_visit.append(neighbor)

    return visited


def part1(all_nodes: Iterable[Node]) -> int:
    for node in all_nodes:
        if node.node_type == node.Type.TARGET:
            return node.distance
    else:
        raise Exception("No target node!")


# Expects an iterable of nodes that are explorable (i.e. not walls)
def part2(all_nodes: Iterable[Node]) -> int:
    for node in all_nodes:
        if node.node_type == node.Type.TARGET:
            node.node_type = node.Type.OXYGEN
            break
    else:
        raise Exception("No target node!")

    # Due to our inability to make large copies of the graph, we need to store the node types by position
    # We could _probably_ clean up the rest of the program to be in this form, but al ot of the graph searches would be
    # less clean
    node_types = {(node.row, node.col): node.node_type for node in all_nodes}
    node_types_to_check = node_types.copy()
    minutes = 0

    # While we have nodes that aren't oxygen left over
    while len([node_type for node_type in node_types_to_check.values() if node_type != Node.Type.OXYGEN]) > 0:
        minutes += 1
        for location, node_type in node_types_to_check.items():
            if node_type != Node.Type.OXYGEN:
                continue

            for direction in Direction:
                location_in_direction = Direction.move_coords_in_direction(direction, *location)
                # Spread the oxygen if the tile exists and we're not spreading into a wall
                if location_in_direction in node_types:
                    node_types[location_in_direction] = Node.Type.OXYGEN

        node_types_to_check = node_types.copy()

    return minutes


# A debug method that uses dfs to print the entire maze graph
def print_graph(root: Node):
    nodes = {}
    visited = set()
    to_visit = [root]
    while len(to_visit) > 0:
        node = to_visit.pop()
        if node in visited:
            continue

        visited.add(node)
        nodes[(node.row, node.col)] = node
        for neighbor in node.neighbors.values():
            to_visit.append(neighbor)

    max_col = max(coord[0] for coord in nodes)
    max_row = max(coord[1] for coord in nodes)
    min_col = min(coord[0] for coord in nodes)
    min_row = min(coord[1] for coord in nodes)
    for i in range(min_row, max_row+1):
        for j in range(min_col, max_col+1):
            if (i, j) == (0, 0):
                print('!', end='')
            if (i, j) not in nodes:
                print('?', end='')
                continue

            node = nodes[(i, j)]
            if node.node_type == Node.Type.TARGET:
                print('x', end='')
            elif node.node_type == Node.Type.WALL:
                print('#', end='')
            else:
                print(' ', end='')
        print('')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        # Today's part 2 produces a lot of output, so i wanted to keep them separate
        print("Usage: ./main.py in_file")
        sys.exit(1)

    memory = Memory()
    with open(sys.argv[1]) as f:
        for i, item in enumerate(f.read().rstrip().split(",")):
            memory[i] = int(item)

    root_node = Node(0, 0, Node.Type.OPEN)
    build_graph_with_dfs(memory, root_node)
    nodes = populate_graph_distances(root_node)
    print_graph(root_node)

    print(part1(nodes))
    print(part2(nodes))
