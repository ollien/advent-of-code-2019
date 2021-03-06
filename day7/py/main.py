import sys
import itertools
from typing import List, Tuple, Optional


# Halt indicates that the assembled program should terminate
class Halt(Exception):
    pass


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
    MODE_POSITION = 0
    MODE_IMMEDIATE = 1
    ALL_OPCODES = (OPCODE_TERMINATE, OPCODE_ADD, OPCODE_MULTIPLY, OPCODE_INPUT, OPCODE_OUTPUT,
                   OPCODE_JUMP_IF_TRUE, OPCODE_JUMP_IF_FALSE, OPCODE_LESS_THAN, OPCODE_EQUALS)

    def __init__(self, instruction: int):
        # The opcode is the first two digits of the number, the rest are parameter modes
        self.opcode: int = instruction % 100
        if self.opcode not in Operation.ALL_OPCODES:
            raise ValueError(f"Bad opcode: {self.opcode}")
        self.modes: Tuple[int, ...] = self._extract_parameter_modes(instruction//100)
        self.output = None

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
        }
        # Opcodes that write to memory as their last parameter
        MEMORY_OPCODES = (Operation.OPCODE_ADD, Operation.OPCODE_MULTIPLY, Operation.OPCODE_INPUT,
                          Operation.OPCODE_LESS_THAN, Operation.OPCODE_EQUALS)

        num_parameters = PARAMETER_COUNTS[self.opcode]
        modes = [Operation.MODE_POSITION for i in range(num_parameters)]
        mode_str = str(raw_modes)
        # Iterate over the modes digits backwards, assigning them to the parameter list until we exhaust the modes
        # The rest must be leading zeroes
        for mode_index, digit in zip(range(num_parameters), reversed(mode_str)):
            modes[mode_index] = int(digit)

        # The last argument (the address parameter) must always be in immediate mode
        # The problem statement is misleading in this regard. You do NOT want to get an address to store the value
        # at from another address.
        if self.opcode in MEMORY_OPCODES:
            modes[-1] = Operation.MODE_IMMEDIATE

        return tuple(modes)

    # Run the given operation, starting at the given instruction pointer
    # Returns the address that the instruction pointer should become, followed by the output of the operation, if any
    def run(self, memory: List[int], instruction_pointer: int, program_input: Optional[int] = None) -> Tuple[int, Optional[int]]:
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
            Operation.OPCODE_EQUALS: Operation.equals
        }

        # Reset the output of a previous run
        self.output = None

        args = []
        for i, mode in enumerate(self.modes):
            # Add 1 to move past the opcode itself
            pointer = instruction_pointer + i + 1
            arg = memory[pointer]
            if mode == Operation.MODE_POSITION:
                arg = memory[arg]
            elif mode != Operation.MODE_IMMEDIATE:
                raise ValueError(f"Invalid parameter mode {mode}")

            args.append(arg)

        func = OPERATION_FUNCS[self.opcode]
        if program_input is None:
            jump_addr = func(self, memory, *args)
        else:
            jump_addr = func(self, memory, program_input, *args)

        if jump_addr is not None:
            return jump_addr, self.output

        return instruction_pointer + len(self.modes) + 1, self.output

    def terminate(self, memory: List[int]) -> None:
        raise Halt("catch fire")

    def add(self, memory: List[int], a: int, b: int, loc: int) -> None:
        memory[loc] = a + b

    def multiply(self, memory: List[int], a: int, b: int, loc: int) -> None:
        memory[loc] = a * b

    def input(self, memory: List[int], program_input: int, loc: int) -> None:
        memory[loc] = program_input

    def output(self, memory: List[int], value: int) -> None:
        self.output = value
        print("OUTPUT:", value)

    def jump_if_true(self, memory: List[int], test_value: int, new_instruction_pointer: int) -> Optional[int]:
        return new_instruction_pointer if test_value != 0 else None

    def jump_if_false(self, memory: List[int], test_value: int, new_instruction_pointer: int) -> Optional[int]:
        return new_instruction_pointer if test_value == 0 else None

    def less_than(self, memory: List[int], a: int, b: int, loc: int):
        memory[loc] = int(a < b)

    def equals(self, memory: List[int], a: int, b: int, loc: int):
        memory[loc] = int(a == b)


# Executes the program, returning the instruction pointer to continue at (if the program paused) and a list of all
# outputs that occurred during the program's execution
def execute_program(memory: List[int], program_inputs: List[int], initial_instruction_pointer: int = 0) -> (Optional[int], List[int]):
    i = initial_instruction_pointer
    input_cursor = 0
    outputs = []
    while i < len(memory):
        operation = Operation(memory[i])
        program_input = None
        # If we're looking for input
        if operation.opcode == Operation.OPCODE_INPUT:
            # If we are out of input, don't fail out, but rather just pause execution
            if input_cursor >= len(program_inputs):
                return i, outputs
            program_input = program_inputs[input_cursor]
            input_cursor += 1

        try:
            i, output = operation.run(memory, i, program_input)
        except Halt:
            break

        if output is not None:
            outputs.append(output)

    # The program is finished, and we are saying there is no instruction pointer
    return None, outputs


def part1(inputs: List[int]) -> int:
    possible_phases = list(range(5))
    max_output = 0
    for permutation in itertools.permutations(possible_phases):
        last_output = 0
        for phase in permutation:
            _, outputs = execute_program(inputs[:], [phase, last_output])
            last_output = outputs[-1]

        if last_output > max_output:
            max_output = last_output

    return max_output


def part2(inputs: List[int]) -> int:
    max_output = 0
    for phase_permutation in itertools.permutations(range(5, 10)):
        last_output = 0
        amplifiers = [{"memory": inputs[:], "next_ip": 0} for i in range(5)]
        # Go over all of the amplifiers and the phase permutation item one by one
        for amplifier, phase in itertools.cycle(zip(amplifiers, phase_permutation)):
            next_input = [last_output]
            # If the program is not currently running, add the phase as the first input
            # Passing both inputs allows us to have an output from this step
            if amplifier["next_ip"] == 0:
                next_input.insert(0, phase)

            last_ip, outputs = execute_program(amplifier["memory"], next_input, amplifier["next_ip"])
            amplifier["next_ip"] = last_ip
            # We are sure we will only get one output for this phase
            last_output = outputs[-1]
            # If none of the programs are running, stop
            if all(amplifier["next_ip"] is None for amplifier in amplifiers):
                break

        if last_output > max_output:
            max_output = last_output

    return max_output


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = [int(item) for item in f.read().rstrip().split(",")]

    print("PART 1")
    print(part1(inputs))
    print("PART 2")
    print(part2(inputs))
