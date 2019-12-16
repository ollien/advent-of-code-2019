import sys
import math
from typing import Tuple

BASE_PATTERN = (0, 1, 0, -1)


def stretch_pattern(i: int, length: int) -> Tuple[int, ...]:
    pattern = []
    for item in BASE_PATTERN:
        pattern += [item] * min(i + 1, length)
        if len(pattern) >= length:
            break

    trimmed_pattern = pattern[:length]
    if len(trimmed_pattern) < length:
        trimmed_pattern = trimmed_pattern * int(math.ceil((length / len(trimmed_pattern))))
        trimmed_pattern = trimmed_pattern[:length]

    return trimmed_pattern


def run_pattern_round(input_num: str) -> str:
    res = ''
    for i in range(len(input_num)):
        pattern = stretch_pattern(i, len(input_num) + 1)[1:]
        total = 0
        for pattern_digit, digit in zip(pattern, input_num):
            total += pattern_digit * int(digit)
        res += str(abs(total) % 10)

    return res


def part1(input_num: str):
    res = input_num
    for i in range(100):
        res = run_pattern_round(res)

    return res[:8]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input_num = f.read().rstrip('\n')

    print(part1(input_num))
