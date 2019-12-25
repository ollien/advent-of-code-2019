import collections
import sys
import itertools
from typing import Iterable, List, Tuple, Optional, TypeVar


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

def convert_input_to_ascii(s: str) -> List[int]:
    return [ord(char) for char in s + '\n']


def convert_ascii_output_to_text(outputs: List[int]) -> str:
    return ''.join(chr(char) for char in outputs)


def run(initial_memory_state: Memory, starting_inputs: List[str] = None) -> None:
    next_ip = 0
    rel_base = 0
    next_input = [] if starting_inputs is None else starting_inputs
    while next_ip is not None:
        if next_input is None:
            input_str = input()
            next_input = convert_input_to_ascii(input_str)

        next_ip, rel_base, _, outputs = execute_program(initial_memory_state, next_input, next_ip, rel_base)
        print(convert_ascii_output_to_text(outputs), end='')
        next_input = None


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: ./main.py in_file [auto]")
        print("       Specifying auto solves the text adventure for my personal input. Your results may vary")
        sys.exit(1)

    memory = Memory()
    with open(sys.argv[1]) as f:
        for i, item in enumerate(f.read().rstrip().split(",")):
            memory[i] = int(item)

    # The automatic input strings to compelte the text adventure for my input
    AUTO_INPUT_STRINGS = [
        'north',
        'east',
        'south',
        'take hypercube',
        'north',
        'west',
        'north',
        'east',
        'take tambourine',
        'west',
        'west',
        'take spool of cat6',
        'north',
        'take weather machine',
        'west',
        'west',
        'west'
    ]

    if len(sys.argv) == 3 and sys.argv[2] == 'auto':
        auto_inputs = [ascii_char for input_str in AUTO_INPUT_STRINGS for ascii_char in convert_input_to_ascii(input_str)]
        run(memory, auto_inputs)
    elif len(sys.argv) == 3:
        print(f"Invalid subcommand '{sys.argv[2]}'")
    else:
        run(memory)
