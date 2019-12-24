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


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = [parse_command(line.rstrip('\n')) for line in f]

    print(part1(inputs))
