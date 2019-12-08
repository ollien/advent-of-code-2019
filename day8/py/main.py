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


def part1(layers: Tuple[Tuple[str]]) -> int:
    fewest_zero_layer = min((layer for layer in layers), key=lambda layer: layer.count(0))

    return fewest_zero_layer.count(1) * fewest_zero_layer.count(2)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: ./main.py in_file width height")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input = [int(char) for char in f.read().strip()]

    width = int(sys.argv[2])
    height = int(sys.argv[3])

    layers = make_layers(input, width, height)
    print(part1(layers))
