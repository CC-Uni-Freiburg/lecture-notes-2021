## Strength reduction in loops

```
s = 0
for i = 1 ... n:
    j = 4*i
	s = s + memory[j]
return s
```

```
int memory[];
int s = 0;
for (int i = 0; i < n; i++) {
   s += memory[ i ];
   // internally we access (*((char *) m + 4*i)
}
```

Transform the multiplication in each iteration to an addition.
In the example:

```
s = 0
j = 0
for i = 1 ... n:
    j = j + 4
	s = s + memory[j]
return s
```

Second step: removing `i`

```
s = 0
j = 0

while j < 4*n:
	j = j + 4
	s = s + memory[j]
return s
```




## Constant Propagation

Suppose we reach l from two places:
1. x = 1
2. x = 2

Reaching l we only see the lub( 1, 2) : rho(x) = T

l : if x = 2 then l1 else l2

eval( rho, 2 ) = 2

rho1( x ) = glb (2, T) = 2

ˆe ˆ= ρ(x)  ::  2 ^= T = T which is >= false, so the false branch l2
is also feasible.

For Bool: {true, false} ^T _\bot ~= P Bool
with \bot = {}
        T      = {true, false}
		false = {false}
		true  = {true}


















## Example for constant propagation

```
 1 z = 3              | z=3           |
 2 x = 1              | z=3, x=1      |
 3 while (x > 0) {    |               | z=3, x=T, y=7
 4   if (x = 1) then  | z=3, x=1      | z=3, x=1, y=7
 5     y = 7          | z=3, x=1, y=7 | z=3, x=1, y=7
 6   else             |
 7     y = z + 4      |               | z=3, x=T, y=7
                      | z=3, x=1, y=7 | z=3, x=T, y=7
 8   x = 3            | z=3, x=3, y=7 | z=3, x=3, y=7
 9   print y          |
10 }   
```

## expectations

* z=3 is a constant throughout
* x is not a constant at the beginning of the while loop (line 4)
* x=1 at line 5
* y=7 in the while loop





















## Example for CSE


```
L1:                        | {}
  x ← a ⊕ b                | { (x, a ⊕ b) }
  if a < b then L2 else L3
L2:
  y ← a ⊕ b   **CSE**      | { (x, a ⊕ b), (y, a ⊕ b) }
  goto L4(y)
L3:
  z ← x ⊕ b                | { (x, a ⊕ b), (z, x ⊕ b) }
  goto L4(z)
L4(w):                     |   { (x, a ⊕ b), (w, a ⊕ b) } /\ { (x, a ⊕ b), (w, x ⊕ b) }
                           | = { (x, a ⊕ b) }
  u ← a ⊕ b    **CSE**
```
