import enum
import sys
from typing import List


class TileState(enum.Enum):
    OCCUPIED = '#'
    EMPTY = '.'


class Grid:
    def __init__(self, grid: List[List[TileState]]):
        self.grid = grid

    def run_generation(self):
        res = self.copy()

        for row, row_items in enumerate(self.grid):
            for col in range(len(row_items)):
                adjacent_tiles = [self.grid[row + d_row][col + d_col] for (d_row, d_col) in ((0, 1), (1, 0), (0, -1), (-1, 0))
                                  if 0 <= row + d_row < len(self.grid) and 0 <= col + d_col < len(row_items)
                                  ]
                if self.grid[row][col] == TileState.EMPTY and adjacent_tiles.count(TileState.OCCUPIED) in (1, 2):
                    res[row][col] = TileState.OCCUPIED
                elif adjacent_tiles.count(TileState.OCCUPIED) != 1:
                    res[row][col] = TileState.EMPTY

        self.grid = res

    def copy(self) -> 'Grid':
        return Grid([row.copy() for row in self.grid])

    def get_biodiversity(self):
        score = 0
        for row, row_items in enumerate(self.grid):
            for col in range(len(row_items)):
                if grid[row][col] == TileState.OCCUPIED:
                    score += 2 ** (row * len(self.grid[row]) + col)

        return score

    def __getitem__(self, index: int) -> List[TileState]:
        return self.grid[index]

    def __str__(self) -> str:
        return '\n'.join(''.join(item.value for item in row) for row in self.grid)

    def __len__(self) -> int:
        return len(self.grid)

    def __eq__(self, other: 'Grid') -> bool:
        if not isinstance(other, Grid):
            return False

        return all(self.grid[row] == other[row] for row in range(len(self.grid)))


def part1(grid: Grid) -> int:
    all_grids = []
    while len(all_grids) == 0 or all_grids[-1] not in all_grids[:-1]:
        grid.run_generation()
        all_grids.append(grid.copy())

    return all_grids[-1].get_biodiversity()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        grid = Grid([[TileState(char) for char in line.rstrip('\n')] for line in f])

    print(part1(grid))
