from dataclasses import dataclass
from typing import List, Tuple, Optional


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
    MODE_PARAMETER = 0
    MODE_IMMEDIATE = 1
    OPCODE__ALLS = (OPCODE_TERMINATE, OPCODE_ADD, OPCODE_MULTIPLY, OPCODE_INPUT, OPCODE_OUTPUT,
                    OPCODE_JUMP_IF_TRUE, OPCODE_JUMP_IF_FALSE, OPCODE_LESS_THAN, OPCODE_EQUALS)

    def __init__(self, instruction: int):
        # The opcode is the first two digits of the number, the rest are parameter modes
        self.opcode: int = instruction % 100
        if self.opcode not in Operation.OPCODE__ALLS:
            raise ValueError(f"Bad opcode: {self.opcode}")
        self.modes: Tuple[int] = self._extract_parameter_modes(instruction//100)

    def _extract_parameter_modes(self, raw_modes) -> Tuple[int]:
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
        }
        MEMORY_OPCODES = (Operation.OPCODE_ADD, Operation.OPCODE_MULTIPLY, Operation.OPCODE_INPUT,
                          Operation.OPCODE_LESS_THAN, Operation.OPCODE_EQUALS)

        num_parameters = PARAMETER_COUNTS[self.opcode]
        modes = [Operation.MODE_PARAMETER for i in range(num_parameters)]
        mode_str = str(raw_modes)
        # Iterate over the modes digits backwards, assigning them to the parameter list until we exhaust the modes
        # The rest must be leading zeroes
        for mode_index, digit in zip(range(num_parameters), reversed(mode_str)):
            modes[mode_index] = int(digit)

        # The last argument (the address parameter) must always be in immediate mode

        if self.opcode in MEMORY_OPCODES:
            modes[-1] = Operation.MODE_IMMEDIATE

        return tuple(modes)

    # Run the given operation, starting at the given instruction pointer
    # Returns the address that the instruction pointer should become
    def run(self, memory: List[int], instruction_pointer: int, program_input=None) -> int:
        OPERATION_FUNCS = {
            # nop for terminate
            Operation.OPCODE_TERMINATE: lambda x: None,
            Operation.OPCODE_ADD: Operation.add,
            Operation.OPCODE_MULTIPLY: Operation.multiply,
            Operation.OPCODE_INPUT: Operation.input,
            Operation.OPCODE_OUTPUT: Operation.output,
            Operation.OPCODE_JUMP_IF_TRUE: Operation.jump_if_true,
            Operation.OPCODE_JUMP_IF_FALSE: Operation.jump_if_false,
            Operation.OPCODE_LESS_THAN: Operation.less_than,
            Operation.OPCODE_EQUALS: Operation.equals
        }

        args = []
        for i, mode in enumerate(self.modes):
            # Add 1 to move past the opcode itself
            pointer = instruction_pointer + i + 1
            arg = memory[pointer]
            if mode == Operation.MODE_PARAMETER:
                arg = memory[arg]
            elif mode != Operation.MODE_IMMEDIATE:
                raise ValueError(f"Invalid parameter mode {mode}")

            args.append(arg)

        func = OPERATION_FUNCS[self.opcode]
        if program_input is not None:
            jump_addr = func(memory, program_input, *args)
        else:
            jump_addr = func(memory, *args)

        if jump_addr is not None:
            return jump_addr

        return instruction_pointer + len(self.modes) + 1

    @staticmethod
    def add(memory: List[int], a: int, b: int, loc: int) -> None:
        memory[loc] = a + b

    @staticmethod
    def multiply(memory: List[int], a: int, b: int, loc: int) -> None:
        memory[loc] = a * b

    @staticmethod
    def input(memory: List[int], program_input: int, loc: int) -> None:
        memory[loc] = program_input

    @staticmethod
    def output(memory: List[int], value: int) -> None:
        print("OUTPUT:", value)

    @staticmethod
    def jump_if_true(memory: List[int], test_value: int, new_instruction_pointer: int) -> Optional[int]:
        return new_instruction_pointer if test_value != 0 else None

    @staticmethod
    def jump_if_false(memory: List[int], test_value: int, new_instruction_pointer: int) -> Optional[int]:
        return new_instruction_pointer if test_value == 0 else None

    @staticmethod
    def less_than(memory: List[int], a: int, b: int, loc: int):
        memory[loc] = int(a < b)

    @staticmethod
    def equals(memory: List[int], a: int, b: int, loc: int):
        memory[loc] = int(a == b)


def execute_program(initial_state: List[int], program_inputs: List[int]):
    memory = initial_state[:]
    i = 0
    input_cursor = 0
    while i < len(memory):
        operation = Operation(memory[i])
        program_input = None
        if operation.opcode == Operation.OPCODE_TERMINATE:
            break
        elif operation.opcode == Operation.OPCODE_INPUT:
            program_input = program_inputs[input_cursor]
            input_cursor += 1

        i = operation.run(memory, i, program_input)


def part1(inputs):
    execute_program(inputs, [1])


def part2(inputs):
    execute_program(inputs, [5])


if __name__ == '__main__':
    with open('../input.txt') as f:
        inputs = [int(item) for item in f.read().rstrip().split(',')]

    part1(inputs)
    part2(inputs)
