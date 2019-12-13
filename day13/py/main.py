import collections
import enum
import itertools
import math
import sys
import os
from typing import List, Tuple, Optional, DefaultDict, Iterable, Any


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

class Tile(enum.Enum):
    EMPTY = 0
    WALL = 1
    BLOCK = 2
    PADDLE = 3
    BALL = 4


# Iterate over the given iterable in chunks by making a copy of the iteratable as an iterator
def group_iter(iterable: Iterable[Any], chunk_size: int):
    chunk_list = [iter(iterable)] * chunk_size
    return itertools.zip_longest(*chunk_list)


# Trace all of the painted points that the robot makes
def run_game(initial_memory_state: Memory, playable: bool = False) -> (DefaultDict[Tuple[int, int], int], Optional[int]):
    screen = collections.defaultdict(lambda: Tile.EMPTY)
    next_ip = 0
    rel_base = 0
    score = None
    memory = initial_memory_state.copy()
    # Set the machine to free play mode
    if playable:
        memory[0] = 2

    next_input = 0
    paddle_position = None
    while next_ip is not None:
        next_ip, rel_base, outputs = execute_program(memory, [next_input], next_ip, rel_base)
        for x, y, value in group_iter(outputs, 3):
            if x == -1 and y == 0:
                score = value
                continue

            tile = Tile(value)
            screen[(x, y)] = tile
            # Everything after this if statement is concerned with moving the paddle, which is unneeded if the game isn't playable
            if not playable:
                continue

            if tile == tile.PADDLE:
                paddle_position = (x, y)
            elif tile == Tile.BALL and paddle_position is not None:
                # Input 0 if the ball is above the paddle, move the paddle towards the ball otherwise.
                next_input = 0 if x == paddle_position[0] else int(math.copysign(1, x - paddle_position[0]))

        print_screen(screen, clear_before_print=playable)

    return screen, score


def print_screen(screen, clear_before_print=False):
    def clear():
        if os.name == 'nt':
            os.system('clr')
        else:
            print('\033c')

    if clear_before_print:
        clear()

    max_x = max(coord[0] for coord in screen)
    max_y = max(coord[1] for coord in screen)
    min_x = min(coord[0] for coord in screen)
    min_y = min(coord[1] for coord in screen)
    for j in range(min_y, max_y+1):
        for i in range(min_x, max_x+1):
            tile = screen[(i, j)]
            if tile == Tile.BLOCK:
                print('#', end='')
            elif tile == Tile.BALL:
                print('*', end='')
            elif tile == tile.PADDLE:
                print('=', end='')
            elif tile != Tile.EMPTY:
                print('.', end='')
            else:
                print(' ', end='')
        print('')


def part1(inputs: Memory) -> int:
    screen = run_game(inputs)[0]

    return list(screen.values()).count(Tile.BLOCK)


def part2(inputs: Memory) -> int:
    score = run_game(inputs, True)[1]

    return score


if __name__ == "__main__":
    if len(sys.argv) != 3:
        # Today's part 2 produces a lot of output, so i wanted to keep them separate
        print("Usage: ./main.py in_file part")
        sys.exit(1)

    memory = Memory()
    with open(sys.argv[1]) as f:
        for i, item in enumerate(f.read().rstrip().split(",")):
            memory[i] = int(item)

    parts = {
        '1': part1,
        '2': part2
    }

    print(parts[sys.argv[2]](memory))
