import enum
import sys
from typing import List, Optional, Tuple


class TileState(enum.Enum):
    OCCUPIED = '#'
    EMPTY = '.'


class Grid:
    def __init__(self, grid: List[List[TileState]], parent: 'Grid' = None, child: 'Grid' = None):
        self.grid = grid
        self.parent = parent
        self.child = child

    # Will run a generation of the game. If recursie is true, then the child grid will be checked.
    def run_generation(self, recurse: bool = True, visited: Optional[List['Grid']] = None):
        if visited is None:
            visited = []

        visited.append(self)
        res = self.copy()

        for row, row_items in enumerate(self.grid):
            for col in range(len(row_items)):
                if recurse and (row, col) == self._get_center():
                    continue

                num_occupied_adjacent = self._get_num_occupied_adjacent(row, col, recurse)
                if self.grid[row][col] == TileState.EMPTY and num_occupied_adjacent in (1, 2):
                    res[row][col] = TileState.OCCUPIED
                elif num_occupied_adjacent != 1:
                    res[row][col] = TileState.EMPTY

        if recurse:
            center_row, center_col = self._get_center()
            # A child generation only needs to run if we have any tiles adjacent to it
            if self.child not in visited and (self.child is not None or self._get_num_occupied_adjacent(center_row, center_col, False) > 0):
                self._make_child()
                self.child.run_generation(recurse, visited)

            if self.parent not in visited and (self.parent is not None or self._get_num_occupied_at_edges() > 0):
                self._make_parent()
                self.parent.run_generation(recurse, visited)

        self.grid = res

    # Gets the numebr of occupied tiles adjacent to a certain cell. If recurse is true, then the child grid will
    # be checked.
    def _get_num_occupied_adjacent(self, row: int, col: int, recurse: bool) -> int:
        adjacent_count = 0
        for d_row, d_col in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            row_candidate, col_candidate = (row + d_row, col + d_col)
            if (0 <= row_candidate < len(self.grid) and 0 <= col + d_col < len(self.grid[row_candidate])
                    and (not recurse or (row_candidate, col_candidate) != self._get_center())):
                adjacent_count += 1 if self.grid[row_candidate][col_candidate] == TileState.OCCUPIED else 0

        if not recurse:
            return adjacent_count

        adjacent_count += self._get_num_occupied_adjacent_in_child(row, col)
        adjacent_count += self._get_num_occupied_adjacent_in_parent(row, col)

        return adjacent_count

    def _get_num_occupied_adjacent_in_child(self, row: int, col: int) -> int:
        if self.child is None:
            return 0

        center_row, center_col = self._get_center()
        d_row, d_col = (row - center_row, col - center_col)
        # We must be adjacent to one of the four sides of the center tile
        if (d_row, d_col) not in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            return 0

        if d_row == 0:
            # The column should either be the rightmos column or 0
            col_to_scan = max(0, d_col * (len(self.child[0]) - 1))
            return [row_items[col_to_scan] for row_items in self.child].count(TileState.OCCUPIED)
        elif d_col == 0:
            # The row should either be the bottom row or 0
            row_to_scan = max(0, d_row * (len(self.child) - 1))
            return self.child[row_to_scan].count(TileState.OCCUPIED)

    def _get_num_occupied_adjacent_in_parent(self, row: int, col: int) -> int:
        if self.parent is None:
            return 0
        # If the item we're checking is not on an edge, then don't check it
        elif not (row in (0, len(self.grid) - 1) or col in (0, len(self.grid[len(self.grid) - 1]) - 1)):
            return 0

        adjacent_count = 0
        parent_center_row, parent_center_col = self.parent._get_center()
        if row == 0:
            adjacent_count += 1 if self.parent[parent_center_row - 1][parent_center_col] == TileState.OCCUPIED else 0
        elif row == len(self.grid) - 1:
            adjacent_count += 1 if self.parent[parent_center_row + 1][parent_center_col] == TileState.OCCUPIED else 0

        if col == 0:
            adjacent_count += 1 if self.parent[parent_center_row][parent_center_col - 1] == TileState.OCCUPIED else 0
        elif col == len(self.grid[len(self.grid) - 1]) - 1:
            adjacent_count += 1 if self.parent[parent_center_row][parent_center_col + 1] == TileState.OCCUPIED else 0

        return adjacent_count

    def _get_num_occupied_at_edges(self) -> int:
        occupied_count = 0
        for row in (0, len(self.grid)-1):
            occupied_count += self.grid[row].count(TileState.OCCUPIED)

        for col in (0, len(self.grid[len(self.grid) - 1]) - 1):
            occupied_count += [row_items[col] for row_items in self.grid].count(TileState.OCCUPIED)

        return occupied_count

    # _make_child will make a child node as we need it
    # We can't do this in __init__ because otherwise it will recurse forever
    def _make_child(self) -> None:
        if self.child is not None:
            return

        self.child = Grid([[TileState.EMPTY] * len(self.grid[row]) for row in range(len(self.grid))], parent=self)

    # _make_parent will make a parent node as we need it
    # We can't do this in __init__ because otherwise it will recurse forever
    def _make_parent(self) -> None:
        if self.parent is not None:
            return

        self.parent = Grid([[TileState.EMPTY] * len(self.grid[row]) for row in range(len(self.grid))], child=self)

    def _get_center(self) -> Tuple[int, int]:
        return (len(self.grid)//2, len(self.grid[0])//2)

    def copy(self) -> 'Grid':
        return Grid([row.copy() for row in self.grid], self.parent, self.child)

    def get_biodiversity(self):
        score = 0
        for row, row_items in enumerate(self.grid):
            for col in range(len(row_items)):
                if self.grid[row][col] == TileState.OCCUPIED:
                    score += 2 ** (row * len(self.grid[row]) + col)

        return score

    def count(self, state: TileState) -> int:
        return sum(row_items.count(state) for row_items in self.grid)

    def __getitem__(self, index: int) -> List[TileState]:
        return self.grid[index]

    def __str__(self) -> str:
        return '\n'.join(''.join(item.value for item in row) for row in self.grid)

    def __len__(self) -> int:
        return len(self.grid)

    def __eq__(self, other: 'Grid') -> bool:
        if not isinstance(other, Grid):
            return False

        return self.__dict__ == other.__dict__


def part1(grid: Grid) -> int:
    all_grids = []
    while len(all_grids) == 0 or all_grids[-1] not in all_grids[:-1]:
        grid.run_generation(recurse=False)
        all_grids.append(grid.copy())

    return all_grids[-1].get_biodiversity()


def part2(grid: Grid) -> int:
    for i in range(200):
        grid.run_generation()

    total = grid.count(TileState.OCCUPIED)

    grid_cursor = grid.child
    while grid_cursor is not None:
        total += grid_cursor.count(TileState.OCCUPIED)
        grid_cursor = grid_cursor.child

    grid_cursor = grid.parent
    while grid_cursor is not None:
        total += grid_cursor.count(TileState.OCCUPIED)
        grid_cursor = grid_cursor.parent

    return total


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        input_grid = Grid([[TileState(char) for char in line.rstrip('\n')] for line in f])

    print(part1(input_grid.copy()))
    print(part2(input_grid.copy()))
