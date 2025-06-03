## 2025-06-03 Functions

### comparing implementations of apply_fun

1. environment structure in the function body

RTEnv( local function env, global env )

2. in the book:

env.copy().update( local function env )

Results in problems if the callee assigns to a global variable.
1. assignments are preserved across function calls
2. assignments are lost when the function returns, because we *copied*
   the global part of the environment

###

we can also write

x = map
print(x(inc, (0, 41))[1])

flag = true
(inc if flag else dec) (41)
