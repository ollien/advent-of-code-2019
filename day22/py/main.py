import re
import sys
import enum
from typing import Callable, List, Tuple, Optional


class Operation(enum.Enum):
    DEAL_TO_STACK = 0
    CUT = 1
    DEAL_BY_N = 2


def deal_to_stack(deck: List[int]) -> List[int]:
    return list(reversed(deck))


def cut_n_cards(deck: List[int], n: int) -> List[int]:
    if n > len(deck):
        raise ValueError(f"Cannot cut a deck of length {len(deck)} by {n}")
    elif n == 0:
        return deck

    return deck[n:] + deck[:n]


def deal_by_n(deck: List[int], n: int) -> List[int]:
    if n <= 0:
        raise ValueError("Cannot deal with n <= 0")
    elif len(deck) % n == 0:
        raise ValueError(f"Cannot exhaust a deck of length {len(deck)} by dealing by {n}")

    # Allocate enough items to hold all of the deck items
    res = [0] * len(deck)
    i = 0
    for card in deck:
        res[i] = card
        # Increment by n, making sure we wrap around
        i = (i + n) % len(deck)

    return res


def parse_command(command: str) -> Tuple[Callable, Optional[int]]:
    if command == 'deal into new stack':
        return Operation.DEAL_TO_STACK, None

    match = re.match(r'deal with increment (\d+)', command)
    if match is not None:
        return Operation.DEAL_BY_N, int(match.groups()[0])

    match = re.match(r'cut (-?\d+)', command)
    if match is not None:
        return Operation.CUT, int(match.groups()[0])

    raise ValueError('Unknown command')


def part1(inputs: List[Operation]) -> int:
    ACTIONS = {
        Operation.DEAL_TO_STACK: deal_to_stack,
        Operation.CUT: cut_n_cards,
        Operation.DEAL_BY_N: deal_by_n
    }
    deck = list(range(10007))
    for action, arg in inputs:
        args = [] if arg is None else [arg]
        deck = ACTIONS[action](deck, *args)

    return deck.index(2019)


def get_offset_and_increment_after_operations(inputs: List[Operation], deck_size: int) -> Tuple[int, int]:
    # Most of this came from https://www.reddit.com/r/adventofcode/comments/ee0rqi/2019_day_22_solutions/fbnkaju/
    # Many thanks to /u/mcpower_ for this :)
    # Offset represents the first item in our deck, and increment represents the difference to the next item
    # (Modulating by deck_size)
    offset = 0
    increment = 1
    for operation, arg in inputs:
        if operation == Operation.DEAL_TO_STACK:
            increment = (increment * -1) % deck_size
            offset = (offset + increment) % deck_size
        elif operation == Operation.CUT:
            offset = (offset + increment * arg) % deck_size
        elif operation == Operation.DEAL_BY_N:
            # Calculate the modulcar inverse with Fermat's Little Thereom.
            # We know that arg^(deck_size - 1) = 1 (mod deck_size), and thus
            # arg^(deck_size - 2) = (deck_size)^(-1) (mod deck_size)
            modular_inverse = pow(arg, deck_size - 2, deck_size)
            # We want to find the element such that increment * arg = 1 (i.e. in the second position),
            # which, by definition, is the modular inverse. second - first = offset, and this
            # works out to increment * modular_inverse.
            increment = (increment * modular_inverse) % deck_size

    return (offset, increment)


def part2(inputs: List[Operation]) -> int:
    DECK_SIZE = 119315717514047
    NUM_SHUFFLES = 101741582076661
    offset_after_shuffle, increment_after_shuffle = get_offset_and_increment_after_operations(inputs, DECK_SIZE)
    # We know that increment = increment * k_1 and offset = offset + increment * k_2.
    # This can be expanded to a geometric sequence such that offset = k_2 * (1 - (k_1)^n)/(1 - k_1) after n shuffles
    # and increment = increment * k_1^n, and since increment = 1, increment = k_1^n.
    # We define k_1 = increment_after_shuffle and k_2 = offset_after_shuffle
    a = pow(increment_after_shuffle, NUM_SHUFFLES, DECK_SIZE)

    # Apply the geometric series formula, performing division by dividing by the modular inverse.
    b = offset_after_shuffle * (1 - a) * pow(1 - increment_after_shuffle, DECK_SIZE - 2, DECK_SIZE)

    # Get the card in the 2020th position.
    return (a * 2020 + b) % DECK_SIZE


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = [parse_command(line.rstrip('\n')) for line in f]

    print(part1(inputs))
    print(part2(inputs))
