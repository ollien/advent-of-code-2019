import itertools
import sys
import re
import math
import copy
import functools


class Moon:
    INPUT_REGEXP = re.compile(r'(\w)=(-?\d*)')

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = 0
        self.y_velocity = 0
        self.z_velocity = 0

    @classmethod
    def from_input_string(cls, input_str: str) -> 'Moon':
        matches = re.findall(cls.INPUT_REGEXP, input_str)
        fields = {}
        for match in matches:
            fields[match[0]] = int(match[1])

        return cls(fields['x'], fields['y'], fields['z'])

    @property
    def potential_energy(self):
        return abs(self.x) + abs(self.y) + abs(self.z)

    @property
    def kinetic_energy(self):
        return abs(self.x_velocity) + abs(self.y_velocity) + abs(self.z_velocity)

    # Applies gravity to this moon and other moon passed in
    def apply_gravity(self, other: 'Moon') -> None:
        FIELDS = {
            'x': 'x_velocity',
            'y': 'y_velocity',
            'z': 'z_velocity'
        }

        for pos_field, velocity_field in FIELDS.items():
            self_velocity = getattr(self, velocity_field)
            other_velocity = getattr(other, velocity_field)
            self_pos = getattr(self, pos_field)
            other_pos = getattr(other, pos_field)
            if self_pos > other_pos:
                setattr(self, velocity_field, self_velocity - 1)
                setattr(other, velocity_field, other_velocity + 1)
            elif self_pos < other_pos:
                setattr(self, velocity_field, self_velocity + 1)
                setattr(other, velocity_field, other_velocity - 1)

    # Update all of the positions based on the stored velocities
    def update_position(self) -> None:
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.z += self.z_velocity

    def __repr__(self) -> str:
        return (f'pos=<x={self.x}, y={self.y}, z={self.z}> ' +
                f'vel=<x={self.x_velocity}, y={self.y_velocity}, z={self.z_velocity}>')


# Apply all physics rules ot the given list of moons
def apply_physics(moons: Moon):
    for moon_1, moon_2 in itertools.combinations(moons, 2):
        moon_1.apply_gravity(moon_2)
    for moon in moons:
        moon.update_position()


def lcm(a: int, b: int) -> int:
    return (a * b) // math.gcd(a, b)


def part1(moons: Moon) -> int:
    for i in range(1000):
        apply_physics(moons)

    return sum(moon.kinetic_energy * moon.potential_energy for moon in moons)


def part2(moons: Moon) -> int:
    VELOCITY_FIELD_SUFFIX = '_velocity'
    # Count until we hit the a 0 velocity and identical position to the starting position
    counts = {
        'x': 0,
        'y': 0,
        'z': 0,
    }

    found_cycle = {
        'x': False,
        'y': False,
        'z': False,
    }

    original_moons = copy.deepcopy(moons)
    while not all(found_cycle.values()):
        apply_physics(moons)
        for key in found_cycle:
            if found_cycle[key]:
                continue

            counts[key] += 1
            found_cycle[key] = all(getattr(original_moons[i], key) == getattr(moon, key)
                                   and getattr(moons[i], key + VELOCITY_FIELD_SUFFIX) == 0
                                   for i, moon in enumerate(moons))

    return functools.reduce(lcm, counts.values())


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        moons = [Moon.from_input_string(line.rstrip()) for line in f if len(line.rstrip()) > 0]

    print(part1(copy.deepcopy(moons)))
    print(part2(copy.deepcopy(moons)))
