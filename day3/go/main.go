package main

import (
	"errors"
	"fmt"
	"io/ioutil"
	"strconv"
	"strings"
)

// Direction represents a direction in space
type Direction byte

const (
	// DirectionUp represents the up direction
	DirectionUp Direction = 'U'
	// DirectionDown represents the down direction
	DirectionDown = 'D'
	// DirectionLeft represents the left direction
	DirectionLeft = 'L'
	// DirectionRight represents the right direction
	DirectionRight = 'R'
)

// Point represents a point in space
type Point struct {
	x int
	y int
}

// PointSet represents a set of points
type PointSet map[Point]struct{}

// DistanceTo finds the manhattan distance between p and p2
func (p Point) DistanceTo(p2 Point) int {
	return abs(p.x-p2.x) + abs(p.y-p2.y)
}

// Add adds the components of two points
func (p Point) Add(p2 Point) Point {
	return Point{
		x: p.x + p2.x,
		y: p.y + p2.y,
	}
}

// Intersection finds the intersection between set1 and set2
func (set PointSet) Intersection(set2 PointSet) PointSet {
	res := make(PointSet)

	for point := range set {
		if _, ok := set2[point]; ok {
			res[point] = struct{}{}
		}
	}

	return res
}

func abs(n int) int {
	if n < 0 {
		return n * -1
	}

	return n
}

func max(a, b int) int {
	if a > b {
		return a
	}

	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}

	return b
}

// makeDeltaPoint makes a point that represents the delta produced by the path component
func makeDeltaPoint(pathComponent string) (Point, error) {
	direction := Direction(pathComponent[0])
	distance, err := strconv.Atoi(pathComponent[1:])
	if err != nil {
		return Point{}, errors.New("Invalid number in path component")
	}

	switch direction {
	case DirectionUp:
		return Point{x: 0, y: distance}, nil
	case DirectionDown:
		return Point{x: 0, y: -distance}, nil
	case DirectionLeft:
		return Point{x: -distance, y: 0}, nil
	case DirectionRight:
		return Point{x: distance, y: 0}, nil
	default:
		return Point{}, errors.New("Invalid direction in path component")
	}
}

// NewPointSetFromPathString makes a point set of all points from the start, along each path
func NewPointSetFromPathString(path string) (PointSet, error) {
	cursor := Point{0, 0}
	pathComponents := strings.Split(path, ",")
	pointSet := make(PointSet)
	for _, component := range pathComponents {
		deltaPoint, err := makeDeltaPoint(component)
		if err != nil {
			return nil, fmt.Errorf("Could not make delta point: %s", err)
		}

		newCursor := cursor.Add(deltaPoint)
		xStart := min(cursor.x, newCursor.x)
		xEnd := max(cursor.x, newCursor.x)
		for i := xStart; i < xEnd; i++ {
			pointSet[Point{x: i, y: cursor.y}] = struct{}{}
		}

		yStart := min(cursor.y, newCursor.y)
		yEnd := max(cursor.y, newCursor.y)
		for i := yStart; i < yEnd; i++ {
			pointSet[Point{x: cursor.x, y: i}] = struct{}{}
		}

		cursor = newCursor
	}

	return pointSet, nil
}

func part1(paths []PointSet) (int, error) {
	intersections := paths[0]
	// Get all points that intersect between the paths
	for _, path := range paths[1:] {
		intersections = intersections.Intersection(path)
	}

	// We don't care about 0,0 as an intersection, as every path starts there.
	delete(intersections, Point{0, 0})

	// this bitshift represents the max int on the system
	minDistance := int(^uint(0) >> 1)
	for point := range intersections {
		distance := point.DistanceTo(Point{0, 0})
		if distance < minDistance {
			minDistance = distance
		}
	}

	return minDistance, nil
}

func main() {
	inputContents, err := ioutil.ReadFile("../input.txt")
	if err != nil {
		panic(err)
	}

	trimmedInput := strings.TrimSpace(string(inputContents))
	rawPaths := strings.Split(trimmedInput, "\n")
	paths := make([]PointSet, len(rawPaths))
	for i, rawPath := range rawPaths {
		paths[i], err = NewPointSetFromPathString(rawPath)
		if err != nil {
			panic(err)
		}
	}

	part1Res, err := part1(paths)
	if err != nil {
		panic(err)
	}

	fmt.Println(part1Res)
}
