import sys
import fractions
from typing import Tuple, Set

ASTEROID_CHAR = '#'
SPACE_CHAR = '.'


def get_items_in_slope(space_map: Tuple[Tuple[str]], start_row: int, start_col: int, rise: int, run: int) -> Tuple[Tuple[int, int]]:
    row = start_row
    col = start_col
    items = []
    while row >= 0 and col >= 0 and row < len(space_map) and col < len(space_map[row]):
        if row == start_row and col == start_col:
            row += rise
            col += run
            continue

        items.append((row, col))
        row += rise
        col += run

    return tuple(items)


def search_for_visible_in_all_directions(space_map: Tuple[Tuple[str, ...]], start_row: int, start_col: int, rise: int, run: int) -> Set[Tuple[int, int]]:
    asteroids = set()
    for i in (-1, 1):
        for j in (-1, 1):
            line_items = get_items_in_slope(space_map, start_row, start_col, i * rise, j * run)
            for row, col in line_items:
                if space_map[row][col] == ASTEROID_CHAR:
                    asteroids.add((row, col))
                    break

    return asteroids


def get_visible_asteroid_count(space_map: Tuple[Tuple[str, ...]], start_row: int, start_col: int) -> int:
    asteroids = set()
    # Because the vertical slopes are undefined, we have to search for them manually
    for row in range(start_row-1, -1, -1):
        if space_map[row][start_col] == ASTEROID_CHAR:
            asteroids.add((row, start_col))
            break

    for row in range(start_row+1, len(space_map[0])):
        if space_map[row][start_col] == ASTEROID_CHAR:
            asteroids.add((row, start_col))
            break

    used_slopes = set()
    for rise in range(0, len(space_map)):
        for run in range(1, len(space_map[0])):
            slope_fraction = fractions.Fraction(rise, run)
            if slope_fraction in used_slopes:
                continue

            used_slopes.add(slope_fraction)
            rise, run = slope_fraction.numerator, slope_fraction.denominator
            found_asteroids = search_for_visible_in_all_directions(space_map, start_row, start_col, rise, run)
            asteroids = asteroids.union(found_asteroids)

    return len(asteroids)


def part1(space_map: Tuple[Tuple[int]]):
    best_count = None
    for i, row in enumerate(space_map):
        for j, item in enumerate(row):
            if item != ASTEROID_CHAR:
                continue
            visible_asteroid_count = get_visible_asteroid_count(space_map, i, j)
            if best_count is None or visible_asteroid_count > best_count:
                best_count = visible_asteroid_count

    return best_count


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = tuple(tuple(line.strip()) for line in f.readlines())

    for row in inputs:
        print(''.join(row))

    print(part1(inputs))
