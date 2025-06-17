## 2025-06-17 Lexically scoped functions


### Lexical scope

Use of a variable always refers to its next enclosing definition.

```python
def f(x : int) -> Callable[[int], int]:
    y = 4
    return lambda z: x + y + z

g = f(5)
# g : Callable[[int], int]
h = f(3)
# h : Callable[[int], int]
print(g(11) + h(15))
```

A variation:

```python
def f (x : int) -> Callable[[int], int]:
    y = 4
	return lambda x: x + y
```

The use of `x` on the last line refers to its definition in the
`lambda x:`, but *not* to the definition in `(x : int)`.
The outer definition is *shadowed* by the `lambda x:`.

Lexical scope is also known as *static* because we can figure
the definition used at any point in the program by examining
the syntax.

### Digression: Static scope vs. dynamic scope

```python
def f(x : int) -> Callable[[int], int]:
    y = 4
    return lambda z: x + y + z
def g(x : int, h : Callable ([int], int)) -> int:
	return h (36)
print (g (1, f(2)))
```

What's printed by this program? `42`!

An early version of Lisp used the last dynamically encountered
definition of each variable:

1. Evaluate `f(2)` -> `y := 4, x := 2, lambda z: x + y + z`
2. Evaluate `g( 1, ...)` (referencing the above datastructure)
3. Inside `g` we extend the datastructure to
   `x := 1, y := 4, x := 2, lambda z: x + y + z`
4. Calling it with 36:
   `z := 36, x := 1, y := 4, x := 2 | x + y + z`
    result: `41`
	
This is called *dynamic scope*. 
Eliminated from Lisp because the behavior is hard to predict.
Most languages nowadays use static scope. 
Except emacs-lisp...


### Free variables

Example: In `lambda z: x + y + z`, the variables `x` and `y` occur
free and `z` occurs bound.
From the subexpression `x + y + z` we obtain `{x, y, z}` as free
variables and `{z}` is the set of bound variables, so in total
`{x, y, z} \ { z} = {x, y}`


### Closure representations: flat vs. nested

How do we represent `lambda z: x + y + z` at run time.
1. in the interpreter
2. in the compiled code

In the interpreter, the environment is represented by a linked list of
dictionaries.
The top-level list corresponds to the innermost (next enclosing)
scope.
Example:
```python
def f(x : int) -> Callable[[int], int]:
    y = 4
    return lambda z: x + y + z
```

In the body of the lambda, we have

>  {z: _}                                  # body of the lamdba
>  {x: _, y: _}                           # body of f
>  {f: VFunction(...), g:_, h:_}    # top-level program scope

represented by the `RTEnv` structure.
This is already a nested closure representation!

In the compiled code, we could do the same arrangement.
Instead of using dictionaries, we would use vectors (lists).
Instead of indexing with variable names, we'd compile them to indices
into the respective list.
But: we need two numbers to address a variable:
1. indicates the number of parent links to traverse
2. the index into the vector addressed by the traversal.

Example:
* z -> (0, 0)
* x -> (1, 0)
* y -> (1, 1)
* f -> (2, 0)

Verdict: it has been done, but it's often inefficient and leads to
problems in connection with mutually recursive functions.

In contrast, the flat representation (of a closure) just consists of a
pair (tuple of values of the free variables, pointer to the code).
(or the other way round...)


### Bidirectional type checking



### Make variable names unique

Some passes of the compiler become simpler if every (local) variable
is only bound once inside a function definition. This way, the pass
can ignore the binding structure.

Counterexample:

```python
def f(x:int, y:int) -> Callable[[int], int]:
	g : Callable[[int],int] = (lambda x: x + y)
	h : Callable[[int],int] = (lambda y: x + y)
	x = input_int()
	return g

print(f(0, 10)(32))
```

In line 2...

The program fragment transforms to:

```python
def f(x_0:int, y_1:int) -> Callable[[int], int]:
	g_2 : Callable[[int],int] = (lambda x_3: x_3 + y_1)
	h_4 : Callable[[int],int] = (lambda y_5: x_0 + y_5)
	x_0 = input_int()
	return g_2

print(f(0, 10)(32))
```

(Mostly for convenience, to simplify the subsequent passes.)


### Assignment and lexically scoped functions

What's the correct output of this program?

```python
def g(z : int) -> int:
	x = 0
	y = 0
    f : Callable[[int],int] = lambda a: a + x + z
	x = 10
	y = 12
	return f(y)

print(g(20))
```

42







Another interesting program.


```python
def f():
	x = 0
	g = lambda: x
	x = 42
	return g

print(f()())
```

Also outputs 42 (not 0)!


### Assignment conversion

*Every problem in CS can be solved by introducing an indirection* (Wheeler)

Example

```python
def g(x : int) -> int:
	x = 0
	f : Callable[[int],int] = lambda a: a + x
	x = 10
	return f(32)
```

Whenever a variable may be assigned and occurs free in the body of a
lambda, then we box this variable (introduce an indirection by putting
the value into a 1-tuple on the heap = box).

Transformed example:

* we must not change the way parameters are passed!

```python
def g(x : int) -> int:
    x = ( x ,)
	f : Callable[[int],int] = lambda a: a + x[0]
	x[0] = 10
	return f(32)
```

For the transformation, calculate

1. the set of variables that occurs free in a lambda
2. the set of variables that are assigned to

Take the intersection of these sets: those are the candidaates for boxing.
