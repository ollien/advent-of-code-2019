use std::fs;
use std::process;

const DESIRED_RESULT: i32 = 19690720;

enum Opcode {
	Add = 1,
	Mult  = 2,
	Terminate = 99
}

#[derive(Clone)]
struct Program {
	memory: Vec<i32>
}

impl Program {
	fn execute(&self, param1: i32, param2: i32) -> Result<i32, String> {
		let mut local_memory = self.memory.clone();
		local_memory[1] = param1;
		local_memory[2] = param2;
		for i in (0..local_memory.len()).step_by(4) {
			let item = local_memory[i];
			let operation = match item {
				item if item == Opcode::Add as i32 => {
					std::ops::Add::add
				},
				item if item == Opcode::Mult as i32 => {
					std::ops::Mul::mul
				},
				item if item == Opcode::Terminate as i32 => {
					 break;
				},
				_ => {
					return Err("Bad Opcode".to_string());
				}
			};

			let param_a_index = local_memory[i + 1] as usize;
			let param_b_index = local_memory[i + 2] as usize;
			let out_index = local_memory[i + 3] as usize;
			local_memory[out_index] = operation(local_memory[param_a_index], local_memory[param_b_index])
		}

		return Ok(local_memory[0])
	}
}

fn part1(program: &Program) -> Result<i32, String> {
	program.execute(12, 2)
}

fn part2(program: &Program) -> Result<(i32, i32), String> {
	for i in 0..100 {
		for j in 0..100 {
			let result = program.execute(i, j)?;
			if result == DESIRED_RESULT {
				return Ok((i, j))
			}
		}
	}

	Err("Could not find result".to_string())
}

fn main() {
	let raw_input = fs::read_to_string("../input.txt");
	let input = match &raw_input {
		Ok(contents) => contents
			.trim()
			.split(',')
			.map(|x| { x.parse::<i32>().unwrap() })
			.collect::<Vec<_>>(),
		Err(error) => {
			eprintln!("Could not read input: {}", error);
			process::exit(1)
		}
	};
	let program = Program{memory: input};

	match part1(&program) {
		Ok(result) => println!("{}", result),
		Err(error) => println!("{}", error)
	}

	match part2(&program) {
		Ok(result) => println!("{:?}", result),
		Err(error) => println!("{}", error)
	}
}
