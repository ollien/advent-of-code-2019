package main

import (
	"fmt"
	"os"
	"strconv"
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

	lastChar := rune(0)
	charCount := 0
	passwordStr := strconv.Itoa(password)
	// We will define an isolated pair to be a set like 22, but not 222
	hasIsolatedRepeatedPair := false
	for _, char := range passwordStr {
		if lastChar == char {
			charCount++
		} else if hasIsolatedRepeatedPair {
			// Once we find an isolated pair, the other digits don't matter
			return true
		} else {
			charCount = 1
		}

		lastChar = char
		if charCount > 2 {
			// If the char count ever exceeds two, we need to say that we don't have an isolated pair
			hasIsolatedRepeatedPair = false
		} else if charCount == 2 {
			hasIsolatedRepeatedPair = true
		}
	}

	return hasIsolatedRepeatedPair
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
