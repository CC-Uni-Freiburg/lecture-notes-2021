import ast

#print(ast.dump(ast.parse("42", mode='eval')))

#print(ast.dump(ast.parse("input_int()", mode='eval')))
# print(ast.dump(ast.parse("-10")))
# print(ast.dump(ast.parse("-10 + 5")))
#print(ast.dump(ast.parse("input_int() + -input_int()", mode='eval')))



"10+32"
ast.BinOp(ast.Constant(10), ast.Add(), ast.Constant(32))


























r = ast.parse("input_int()")
match r:
    case ast.Module([stmt]):
        print(ast.dump(stmt))
        match stmt:
            case ast.Expr(e):
                print(ast.dump(e))
                match e:
                    case ast.Call(id, args):
                        print(ast.dump( id))
                        print(args)

