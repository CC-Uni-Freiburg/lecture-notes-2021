---
instructor: Prof. Dr. Peter Thiemann
author: Peter Thiemann
date: 2025-07-01
title: Lecture notes on dataclasses
---
# Data classes

Moving towards the goal of supporting classes with single
inheritance. First step: support for immutable data classes, i.e., classes
without methods and without inheritance. (No assignment to fields.)

Example code snippet:

```python
class RGB:
    red: int
	green: int
	blue: int

def intensity (v: RGB) -> int:
    return v.red + v.green + v.blue

def test():
    r = RGB(100,24,0)
	print(intensity(r))
```









# Abstract syntax representation

New expression: field access

```python
@dataclass
class EField:
    e: Expr
    name: Id
    idx: Optional[int] = None
```

THe `idx` field contains the position of the addressed field in the
class declaration. For instance the encoding of `v.green`:

```python
EField( "v" ... , "green", 1)
EField( "v" ... , "red", 0)
```

This information is used for code generation.


New statement: class definition

```python
@dataclass(frozen=True)
class SClass:
    name: Id
    fields: IList[tuple[Id, Type]]
```








# Type checking data classes

Guidelines

* Class definitions are statements and can appear anywhere a statement
  is allowed
* Class definitions are scope global (i.e.., forward
  references in function bodies and types are allowed)
* Class definitions can appear in the body of a function to define
  local types
* Names of class definitions must be unique.














## Typing rules

Expressions: field access, constructor calls

We write `C( f1:t1, ..., fn:tn )` for a class type `C` with fields
`f1 ... fn`.

    ctx |- e : C( f1:t1, ..., fn:tn )
	f == fj
    ---------------------------------
    ctx |- e.f : tj








Each class definition for  `C( f1:t1, ..., fn:tn )` defines a global
constructor function `C` of type  `( t1, ..., tn ) -> C`.
The standard rule for function call takes care of the constructor.






Statements: class statement

    ctx (C) = (t1, ..., tn) -> C
	--------------------------------
    ctx |- class C: f1:t1; ... fn:tn

This rule is nondeterministic because we have to guess the context in
the beginning.



## Implementation

Representation of class types.

```python
@dataclass
class TClass:
    name: Id
    _fields: Optional[IList[tuple[Id, Type]]] = None
```





### Toplevel.

Three passes.
The first pass collects all dataclass definitions and enters their constructors in
the context.
The second pass collects all function definitions.
The third pass typechecks all function bodies and the top-level
statements.

### Function body

In a function body, the constructor is entered in the environment as
we execute it. It can only be used by subsequent statements.





# Semantics of data classes

There are three new values.

```python
@dataclass(frozen=True)
class VClass:
    name: Id
	## here is the place for a dict of methods

@dataclass
class VObject:
    classref: VClass
    fields: IList[tuple[Id, Value]]

@dataclass
class VConstructor:
    name: Id
    fields: IList[Id]
```

The `VClass` value is unique. It determines the class identity, if it
comes to comparing classes. In Python, it would be returned by the
`type` operation.

A `VObject` value is generated for each invocation of the
constructor. It contains the values of all fields.

A `VConstructor` value encodes the object constructor.
See `apply`.


# Code generation

See exercise.



# Extension

Union types and type test (or pattern matching).

Primitive function `type` returns the class object of the type of its
argument value.

```
type : Any -> Class
```

(The implementation of `type` applied to a class instance just returns
the `classref` field, a `VClass` object.)



New type syntax `t1 | ... | tn`  for the union type of `t1` ... `tn`.


So far, matching of types was always exact (i.e., for equality / equivalence).
Now we need the concept of *subtyping*.
We write `s <: t` for *s is a subtype of t*.
Intention: whereever a value of type `t` is expected, we can also pass
a value of type `s`.
(Liskov's substitution principle)
In most OO languages, if A is a subclass of B, then A is also a
subtype of B. (OO-style polymorphism.)




Typing requires a *subsumption rule*

    ctx |- e : t
	t <: t'
	------------------
	ctx |- e : t'

Example: 

```python
class B:
	b : int

class A(B):
	a : int
```

Subtyping: `A <: B`
Subsumption: (in this context) allows us to ignore fields that were
introduced by inheritance.

In the context of unions, subsumption allows us to introduce extra alternatives.


This is driven by another *subtyping judgment* `|- t1 <: t2`, a binary
relation which is reflexive and transitive and obeys the following rules:

    1 <= i <= n
    -----------------------
    |- ti <: t1 | ... | tn
	



    s <: t
	ti <: si  (1 <= i <= n)
    --------------------------------------------------
    |- (s1, ..., sn) -> s  <:  (t1, ..., tn) -> t

The subtyping relation is *covariant* in the return type and
*contravariant* (i.e., its direction swaps) in the argument types.

Example:

Suppose we expect a function of type `int -> int`
but I only have a function of type `(bool | int) -> int`.

Suppose we expect a function of type `A -> int`
but I only have a function of type `B -> int`.

Final remark:

Bidirectional typing can nicely deal with subsumption.
COnsider the rule where we change direction:


    ctx |- e => s
	|- s <: t
    --------------------
    ctx |- e <= t
