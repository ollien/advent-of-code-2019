import collections
import itertools
from dataclasses import dataclass
import re
import sys
import enum
import networkx
from typing import List, Tuple, Optional


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
# and a list of all inputs/outputs that occurred during the program's execution
# This return signature is gross but it's day 23... I'm not going to rewrite it.
def execute_program(memory: Memory, program_inputs: List[int], initial_instruction_pointer: int = 0, initial_rel_base: int = 0) -> Tuple[Optional[int], int, List[int], List[int]]:
    i = initial_instruction_pointer
    input_cursor = 0
    consumed_inputs = []
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
                return i, rel_base, consumed_inputs, outputs
            program_input = program_inputs[input_cursor]
            consumed_inputs.append(program_input)
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
    return None, rel_base, consumed_inputs, outputs

# Problem specific code starts here


@dataclass(eq=True, frozen=True)
class Room:
    name: str
    directions: Tuple[str, ...]
    items: Tuple[str, ...]

    @classmethod
    def parse_output_to_room(cls, output: str):
        OUTPUT_REGEX = re.compile(r'^\n*== (?P<room_name>.*?) ==.*'
                                  r'?Doors here lead:\n(?P<directions>(?:- [^\n]*\n)*)\n'
                                  r'(?:Items here:\n(?P<items>(?:- [^\n]*\n)*))?', flags=re.S)

        match = re.match(OUTPUT_REGEX, output)
        groups = match.groupdict()
        directions = tuple(direction[2:] for direction in groups['directions'].splitlines())
        items = ()
        if groups['items'] is not None:
            items = tuple(item[2:] for item in groups['items'].splitlines())

        return cls(groups['room_name'], directions, items)


class Direction(enum.Enum):
    NORTH = 'north'
    SOUTH = 'south'
    EAST = 'east'
    WEST = 'west'

    def get_opposite(self) -> 'Direction':
        OPPOSITES = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }

        return OPPOSITES[self]


class BadItem(Exception):
    def __init__(self, item_name: str) -> None:
        self.item_name = item_name

        super().__init__()


# Solves the text adventure automatically. A bit of a chonker, but it works
def auto_solve(initial_memory_state: Memory) -> None:
    TARGET_ROOM_NAME = 'Pressure-Sensitive Floor'
    # A list of dangerous items. The two pre-provided do not end the run immediately and are harder to work around.
    blacklisted_items = ['infinite loop', 'giant electromagnet']
    graph = networkx.OrderedDiGraph()
    visited = set()
    next_ip = 0
    rel_base = 0
    memory = initial_memory_state.copy()
    inventory = []

    def execute_step(input_str: str) -> str:
        nonlocal next_ip
        nonlocal rel_base
        next_input = convert_input_to_ascii(input_str) if len(input_str) > 0 else []
        next_ip, rel_base, _, outputs = execute_program(memory, next_input, next_ip, rel_base)

        return convert_ascii_output_to_text(outputs)

    def explore_in_direction(direction: Direction) -> str:
        return execute_step(direction.value)

    def take_item(item_name: str) -> str:
        output = execute_step(f'take {item_name}')
        if next_ip is None:
            raise BadItem(item_name)

        inventory.append(item_name)

        return output

    def drop_item(item_name: str) -> str:
        return execute_step(f'drop {item_name}')

    def build_graph_with_dfs(direction_to_travel: Optional[Direction] = None, last_room: Optional[Room] = None):
        if direction_to_travel is None:
            output = execute_step('')
        else:
            output = explore_in_direction(direction_to_travel)

        room = Room.parse_output_to_room(output)
        if room.name in visited:
            # We will let the recursion handle undoing this movement.
            print("in visited")
            return

        visited.add(room.name)
        graph.add_node(room.name)
        if last_room is not None:
            graph.add_edge(last_room.name, room.name, direction=direction_to_travel)
            graph.add_edge(room.name, last_room.name, direction=direction_to_travel.get_opposite())

        if room.name == TARGET_ROOM_NAME:
            return

        for item in room.items:
            if item in blacklisted_items:
                continue
            take_item(item)

        for raw_direction in room.directions:
            direction = Direction(raw_direction)
            # If we already have an edge from this node going in the same direction, we don't need to re-explore
            if direction in [graph.edges[edge]['direction'] for edge in graph.edges(room.name)]:
                continue

            build_graph_with_dfs(direction, room)
            opposite_direction = direction.get_opposite()
            explore_in_direction(opposite_direction)

    # Find the items that without, we will be too light to enter the airlocked room, and enter it
    def enter_airlock(direction_to_target: Direction) -> str:
        all_items = inventory.copy()
        required_items = []
        for item in all_items:
            drop_item(item)
            output = explore_in_direction(direction_to_target)
            # If we are told that all of the robots are heavier without this one item, we know we must need it.
            if 'heavier' in output:
                print(f'{item} is definitely required')
                required_items.append(item)
            elif 'proceed' in output:
                # If we are told we can proceed, we are done.
                return output

            take_item(item)

        remaining_items = []
        for item in all_items:
            if item not in required_items:
                drop_item(item)
                remaining_items.append(item)

        # For the remaining items, we will check all subsets of the remaining items to see which we must take
        for i in range(len(remaining_items)+1):
            for subset in itertools.combinations(remaining_items, i):
                print('Trying', ', '.join(required_items + list(subset)))
                for item in subset:
                    take_item(item)
                output = explore_in_direction(direction_to_target)
                if 'proceed' in output:
                    return output

                for item in subset:
                    drop_item(item)
        else:
            raise ValueError('Could not find combination of items to enter airlock')

    print('Searching for airlock and items...')
    # Explore the full graph, collecting all items that we can
    # Is there a smarter way to do this than starting from scratch? Yes, but it's just easiest to do it this way as we
    # want to get all items anyway.
    while True:
        try:
            memory = initial_memory_state.copy()
            next_ip = 0
            rel_base = 0
            visited.clear()
            graph.clear()
            inventory.clear()
            build_graph_with_dfs()
            break
        except BadItem as e:
            print(f'Blacklisting {e.item_name}')
            blacklisted_items.append(e.item_name)

    print('Found airlock. Attempting to enter...')
    # Because we're using an ordered graph, we know that the node we want to start with is the first in graph.nodes
    # We also know from the DFS that we are still at the start node.
    start_node = next(iter(graph.nodes))
    target_node = next(node for node in graph.nodes if node == TARGET_ROOM_NAME)
    nodes_to_target = networkx.shortest_path(graph, start_node, target_node)
    for node1, node2 in zip(nodes_to_target[:-1], nodes_to_target[1:-1]):
        direction = graph.edges[(node1, node2)]['direction']
        explore_in_direction(direction)

    direction_to_target = graph.edges[nodes_to_target[-2:]]['direction']
    output = enter_airlock(direction_to_target)
    print(output.splitlines()[-1])


def convert_input_to_ascii(s: str) -> List[int]:
    return [ord(char) for char in s + '\n']


def convert_ascii_output_to_text(outputs: List[int]) -> str:
    return ''.join(chr(char) for char in outputs)


def run(memory: Memory, starting_inputs: List[str] = None) -> None:
    next_ip = 0
    rel_base = 0
    next_input = [] if starting_inputs is None else starting_inputs
    while next_ip is not None:
        if next_input is None:
            input_str = input()
            next_input = convert_input_to_ascii(input_str)

        next_ip, rel_base, _, outputs = execute_program(memory, next_input, next_ip, rel_base)
        print(convert_ascii_output_to_text(outputs), end='')
        next_input = None


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print('Usage: ./main.py in_file [auto]')
        print('       Speicfying auto attempts to solve the adventure automatically :)')
        sys.exit(1)

    memory = Memory()
    with open(sys.argv[1]) as f:
        for i, item in enumerate(f.read().rstrip().split(",")):
            memory[i] = int(item)

    if len(sys.argv) == 3 and sys.argv[2] == 'auto':
        auto_solve(memory)
    elif len(sys.argv) == 3:
        print(f"Invalid subcommand '{sys.argv[2]}'")
    else:
        run(memory)
