---
instructor: Prof. Dr. Peter Thiemann
author: Peter Thiemann
date: 2025-06-24
title: Lecture notes for chapter 12
---

# Type checking LGen

* top-level functions with type annotations and *generics*

```python
def map[T](f : Callable[[T],T], tup : tuple[T,T]) -> tuple[T,T]:
  return (f(tup[0]), f(tup[1]))

def add1(x : int) -> int:
  return x + 1

t = map(add1, (0, 41))
print(t[1])
```

Now `map` works for any instantiation of `T` with a type, for example
`{ T : int }`, then (see `map_int` below).

A better type signature for `map` (actually, the best possible):

```
def map[S,T](f : Callable[[S],T], tup : tuple[S,S]) -> tuple[T,T]:
  return (f(tup[0]), f(tup[1]))
```

New features

* type variables introduced in function signatures
* generic types
* which adaptations are needed in the type checker?

# What are the issues?

Given `map : All[[T], Callable[[Callable[[T],T], tuple[T,T] ], tuple[T,T]]` 
we wish to check if the function application `map(add1, (0, 41))` type
checks.

The new `All` type takes two "parameters":
1. a list of type variables
2. a type (the type variables scope over this type)

To this end, we need to find a _substitution_ that maps the type
variables to types, so that the application type checks.

In this example, the substitution `{ T: int }` (represented as a
dictionary) yields

`map_int : Callable[[Callable[[int],int], tuple[int,int] ], tuple[int,int]]`,

which is applicable to `add1 : Callable[[int],int]` and to `(0, 41) : tuple[int,int]`.

However, during type checking *we don't know the substitution initially*.

Let's have a look at the typing rules for expressions for guidance and
start *without generics*.


# Typing judgment

Judgment (in this case, a three-place relation)

      ctx |- e : t
	  
* `ctx` typing context
* `e` expression
* `t` type (of `e`)


# Typing rules for expressions (without generics)


              ctx (x) = t
        [VAR] ------------
              ctx |- x : t


        [CST] --------------
              ctx |- n : int


              ctx |- e : int
        [OP1] ----------------------------------------
              ctx |- - e : int


        	  ctx |- e1 : int
			  ctx |- e2 : int
        [OP2] ----------------------------------------
              ctx |- e1 + e2 : int


        	  ctx |- e0 : Bool
        	  ctx |- e1 : t
        	  ctx |- e2 : t
        [CND] ----------------------------------------
              ctx |- e1 if e0 else: e2 : t


        	  ctx |- e : Callable[ [t1, ..., tn] , t ]
        	  ctx |- ei : ti  (1 <= i <= n)
        [APP] ----------------------------------------
              ctx |- e (e1, ..., en) : t


        	  ctx, x1 : t1, ..., xn : tn |- e : t
        [LAM] -----------------------------------------------------------
              ctx |- lambda x1, ..., xn : e : Callable[ [t1, ..., tn], t]


        	  ctx |- ei : ti      (1 <= i <= n)
        [TUP] -------------------------------------------
              ctx |- (e1, ..., en) : tuple[ t1, ..., tn ]


        	  ctx |- e : tuple[ t1, ..., tn ]  (1 <= i <= n)
        [SEL] ----------------------------------------------
              ctx |- e[i] : ti
      

* these are *declarative* typing rules
* a type checker has to work backwards (from bottom to top)
* its input is `ctx` and `e` and it calculates `t`
* for most rules, this information is sufficient
* except for [LAM] where we have to *invent* the types of the
  variables `t1, ..., tn`


# Solution: Bidirectional type checking

*two* judgments

* synthesize type `t` from `ctx` and `e`

        ctx |- e => t

* check `e` against type `t` in context `ctx` (all three are inputs!)

        ctx |- e <= t

Let's modify the declarative rules to bidirectional rules (or:
algorithmic rules)


              ctx (x) = t
        [VAR] -------------
              ctx |- x => t


        [CST] ---------------
              ctx |- n => int


              ctx |- e => int
        [OP1] ----------------------------------------
              ctx |- - e => int


        	  ctx |- e1 => int
			  ctx |- e2 => int
        [OP2] ----------------------------------------
              ctx |- e1 + e2 => int


        	  ctx |- e0 <= Bool
        	  ctx |- e1 => t
        	  ctx |- e2 => t
        [CND] ----------------------------------------
              ctx |- e1 if e0 else: e2 => t


        	  ctx |- e => Callable[ [t1, ..., tn] , t ]
        	  ctx |- ei <= ti  (1 <= i <= n)
        [APP] ----------------------------------------
              ctx |- e (e1, ..., en) => t


        	  ctx, x1 : t1, ..., xn : tn |- e <= t
        [LAM] -----------------------------------------------------------
              ctx |- lambda x1, ..., xn : e <= Callable[ [t1, ..., tn], t]


        	  ctx |- ei => ti      (1 <= i <= n)
        [TP>] -------------------------------------------
              ctx |- (e1, ..., en) => tuple[ t1, ..., tn ]

        	  ctx |- ei <= ti      (1 <= i <= n)
        [TP<] -------------------------------------------
              ctx |- (e1, ..., en) <= tuple[ t1, ..., tn ]


        	  ctx |- e => tuple[ t1, ..., tn ]  (1 <= i <= n)
        [SEL] ----------------------------------------------
              ctx |- e[i] => ti
			  
What's missing?

Consider a function call `f(x)`
Typechecking this results in

Context:

      f : Callable[ [int] , int ]
	  x : int
      
Typechecking

      ctx |- f (x) => ?
        ctx |- f => Callable[ [int] , int ]  (by [VAR]
    	ctx |- x <= int
		
Need to add a rule to switch from checking to synthesis:


      ctx |- e => t1
      t1 == t2
	  -------------------
      ctx |- e <= t2
		
		
# Type checking generic functions

Declarative rules for applying generic functions

        	  ctx |- e : All[ [A1, ..., Ak], Callable[ [t1, ..., tn] , t ]]
			  let s = { A1 : s1, ..., Ak : sk } a substitution where s1 ... sk are types
        	  ctx |- ei : ti { A1 : s1, ..., Ak : sk }  (1 <= i <= n)
        [APP] -------------------------------------------------------------
              ctx |- e (e1, ..., en) : t { A1 : s1, ..., Ak : sk }

how do we obtain the substitution?

We can't invent the whole substitution at the point of the [APP] rule.
We have to do it incrementally.
We substitute new type variables for the Ai, if the type checker
reaches a place where it wants to check against a type variable, it
creates a substitution for the variable.

Now type checking of expression `e` against type `t` has to return a
substitution `s`.

     ctx |- e <= t | u
	 

      ctx |- e => All[ [A1, ..., Ak], Callable[ [t1, ..., tn] , t ]]
	  obtain fresh type variables F1, ..., Fk
	  let si = ti { A1 : F1, ..., Ak : Fk }
	  let s  = t  { A1 : F1, ..., Ak : Fk }
	  ctx |- ei <= si | ui
	  let u = unify (u1, ..., un)
    ----------------------------------
      ctx |- e (e1, ..., en) => s @ u

* `u` is a substitution `{ F1 : r1, ..., Fk : rk }` for types `r1, ..., rk`

To get our substitution, we have to augment our switch judgment


      ctx |- e => t1
      t1 == t2 | u
	  -------------------
      ctx |- e <= t2 | u

The equality judgment `t1 == t2 | u` has to perform unification (i.e.,
matching). For example:

      t == Fi | { Fi : t }
	  
	  
	  
      t1 == s1 | u1
	  t2 == s2 | u2
	  ...
	  let u = unify (u1, ..., un)
	  ------------------------------------------------
	  tuple[ t1, ..., tn ] == tuple[ s1, ..., sn ] | u


## First-class generics

```python
def apply_twice(f : All[[U], Callable[[U],U]]) -> int:
  if f(True):
    return f(42)
  else:
    return f(777)

def id[T](x: T) -> T:
  return x

print(apply_twice(id))
```

The function call `apply_twice(id)`
checks its argument type against `All[[U], Callable[[U],U]]`
but the type of `id`  is `All[[T], Callable[[T],T]`.
These types are considered equal, because the names of the bound type
variables do not matter - they can be renamed.

The equality check has to keep in mind that `U` in one type is equal
to `T` in the other.
For example, maintain a mapping/relation between type variables in the
two types.
Or by normalizing the type variables to some standard names.


# Implementation options for generics

## monomorphization aka heterogeneous translation

C++ templates, Go, Rust

Very efficient, but results in code duplication (increase the size of
the program, in theory exponentially - but not observed in practice)

Problems: depending on the language features, monomorphization may not terminate

## mixed representation aka homogenenous translation

Java casts generic arguments to `Object` before the call and back from
`Object` afterwards. Introduces some overhead:

1. casting to `Object` has no run-time cost
2. casting from `Object` requires a type check at run time
3. in Java there are primitive types (int, bool, double, float) and
   there are reference types (aka objects). In particular, a primitive
   type is *not* an object, so it cannot be cast to `Object`.
   Java's solution: introduce a wrapper type (Int, Bool, Double, Float) for each primitive type,
   then Java wraps each primitive type in its wrapper that can be cast
   to `Object` (and unwrap on return). Wrapping is also known as
   boxing/unboxing.
   This combination can be very inefficient. 
