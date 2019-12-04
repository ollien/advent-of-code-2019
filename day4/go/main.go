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

	part1Passwords := 0
	for password := lowerBound; password <= upperBound; password++ {
		if isValidPart1Password(password) {
			part1Passwords++
		}
	}

	fmt.Println(part1Passwords)
}
