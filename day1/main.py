#!/usr/bin/env python3


def part1():
    with open('input.txt', 'r') as f:
        print(sum(int(line)//3 - 2 for line in f))


def part2():
    with open('input.txt', 'r') as f:
        modules = [int(line) for line in f]

    total = 0
    for module in modules:
        next_cost = module//3 - 2
        while next_cost >= 0:
            total += next_cost
            next_cost = next_cost // 3 - 2

    print(total)


if __name__ == '__main__':
    part1()
    part2()
