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

// Path represents a path taken
type Path []Point

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

// Intersection finds the intersection between two paths
func (path Path) Intersection(path2 Path) []Point {
	res := []Point{}
	pathPointSet := make(map[Point]struct{})
	// Add all elements from the first path into the path set
	for _, point := range path {
		pathPointSet[point] = struct{}{}
	}

	for _, point := range path2 {
		if _, ok := pathPointSet[point]; ok {
			res = append(res, point)
		}
	}

	return res
}

// Index returns the index at which the point occurs in the given path
func (path Path) Index(point Point) (int, error) {
	for i, pathPoint := range path {
		if point == pathPoint {
			return i, nil
		}
	}

	return -1, errors.New("point not in path")
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

// NewPathFromPathString makes a Path from a string representing it
func NewPathFromPathString(rawPath string) (Path, error) {
	cursor := Point{0, 0}
	pathComponents := strings.Split(rawPath, ",")
	path := Path{}
	for _, component := range pathComponents {
		deltaPoint, err := makeDeltaPoint(component)
		if err != nil {
			return nil, fmt.Errorf("Could not make delta point: %s", err)
		}

		newCursor := cursor.Add(deltaPoint)
		// Trace out the paths
		// This is a bit gross, but I don't know of a better way to do it
		if cursor.x < newCursor.x {
			for i := cursor.x; i < newCursor.x; i++ {
				path = append(path, Point{x: i, y: cursor.y})
			}
		} else {
			for i := cursor.x; i > newCursor.x; i-- {
				path = append(path, Point{x: i, y: cursor.y})
			}
		}

		if cursor.y < newCursor.y {
			for i := cursor.y; i < newCursor.y; i++ {
				path = append(path, Point{x: cursor.x, y: i})
			}
		} else {
			for i := cursor.y; i > newCursor.y; i-- {
				path = append(path, Point{x: cursor.x, y: i})
			}
		}

		cursor = newCursor
	}

	return path, nil
}

func part1(paths []Path) (int, error) {
	intersections := paths[0]
	// Get all points that intersect between the paths
	for _, path := range paths[1:] {
		intersections = intersections.Intersection(path)
	}

	// this bitshift represents the max int on the system
	// https://stackoverflow.com/a/6878625
	minDistance := int(^uint(0) >> 1)
	for _, point := range intersections {
		// We don't care about 0,0 as an intersection, as every path starts there.
		if point == (Point{0, 0}) {
			continue
		}

		distance := point.DistanceTo(Point{0, 0})
		if distance < minDistance {
			minDistance = distance
		}
	}

	return minDistance, nil
}

func part2(paths []Path) (int, error) {
	intersections := paths[0]
	// Get all points that intersect between the paths
	for _, path := range paths[1:] {
		intersections = intersections.Intersection(path)
	}

	// this bitshift represents the max int on the system
	// https://stackoverflow.com/a/6878625
	minLength := int(^uint(0) >> 2)
	for _, point := range intersections {
		// We don't care about 0,0 as an intersection, as every path starts there.
		if point == (Point{0, 0}) {
			continue
		}

		length := 0
		for _, path := range paths {
			// Index will equal the path length, as 0,0 is the first item in all paths
			index, err := path.Index(point)
			if err != nil {
				return -1, fmt.Errorf("could not get index of point in path: %s", err)
			}

			length += index
		}

		if length < minLength {
			minLength = length
		}
	}

	return minLength, nil
}

func main() {
	inputContents, err := ioutil.ReadFile("../input.txt")
	if err != nil {
		panic(err)
	}

	trimmedInput := strings.TrimSpace(string(inputContents))
	rawPaths := strings.Split(trimmedInput, "\n")
	paths := make([]Path, len(rawPaths))
	for i, rawPath := range rawPaths {
		paths[i], err = NewPathFromPathString(rawPath)
		if err != nil {
			panic(err)
		}
	}

	part1Res, err := part1(paths)
	if err != nil {
		panic(err)
	}

	fmt.Println(part1Res)

	part2Res, err := part2(paths)
	if err != nil {
		panic(err)
	}

	fmt.Println(part2Res)
}
