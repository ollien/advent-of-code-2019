import collections
import enum
import itertools
import re
import sys
import networkx
from typing import Dict, List, Tuple, Optional


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


# Problem specific code starts here
SCAFFOLD_CHAR = ord('#')
ROBOT_CHAR = ord('^')


class TurnDirection(enum.Enum):
    LEFT = 'L'
    RIGHT = 'R'

    def __str__(self):
        return self.value


class Direction(enum.IntEnum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4

    # Given the direction we currently are, get the direction we need to turn to face this coordinate.
    # Returns None if these are the same coordinate.
    @staticmethod
    def get_direction_to_coordinate(current_pos: Tuple[int, int], next_pos: Tuple[int, int]) -> Optional['Direction']:
        current_row, current_col = current_pos
        next_row, next_col = next_pos
        direction_required = None
        if next_col == current_col and next_row < current_row:
            direction_required = Direction.NORTH
        elif next_col == current_col and next_row > current_row:
            direction_required = Direction.SOUTH
        elif next_row == current_row and next_col < current_col:
            direction_required = Direction.WEST
        elif next_row == current_row and next_col > current_col:
            direction_required = Direction.EAST

        return direction_required

    # Gets the direction we need to turn for fix.
    # Returns None if we are currently facing the right direction
    def get_turn_to_direction(self, new_direction: 'Direction') -> Optional[Tuple['TurnDirection', ...]]:
        turn_distance = (self - new_direction) % 4
        # if turn_distance == 2:
            # breakpoint()
        if turn_distance == 0:
            return None
        elif turn_distance == 3:
            return (TurnDirection.RIGHT,)
        else:
            return (TurnDirection.LEFT,) * turn_distance

    def move_coords_in_direction(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        D_ROWS = {
            Direction.NORTH: -1,
            Direction.SOUTH: 1,
            Direction.EAST: 0,
            Direction.WEST: 0
        }

        D_COLS = {
            Direction.NORTH: 0,
            Direction.SOUTH: 0,
            Direction.EAST: 1,
            Direction.WEST: -1
        }

        return (pos[0] + D_ROWS[self], pos[1] + D_COLS[self])


# Return a graph of all of the scaffolding, with a tuple represeting the robot's starting position
def build_graph_from_program(initial_memory_state: Memory) -> (networkx.Graph, Tuple[int, int]):
    program_memory = initial_memory_state.copy()

    # Add all edges that are directly above/below or directly left/right of our cursor
    def add_adjacent_edges(scaffold_graph: networkx.Graph, row_cursor: int, col_cursor: int):
        scaffold_graph.add_node((row_cursor, col_cursor))
        for d_row in range(-1, 1):
            for d_col in range(-1, 1):
                if d_row == 0 and d_col == 0 or 0 not in (d_row, d_col):
                    continue
                adjacent_coord = (row_cursor + d_row, col_cursor + d_col)
                if adjacent_coord in scaffold_graph:
                    scaffold_graph.add_edge((row_cursor, col_cursor), adjacent_coord)

    _, _, outputs = execute_program(program_memory, [])
    scaffold_graph = networkx.Graph()
    row_cursor = 0
    col_cursor = 0
    robot_pos = None
    for item in outputs:
        if item == ord('\n'):
            row_cursor += 1
            col_cursor = 0
            continue
        elif item == SCAFFOLD_CHAR:
            add_adjacent_edges(scaffold_graph, row_cursor, col_cursor)
        elif item == ROBOT_CHAR:
            add_adjacent_edges(scaffold_graph, row_cursor, col_cursor)
            robot_pos = (row_cursor, col_cursor)

        col_cursor += 1

    return scaffold_graph, robot_pos


def make_greedy_path(scaffold_graph: networkx.Graph, start_pos: Tuple[int, int]) -> str:
    path_components = []
    forward_count = 0
    robot_direction = Direction.NORTH
    visited = set()
    node_cursor = start_pos
    while visited != set(scaffold_graph.nodes):
        next_pos = robot_direction.move_coords_in_direction(node_cursor)
        if next_pos not in scaffold_graph:
            possible_points = set(scaffold_graph.neighbors(node_cursor)) - set(visited)
            next_pos = sorted(possible_points, key=lambda x: (x[0], x[1]))[0]
            new_direction = Direction.get_direction_to_coordinate(node_cursor, next_pos)
            turns_needed = robot_direction.get_turn_to_direction(new_direction)
            robot_direction = new_direction

            if forward_count > 0:
                path_components.append(str(forward_count))
            path_components += [str(turn) for turn in turns_needed]
            forward_count = 0

        visited.add(node_cursor)
        visited.add(next_pos)
        node_cursor = next_pos
        forward_count += 1
    if forward_count > 0:
        path_components.append(str(forward_count))

    return ','.join(path_components)


# Find a component of the string that occurs more than once, starting at the given position and checking forwards/backwards
# based on the given offset
def find_component(path: str, start: int, offset: int) -> str:
    component = path[start:offset] if offset > 0 else path[start + offset:]
    if (offset > 0 and component[-1] != ',') or (offset < 0 and component[0] != ','):
        return None
    elif path.count(component) == 1:
        return None

    return component.strip(',')


# Get all substrings of s without the given component
def get_substrings_without_str(s: str, component: str) -> str:
    locations = [(match.start(), match.end()) for match in re.finditer(re.escape(component), s)]
    locations.insert(0, (None, None))
    locations.append((None, None))

    substrings = [s[location1[1]:location2[0]].strip(',') for location1, location2 in zip(locations, locations[1:])]

    return [substring for substring in substrings if len(substring) > 0]


# If a path string is a duplicate itself, strip it down to its base component
def dedup_path_string(s: str) -> str:
    normalized_s = s
    # Need to join the two components with a comma so that we actually can spot the repetition (the string may not have a trailing comma)
    if s[-1] != ',':
        normalized_s = s + ','

    # Find if the string is only composed of a portion of itself
    repeat_index = (normalized_s + normalized_s).find(normalized_s, 1, -1)
    if repeat_index == -1:
        return s
    else:
        return s[:repeat_index].rstrip(',')


# Given the two other components, see if there's one final component left in the string
def get_last_component(path: str, component1: str, component2: str) -> Optional[str]:
    path_without_component1 = get_substrings_without_str(path, component1)
    # Get the path without component 1 or component 2
    remaining_comonents = []
    for substring in path_without_component1:
        remaining_comonents += get_substrings_without_str(substring, component2)

    # Make sure the last component we have is unique
    if len(set(remaining_comonents)) > 1:
        return None

    last_component = dedup_path_string(remaining_comonents[0])
    if len(last_component) > 20:
        return None

    return last_component


# Find the three compressible components of the path
# This is NOT pretty. This could be generalized by searching for all substrings, but that would be longer
def find_compressable_path_components(path: str) -> Tuple[str, str, str]:
    MAX_LENGTH = 20
    for i in range(MAX_LENGTH + 1):
        path_candidate = path
        # Find the first component at the start of the string
        component1 = find_component(path_candidate, 0, i)
        if component1 is None:
            continue

        # Remove it from both ends
        path_candidate = path_candidate[len(component1):].lstrip(',')
        if path_candidate.endswith(component1):
            path_candidate = path_candidate[:-len(component1)].rstrip(',')

        for j in range(MAX_LENGTH + 1):
            trimmed_candidate = path_candidate
            # We know there must be another unique component at the end of the string
            component2 = find_component(trimmed_candidate, len(trimmed_candidate) - 1, -j)
            if component2 is None:
                continue

            # Remove it from both ends
            trimmed_candidate = trimmed_candidate[:-len(component2)].rstrip(',')
            if trimmed_candidate.startswith(component2):
                trimmed_candidate = trimmed_candidate[len(component2):].lstrip(',')

            component3 = get_last_component(trimmed_candidate, component1, component2)
            if component3 is None:
                continue

            return component1, component2, component3
    else:
        raise Exception("path is not compressible into three functions")


# Convert a path into a list of functions based on the given function defintiions
def make_function_nav_string(path: str, functions: Dict[str, str]) -> str:
    i = 0
    function_nav_string = []
    while i < len(path):
        for function_name, function in sorted(functions.items(), key=lambda x: len(x[1]), reverse=True):
            if path[i:i+len(function)] == function:
                function_nav_string.append(function_name)
                # +1 for the comma
                i += len(function) + 1
                break
        else:
            raise ValueError('Functions not in path')

    return ','.join(function_nav_string)


def part1(scaffold_graph: networkx.Graph) -> int:
    return sum(row * col for row, col in scaffold_graph.nodes if scaffold_graph.degree((row, col)) > 2)


def part2(initial_memory_state: Memory, scaffold_graph: networkx.Graph, robot_pos: Tuple[int, int]):
    def make_ascii_input(s: str) -> str:
        return [ord(char) for char in s]

    nav_string = make_greedy_path(scaffold_graph, robot_pos)
    functions = find_compressable_path_components(nav_string)
    named_functions = {name: function for name, function in zip(['A', 'B', 'C'], functions)}
    function_nav_string = make_function_nav_string(nav_string, named_functions)

    # Start the sequence of the interacitve mode
    program_memory = initial_memory_state.copy()
    program_memory[0] = 2
    _, _, outputs = execute_program(program_memory, [
        *make_ascii_input(function_nav_string + '\n'),
        *make_ascii_input(named_functions['A'] + '\n'),
        *make_ascii_input(named_functions['B'] + '\n'),
        *make_ascii_input(named_functions['C'] + '\n'),
        *make_ascii_input('n\n')
    ])

    return outputs[-1]


# A debug method to print the entire graph
def print_scaffold_graph(scaffold_graph: networkx.Graph) -> None:
    print('   ', end='')
    max_row = max(node[0] for node in scaffold_graph.nodes) + 1
    max_col = max(node[1] for node in scaffold_graph.nodes) + 1

    for i in range(max_col):
        print(i // 10 if i // 10 > 0 else ' ', end='')
    print('')
    print('   ', end='')
    for i in range(max_col):
        print(i % 10, end='')
    print('')
    for i in range(max_row):
        print(f'{i:2} ', end='')
        for j in range(max_col):
            if (i, j) in scaffold_graph.nodes:
                print('#', end='')
            else:
                print('.', end='')
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

    scaffold_graph, robot_pos = build_graph_from_program(memory)
    print_scaffold_graph(scaffold_graph)
    print(part1(scaffold_graph))
    print(part2(memory, scaffold_graph, robot_pos))
