package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

func isValidPart1Password(password int) bool {
	passwordStr := strconv.Itoa(password)
	if len(passwordStr) != 6 {
		return false
	}

	hasDoubleDigitPair := false
	for i := range passwordStr[1:] {
		// Convert each byte (in ASCII) to its numeric counterpart
		digitA := int(passwordStr[i] - '0')
		digitB := int(passwordStr[i+1] - '0')
		if digitB < digitA {
			return false
		} else if digitB == digitA {
			hasDoubleDigitPair = true
		}
	}

	return hasDoubleDigitPair
}

// getAllPart1Passwords gets all valid passwords for part 1 in [lowerBound, upperBound]
func getAllPart1Passwords(lowerBound, upperBound int) []int {
	res := []int{}
	for password := lowerBound; password <= upperBound; password++ {
		if isValidPart1Password(password) {
			res = append(res, password)
		}
	}

	return res
}

func isValidPart2Password(password int) bool {
	// The part 2 rules are stricter than part 1; they must be a valid part 1 password
	if !isValidPart1Password(password) {
		return false
	}

	passwordStr := strconv.Itoa(password)
	for _, char := range passwordStr {
		// Because we know the digits must already be ascending, we know that there must be exactly two of one of the
		// characters, and if there is more than one, they must be next to each other
		if strings.Count(passwordStr, fmt.Sprintf("%c", char)) == 2 {
			return true
		}
	}

	return false
}

func main() {
	if len(os.Args) != 3 {
		fmt.Println("Usage: ./main lower_bound upper_bound")
		os.Exit(1)
	}

	lowerBound, err := strconv.Atoi(os.Args[1])
	if err != nil {
		panic(fmt.Sprintf("could not parse lower bound: %s", err))
	}
	upperBound, err := strconv.Atoi(os.Args[2])
	if err != nil {
		panic(fmt.Sprintf("could not parse upper bound: %s", err))
	}

	part1Passwords := getAllPart1Passwords(lowerBound, upperBound)
	fmt.Println(len(part1Passwords))

	// We can save some computation by just going over our existing part 1 passwords for part 2
	numPart2Passwords := 0
	for _, password := range part1Passwords {
		if isValidPart2Password(password) {
			numPart2Passwords++
		}
	}

	fmt.Println(numPart2Passwords)
}
