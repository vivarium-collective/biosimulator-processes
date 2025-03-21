package main

import "fmt"

func main() {
	// defer works in a FILO (first in, last out) queue, so in this case Start -> C -> B -> A
	defer fmt.Println("A")
	defer fmt.Println("B")
	defer fmt.Println("C")
	fmt.Println("Start")
}
