---
instructor: Prof. Dr. Peter Thiemann
tutor: Fabian Krause
date: 2022-03-06
title: Final take home exam
---

# General

The take-home exam consists of three tasks of different complexity.
For each task you can earn 30 marks. These marks are distributed as follows:

* 10 marks for the functionality: implementation passes all test cases provided (including regression)
* 10 marks for test cases
* 5 marks for programming style and structure
* 5 marks for documentation
 
Documentation has to be provided for each task. It comprises
 
* brief explanation of background and prerequisites
* which functions have been modified or added; how and why
* for each test case: what is the purpose of the test, i.e. which aspect of the solution / which component of the compiler is tested? 
 
Useful x86-64 assembly ressources

* http://linasm.sourceforge.net/docs/instructions/index.php
* https://cs61.seas.harvard.edu/site/2021/Asm/

 
# Multiplication and Division (easy)
 
 Extend the `Lfun` language with multiplication, division, and modulo on integers to obtain `Lmul`.
 
 * Investigate the abstract syntax for these operators.
 * Extend the interpreter and type checker for `Lfun` to `Lmul`.
 * Extend the compiler accordingly.
 
Hint: use the instructions `imul`, `idiv`, and `cqo`. Do not worry about overflow or exceptions (e.g., division by zero).
 
# While (medium)

Implement `Lwhile` as presented in Chapter 5 of the book. Interpreter and type checker are provided.
The main difficulty is the overhaul of the liveness analysis. Without loops it is sufficient to perform one pass over each basic block in topological order. In the presence of loops, you must repeatly process the blocks to update the liveness information until a fixed point is reached (i.e., the liveness information does not change anymore).

# Datatype Array
 
Consider the challenge problem 6.9 of the book: implement the mutable array datatype.

For extra marks extend the multiplication operator with cases for `list` times `int` and `int` times `list`.

