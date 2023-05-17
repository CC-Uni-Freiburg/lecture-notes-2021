from dataclasses import dataclass

@dataclass
class Constant:
    value : int

ex_num = Constant(42)


@dataclass
class Add:
    pass

@dataclass
class BinOp:
    left : any
    op : Add
    right : any

# ast for "17 + 4"
ex_add = BinOp(Constant(17), Add(), Constant(4))

print(ex_num)
print(ex_add)

