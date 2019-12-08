import sys
from typing import Tuple


def make_layers(input: Tuple[int], width: int, height: int) -> Tuple[Tuple[int]]:
    layers = []
    # There should be height * width items in a given layer
    num_layers = len(input) // (height * width)
    for i in range(num_layers):
        start = i * height * width
        end = (i + 1) * height * width
        layers.append(tuple(input[start:end]))

    return tuple(layers)


def stack_layers(layers: Tuple[Tuple[str]], width: int, height: int) -> Tuple[int]:
    merged_stacks = []
    for i in range(height):
        for j in range(width):
            stack = []
            for layer in layers:
                stack.append(layer[i * width + j])
            try:
                pixel = next(item for item in stack if item != 2)
            except StopIteration:
                pixel = 0

            merged_stacks.append(pixel)

    return tuple(merged_stacks)


def part1(layers: Tuple[Tuple[str]]) -> int:
    fewest_zero_layer = min((layer for layer in layers), key=lambda layer: layer.count(0))

    return fewest_zero_layer.count(1) * fewest_zero_layer.count(2)


def part2(layers: Tuple[Tuple[str]], width: int, height: int) -> int:
    stacked = stack_layers(layers, width, height)
    for i in range(height):
        for j in range(width):
            pixel = stacked[i * width + j]
            print('#' if pixel == 1 else ' ', end=' ')
        print('')


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: ./main.py in_file width height")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input = [int(char) for char in f.read().strip()]

    width = int(sys.argv[2])
    height = int(sys.argv[3])

    layers = make_layers(input, width, height)
    print("PART 1")
    print(part1(layers))
    print("PART 2")
    part2(layers, width, height)
