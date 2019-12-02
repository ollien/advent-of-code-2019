import itertools


def execute_program(inputs):
    TERMINATE_OPCODE = 99
    ADD_OPCODE = 1
    MULTIPLY_OPCODE = 2

    program_memory = inputs[:]
    # Each instruction moves the instruction pointer forward by 4.
    # Iterate over the loop opcodes accordingly (stepping by 4)
    for i, opcode in itertools.islice(enumerate(program_memory), 0, None, 4):
        operation = None
        if opcode == TERMINATE_OPCODE:
            break
        elif opcode == ADD_OPCODE:
            operation = lambda a, b: a + b
        elif opcode == MULTIPLY_OPCODE:
            operation = lambda a, b: a * b
        else:
            raise Exception('Bad opcode: ' + str(opcode))

        # Get parameters of program
        input_a_index = program_memory[i + 1]
        input_b_index = program_memory[i + 2]
        out_index = program_memory[i + 3]
        # Run program with parameters
        program_memory[out_index] = operation(program_memory[input_a_index], program_memory[input_b_index])

    return program_memory[0]


def part1(inputs):
    inputs[1] = 12
    inputs[2] = 2

    return execute_program(inputs)


def part2(inputs):
    DESIRED_OUTPUT = 19690720

    for i in range(100):
        for j in range(100):
            inputs[1] = i
            inputs[2] = j
            # Execute the program, making sure we clone the inputs array so we don't reuse the list
            result = execute_program(inputs)
            if result == DESIRED_OUTPUT:
                return 100 * i + j
    else:
        raise Exception('Could not find result')


if __name__ == '__main__':
    with open('input.txt') as f:
        inputs = [int(item) for item in f.read().rstrip().split(',')]

    print(part1(inputs))
    print(part2(inputs))
