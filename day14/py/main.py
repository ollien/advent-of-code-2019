import sys
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


# Element is a node in a graph used to represent the dependencies amongst reactions (not the quantities themselves)
class Element:
    FUEL_ELEMENT = 'FUEL'
    ORE_ELEMENT = 'ORE'

    def __init__(self, name: str):
        self.name = name
        self.possible_inputs = set()
        self.possible_outputs = set()

    def __repr__(self) -> str:
        return f'<Element: {self.name}>'


@dataclass
class Reaction:
    # We can have many inputs
    inputs: Dict[Element, int]
    # We only have one output
    output: Tuple[Element, int]

    @classmethod
    def from_input_str(cls, s: str):
        REACTION_DELIM = ' => '
        INPUT_DELIM = ', '
        ELEMENT_DELIM = ' '
        raw_inputs, raw_output = s.split(REACTION_DELIM)
        split_output = raw_output.split(ELEMENT_DELIM)
        output = (Element(split_output[1]), int(split_output[0]))

        inputs = {}
        for raw_input in raw_inputs.split(INPUT_DELIM):
            split_input = raw_input.split(ELEMENT_DELIM)
            inputs[Element(split_input[1])] = int(split_input[0])

        return cls(inputs, output)

    def __repr__(self) -> str:
        inputs = ', '.join(f'{count} {element.name}' for element, count in self.inputs.items())
        return inputs + f' => {self.output[1]} {self.output[0].name}'


# Parses all of the output, returns a list of all of the reactions and the FUEL element
def parse_reaction_list(input_lines: str) -> Tuple[List[Reaction], Element]:
    elements = {Element.ORE_ELEMENT: Element(Element.ORE_ELEMENT)}
    reactions = [Reaction.from_input_str(line) for line in input_lines]
    for reaction in reactions:
        output_element = reaction.output[0]
        elements[output_element.name] = output_element

    # Once we add all reactions, add neighbors for the elements
    for reaction in reactions:
        output_element = elements[reaction.output[0].name]
        reaction_inputs = reaction.inputs.copy()
        for reaction_input_element, quantity in reaction_inputs.items():
            input_element = elements[reaction_input_element.name]
            # Noramlize the elemnts in the reaction list to all point to the same instance of that element.
            del reaction.inputs[reaction_input_element]
            reaction.inputs[input_element] = quantity
            output_element.possible_inputs.add(input_element)
            input_element.possible_outputs.add(output_element)

    return reactions, elements[Element.FUEL_ELEMENT]


def find_ore_required_for_fuel_amount(fuel_amount: int, reactions: List[Reaction], fuel_element: Element):
    surplus_elements = {}
    # Counts how many times a reaction with index i is run
    reaction_counts = {}
    # Maps a reaction's output to its reaction
    reaction_map = {reaction.output[0].name: (i, reaction) for i, reaction in enumerate(reactions)}

    def generate_reaction_counts(element: Element, num_required: int):
        if element.name == Element.ORE_ELEMENT:
            return

        num_surplus = surplus_elements.get(element.name, 0)
        i, reaction = reaction_map[element.name]
        num_missing = num_required - num_surplus
        # If we already have enough elements, we're done.
        if num_missing <= 0:
            # Store how many our new suplus is
            surplus_elements[element.name] = num_surplus - num_required
            return

        reactions_required = int(math.ceil(num_missing / reaction.output[1]))
        surplus_elements[element.name] = (num_surplus - num_required) + reactions_required * reaction.output[1]
        reaction_count = reaction_counts.get(i, 0)
        reaction_counts[i] = reaction_count + reactions_required

        for input_element, count in reaction.inputs.items():
            generate_reaction_counts(input_element, count * reactions_required)

    # Run our recursive algorithm to calculate how many reactions are required
    generate_reaction_counts(fuel_element, fuel_amount)
    num_ore_required = 0
    for i, count in reaction_counts.items():
        for input_element, reaction_input_count in reactions[i].inputs.items():
            if input_element.name == Element.ORE_ELEMENT:
                num_ore_required += count * reaction_input_count

    return num_ore_required


def part1(reactions: List[Reaction], fuel_element: Element) -> int:
    return find_ore_required_for_fuel_amount(1, reactions, fuel_element)


def part2(reactions: List[Reaction], fuel_element: Element) -> int:
    THRESHOLD = 1000000000000
    fuel_amount = 1
    low = None
    high = None
    required_ore = None
    # Bound the problem by finding a range in which our answer could be
    while required_ore is None or required_ore < THRESHOLD:
        required_ore = find_ore_required_for_fuel_amount(fuel_amount, reactions, fuel_element)
        if required_ore >= THRESHOLD:
            high = fuel_amount
            low = fuel_amount // 2
            break

        fuel_amount *= 2

    # Binary search our answers, looking for the fuel amount that gives us the most ore.
    best_fuel_amount = None
    while low <= high:
        fuel_amount = (low + high) // 2
        required_ore = find_ore_required_for_fuel_amount(fuel_amount, reactions, fuel_element)
        if required_ore >= THRESHOLD:
            high = fuel_amount - 1
        else:
            if best_fuel_amount is None or fuel_amount > best_fuel_amount:
                best_fuel_amount = fuel_amount
            low = fuel_amount + 1

    return best_fuel_amount


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./main.py in_file")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        lines = f.read().rstrip('\n').split('\n')
        reactions, fuel_element = parse_reaction_list(lines)

    print(part1(reactions, fuel_element))
    print(part2(reactions, fuel_element))
