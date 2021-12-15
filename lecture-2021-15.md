---
instructor: Prof. Dr. Peter Thiemann
tutor: Fabian Krause
date: 2021-12-15
title: Toplevel Functions, part 2
---

# assigned reading: chapter 7.3 - end of chapter 7

# chapter 8...

Free variables (free occurrence of variable) in an expression.

Define FV(exp) by cases on expressions (exp) to return the set of free variables in exp:

FV(int) = {}
FV(input_int()) = {}
FV(-exp)  = FV (exp)
FV(exp1+exp2) = FV(exp1) U FV (exp2)
FV(exp1-exp2) = FV(exp1) U FV (exp2)

FV(var) = {var}

FV(True) = FV(False) = {}
FV(exp1 and exp2) = FV(exp1 or exp2) = FV(exp1) U FV (exp2)
FV (not exp)  = FV (exp)
FV (exp1 cmp exp2) = FV(exp1 U exp2)
FV(exp1 if exp2 else exp3) = FV (exp1) U FV(exp2) U FV(exp3)

FV (exp1, ..., expn)  = FV(exp1) U ... U FV(expn)

FV (exp0 (exp1, ..., expn)) = FV(exp0) U FV (exp1) U ...

FV (lambda var1, ..., varn: exp) = FV (exp) \ var1 \ var2 \ ... \ varn


When defining a function locally, we need a datastructure to remember the current values of the free variables!

A **function closure**.

There are different approaches to the layout of closures.
We choose the simplest **flat closures**, which provides the values of the free variables as a tuple.

In the presence of closures, we move from a representation of functions by pointers to a representation of functions as closures -> we store the function pointer in the first slot of the closure!

After assignment conversion, a closure contains either the value of the free variable or the pointer to the box containing its current value.  The address of the box does not change, but its content may!


# use of tuples in chapter 8

In Python, tuples are immutable (can't be assigned to, can't be changed).
In the compiler IL, we actually need  a vector type that *is* mutable.
So we misuse tuples and freely assign to the components. 

# closures for top-level functions

just a one-tuple with the function's address!

We get an extra indirection to access this address.

In the example fig 8.8, there is lots of potential for optimization.

* we could allocate a single closure for a top-level function and reuse
* when calling a top-level function, we can ignore its closure argument
* when calling the function directly, we can still just use its address immediately. (but observe the different calling convention).

A closure for function f is only needed, really, if the function f is passed as a parameter or returned from a function.

# reading for next Wednesday: (rest of) chapter 8, peek into chapter 9

