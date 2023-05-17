from ast import *

def interp_exp(e): 
    match e:
        case BinOp(left, Add(), right):
            l = interp_exp(left)
            r = interp_exp(right) 
            return l + r
        case UnaryOp(USub(), v):
            return - interp_exp(v)
        case Constant(value): 
            return value
        case Call(Name('input_int'), []): 
            return int(input())

def interp_stmt(s): 
    match s:
        case Expr(Call(Name('print'), [arg])): 
            print(interp_exp(arg))
        case Expr(value): 
            interp_exp(value)

def interp_Lint(p): 
    match p:
        case Module(body): 
            for s in body:
                interp_stmt(s)

ex1 = "print(1 + (2 + 3))"
ast1 = parse(ex1)
print(dump(ast1))

interp_Lint(ast1)

ex2 = "print(6)"
ast2 = parse(ex2)

# output of interp_Lint(ast1) == output of interp_Lint(ast2)

# more interesting example for partial evaluation
ex3 = "print(input_int() + (2 + 3))"
ex3_opt = "print(input_int() + 5)"

ex4 = "print((input_int() + 2) + 3)"
ex4_from_book = "print((input_int() + 2) + 3)"
ex4_your_pe   = "print(input_int() + 5)"



