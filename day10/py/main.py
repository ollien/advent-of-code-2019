import sys
import copy
import fractions
import math
from typing import List, Iterable, Tuple


ASTEROID_CHAR = '#'
SPACE_CHAR = '.'

# Get the coordinates of all items in a line
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


# Spread a set of coordinates into all quadrants (e.g. (1,1) will produce (1,1) (1,-1) (-1,1) (-1,-1)
def put_items_in_all_quadrants(items: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    mirrored = set()
    for item in items:
        for i in (-1, 1):
            for j in (-1, 1):
                mirrored.add((i * item[0], j * item[1]))

    return list(mirrored)


# Start a list of slopes clockwise, starting at pi/2
def sort_slopes_clockwise(items: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    # math.atan(-x[0]/abs(x[0])) allows us to get the correct positive/negative infinity for arctan
    # (remember, our coords are flipped from a standard coordinate plane)
    sort_key = lambda x: math.atan(-x[0]/abs(x[0]) * math.inf if x[1] == 0 else -x[0]/x[1])
    quad_1_3_items = sorted((item for item in items if item[1] >= 0), reverse=True, key=sort_key)
    quad_2_4_items = sorted((item for item in items if item[1] < 0), reverse=True, key=sort_key)

    return quad_1_3_items + quad_2_4_items


def generate_all_slopes(height: int, width: int) -> Tuple[Tuple[int, int]]:
    # Get all slopes in the first quadrant
    quad_slopes = set()
    used_slopes = set()
    for rise in range(height):
        for run in range(width):
            effective_rise, effective_run = rise, run
            if rise == 0 and run == 0:
                continue
            elif run == 0:
                slope_fraction = math.inf
            else:
                slope_fraction = fractions.Fraction(rise, run)
                effective_rise, effective_run = slope_fraction.numerator, slope_fraction.denominator

            if slope_fraction in used_slopes:
                continue

            used_slopes.add(slope_fraction)
            quad_slopes.add((effective_rise, effective_run))

    # Spread them across the rest of the coordinates
    slopes = put_items_in_all_quadrants(quad_slopes)

    return sort_slopes_clockwise(slopes)


# Get all asteroids that are visible from a certian point, marking whether to destroy them on scan or not
def get_visible_asteroids(space_map: List[List[int]], start_row: int, start_col: int, destroy=False) -> List[Tuple[int, int]]:
    asteroids = []
    slopes = generate_all_slopes(len(space_map), len(space_map[0]))
    for slope in slopes:
        rise, run = slope
        line_items = get_items_in_slope(space_map, start_row, start_col, rise, run)
        for row, col in line_items:
            if space_map[row][col] == ASTEROID_CHAR:
                if destroy:
                    space_map[row][col] = SPACE_CHAR
                if (row, col) not in asteroids:
                    asteroids.append((row, col))
                break

    return asteroids


def part1(input_space_map: List[List[str]]) -> Tuple[Tuple[int, int], int]:
    space_map = copy.deepcopy(input_space_map)
    best_count = None
    best_pos = None
    for i, row in enumerate(space_map):
        for j, item in enumerate(row):
            if item != ASTEROID_CHAR:
                continue
            visible_asteroid_count = len(get_visible_asteroids(space_map, i, j))
            if best_count is None or visible_asteroid_count > best_count:
                best_pos = (i, j)
                best_count = visible_asteroid_count

    return best_pos, best_count


def part2(input_space_map: Tuple[Tuple[str, ...]], station_pos: Tuple[int, int]) -> int:
    space_map = copy.deepcopy(input_space_map)
    destroyed_asteroids = []
    station_row, station_col = station_pos
    while len(destroyed_asteroids) < 200:
        destroyed_asteroids += get_visible_asteroids(space_map, station_row, station_col, True)

    asteroid = destroyed_asteroids[199]

    return asteroid[1] * 100 + asteroid[0]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = [list(line.strip()) for line in f.readlines()]

    for row in inputs:
        print(''.join(row))

    best_pos, best_count = part1(inputs)
    print(best_count)
    print(part2(inputs, best_pos))
