from dataclasses import dataclass
from typing import List, Tuple


class Operation:
    OPCODE_TERMINATE = 99
    OPCODE_ADD = 1
    OPCODE_MULTIPLY = 2
    OPCODE_INPUT = 3
    OPCODE_OUTPUT = 4
    MODE_PARAMETER = 0
    MODE_IMMEDIATE = 1
    OPCODE__ALLS = (OPCODE_TERMINATE, OPCODE_ADD, OPCODE_MULTIPLY, OPCODE_INPUT, OPCODE_OUTPUT)

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
            Operation.OPCODE_OUTPUT: 1
        }
        MEMORY_OPCODES = (Operation.OPCODE_ADD, Operation.OPCODE_MULTIPLY, Operation.OPCODE_INPUT)

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
    # Returns the number of steps the instruction pointer went
    def run(self, memory: List[int], instruction_pointer: int, program_input=None) -> int:
        OPERATION_FUNCS = {
            # nop for terminate
            Operation.OPCODE_TERMINATE: lambda x: None,
            Operation.OPCODE_ADD: Operation.add,
            Operation.OPCODE_MULTIPLY: Operation.multiply,
            Operation.OPCODE_INPUT: Operation.input,
            Operation.OPCODE_OUTPUT: Operation.output
        }

        args = []
        for i, mode in enumerate(self.modes):
            # Add 1 to move past the opcode itself
            pointer = instruction_pointer + i + 1
            arg = memory[pointer]
            print(f"raw_arg={arg}")
            if mode == Operation.MODE_PARAMETER:
                print(f"Resolving {arg} to {memory[arg]}")
                arg = memory[arg]
            elif mode != Operation.MODE_IMMEDIATE:
                raise ValueError(f"Invalid parameter mode {mode}")

            args.append(arg)

        print("MODES:", self.modes)
        print("ARGS:", args)
        func = OPERATION_FUNCS[self.opcode]
        if program_input is not None:
            func(memory, program_input, *args)
        else:
            func(memory, *args)

        return len(self.modes) + 1

    @staticmethod
    def add(memory: List[int], a: int, b: int, loc: int):
        memory[loc] = a + b
        print(f"{a} + {b} => {memory[loc]} @ {loc}")

    @staticmethod
    def multiply(memory: List[int], a: int, b: int, loc: int):
        memory[loc] = a * b
        print(f"{a} * {b} => {memory[loc]} @ {loc}")

    @staticmethod
    def input(memory: List[int], program_input: int, loc: int):
        memory[loc] = program_input
        print(f"{program_input} => {memory[loc]} @ {loc}")

    @staticmethod
    def output(memory: List[int], value: int):
        print("OUTPUT:", value)


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

        advance_count = operation.run(memory, i, program_input)
        i += advance_count


def part1(inputs):
    execute_program(inputs, [1])


if __name__ == '__main__':
    with open('../input.txt') as f:
        inputs = [int(item) for item in f.read().rstrip().split(',')]

    part1(inputs)
