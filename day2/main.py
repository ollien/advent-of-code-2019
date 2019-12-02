import itertools


def part1(inputs):
    inputs[1] = 12
    inputs[2] = 2
    for i, opcode in itertools.islice(enumerate(inputs), 0, None, 4):
        operation = None
        # Terminate opcode
        if opcode == 99:
            break
        elif opcode == 1:
            operation = lambda a, b: a + b
        elif opcode == 2:
            operation = lambda a, b: a * b
        else:
            raise Exception('Bad opcode: ' + str(opcode))

        input_a_index = inputs[i + 1]
        input_b_index = inputs[i + 2]
        out_index = inputs[i + 3]
        inputs[out_index] = operation(inputs[input_a_index], inputs[input_b_index])

    return inputs[0]


if __name__ == '__main__':
    with open('input.txt') as f:
        inputs = [int(item) for item in f.read().rstrip().split(',')]

    print(part1(inputs))
