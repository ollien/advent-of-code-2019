use std::fs;
use std::process;

fn get_cost(n: &i32) -> i32 {
	return n/3 - 2
}

fn part1(input: &Vec<i32>) -> i32 {
	input
		.iter()
		.map(get_cost)
		.sum()
}

fn part2(input: &Vec<i32>) -> i32 {
	let mut total_cost = 0;
	for item in input {
		let mut next_cost = get_cost(item);
		while next_cost >= 0 {
			total_cost += next_cost;
			next_cost = get_cost(&next_cost);
		}
	}

	total_cost
}

fn main() {
	let raw_input = fs::read_to_string("../input.txt");
	let input = match &raw_input {
		Ok(contents) => contents
            .trim()
			.split('\n')
			.map(|x| { x.parse::<i32>().unwrap() })
			.collect::<Vec<_>>(),
		Err(error) => {
			eprintln!("Could not read input: {}", error);
			process::exit(1)
		}
	};

	println!("Part 1: {}", part1(&input));
	println!("Part 2: {}", part2(&input));
}
