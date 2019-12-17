import sys
import math
from typing import Tuple, List

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


def generate_second_half(input_num: str) -> str:
    last_sum = 0
    # It is much much faster if, instead of concating a result as a string, we replace the results in a list in-place
    # We could probably make this faster if we mutated a list each time instead of making a new list, but this is
    # good enough(tm)
    input_list = [int(digit) for digit in input_num]
    for i, digit in reversed(tuple(enumerate(input_list))):
        last_sum = digit + last_sum
        input_list[i] = str(last_sum % 10)

    return ''.join(input_list)


def run_pattern_round(input_num: str, offset: int) -> str:
    res = ''
    for i in range(offset, len(input_num)//2):
        pattern = stretch_pattern(i, len(input_num) + 1)[1:]
        total = 0
        for pattern_digit, digit in zip(pattern[i:], input_num[i:]):
            total += pattern_digit * int(digit)
        res += str(abs(total) % 10)

    starting_pos = max(len(input_num)//2, offset)
    res += generate_second_half(input_num[starting_pos:])

    return res


def generate_all_pattern_rounds(input_num: str, offset: int = 0) -> str:
    res = input_num
    for i in range(100):
        length_difference = len(input_num) - len(res)
        if length_difference > len(input_num)//2:
            res = generate_second_half(res[-length_difference:])
        else:
            res = run_pattern_round(res, offset)

    return res


def part1(input_num: str) -> str:
    return generate_all_pattern_rounds(input_num)[:8]


def part2(input_num: str) -> str:
    offset = int(input_num[:7])
    return generate_all_pattern_rounds(input_num * 10000, offset)[:8]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input_num = f.read().rstrip('\n')

    print(part1(input_num))
    print(part2(input_num))
