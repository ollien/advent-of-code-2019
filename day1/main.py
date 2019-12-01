#!/usr/bin/env python3
import functools


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


# Somewhat of a weird solution, but by combining reduce with a recursive solution, we can get the correct answer :)
def part2_alternate():
    input_file = open('input.txt', 'r')

    def reducer(total, cost):
        next_cost = cost//3 - 2
        if next_cost <= 0:
            # If the next cost is less than or equal to zero, the current cost we have is the total cost
            return total

        return total + reducer(next_cost, next_cost)

    total = functools.reduce(reducer, (int(line) for line in input_file), 0)

    print(total)
    input_file.close()


if __name__ == '__main__':
    part1()
    part2()
    part2_alternate()
