from ast import BinOp
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Iterator, Optional, TypeVar


### context free grammars

TS     = TypeVar("TS")
NTS    = TypeVar("NTS", str, int)

@dataclass(frozen=True)
class NT:
    nt: NTS

Symbol = NT | TS

@dataclass(frozen=True)
class Production:
    lhs: NTS
    rhs: list[Symbol]
    ext: Any = None

@dataclass(frozen=True)
class Grammar:
    nonterminals: list[NTS]
    terminals: list[TS]
    rules: list[Production]
    start: NTS

    def productions_with_lhs(self, nts: NTS) -> list[Production]:
        return [ rule for rule in self.rules if rule.lhs == nts ]

### abstract syntax for arithmetic expressions

class AST: pass
@dataclass
class Binop(AST):
    left: AST
    binop: str
    right: AST
@dataclass
class Var(AST):
    name: str
@dataclass
class Constant(AST):
    val: int

### an example grammar

expr_grammar = Grammar(
    ['T', 'E', 'F'],
    ['x', '2', '(', ')', '+', '*'],
    [Production('T', [NT('E')],               lambda e: e)
    ,Production('T', [NT('T'), '+', NT('E')], lambda t, e: BinOp(t, '+', e))
    ,Production('E', [NT('F')],               lambda f: f)
    ,Production('E', [NT('E'), '*', NT('F')], lambda e, f: BinOp(e, '*', f))
    ,Production('F', ['x'],                   lambda : Var('x'))
    ,Production('F', ['2'],                   lambda : Constant(2))
    ,Production('F', ['(', NT('T'), ')'],     lambda t: t)],
    'T'
)
expr_grammar_ = Grammar(
    ['T', "T'", 'E', "E'", 'F'],
    ['x', '2', '(', ')', '+', '*'],
    [Production('T', [NT('E'), NT("T'")])
    ,Production("T'", ['+', NT('E'), NT("T'")])
    ,Production("T'", [])
    ,Production('E', [NT('F'), NT("E'")])
    ,Production("E'", ['*', NT('F'), NT("E'")])
    ,Production("E'", [])
    ,Production('F', ['x'])
    ,Production('F', ['2'])
    ,Production('F', ['(', NT('T'), ')'])],
    'T'
)

### ineffective, nondeterministic parser

def td_parse(g: Grammar, alpha: list[Symbol], inp: list[TS]
            ) -> Iterator[list[TS]]:
    match alpha:
        case []:
            yield inp
        case [NT(nt), *rest_alpha]:
            for rule in g.productions_with_lhs(nt):
                for rest_inp in td_parse(g, rule.rhs, inp):
                    yield from td_parse(g, rest_alpha, rest_inp)
        case [ts, *rest_alpha]:
            if inp and ts == inp[0]:
                yield from td_parse(g, rest_alpha, inp[1:])

# convenience

def parse_from_string(g: Grammar, s: str) -> Iterator[list[str]]:
    return td_parse(g, [NT(g.start)], list(s))

### example parser for expr_grammar

def td_parse_T(inp: str) -> Iterator[list[str]]:
    # 1st production
    yield from td_parse_E(inp)
    # 2nd production
    for inp1 in td_parse_T(inp):
        if inp1[:1] == '+':
            yield from td_parse_E(inp1[1:])

def td_parse_E(inp: str) -> Iterator[list[str]]:
    # 1st production
    yield from td_parse_F(inp)
    # 2nd production
    for inp1 in td_parse_E(inp):
        if inp1[:1] == '*':
            yield from td_parse_F(inp1[1:])

def td_parse_F(inp: str) -> Iterator[list[str]]:
    match inp[:1]:
        case 'x':
            yield inp[1:]
        case '2':
            yield inp[1:]
        case '(':
            for rest_inp in td_parse_E(inp[1:]):
                match rest_inp[:1]:
                    case ')':
                        yield rest_inp[1:]

### first sets for k=1
# we represent first sets as a mapping
EmptySet = dict[NTS,bool]

def initial_empty(g: Grammar) -> EmptySet:
    return { n : False for n in g.nonterminals }

def derives_empty(fs: EmptySet, alpha: list[Symbol]) -> bool:
    match alpha:
        case []:
            return True
        case [NT(nt), *rest]:
            return fs[nt] and derives_empty(fs, rest)
        case [ts, *rest]:
            return False

def update_empty(g: Grammar, fs: EmptySet):
    for n in g.nonterminals:
        fn = fs[n]
        for rule in g.productions_with_lhs(n):
            fn = fn or derives_empty(fs, rule.rhs)
        fs[n] = fn

FirstSet = dict[NTS,frozenset[TS]]

def initial_first(g: Grammar) -> FirstSet:
    return { n : frozenset() for n in g.nonterminals }

def first(es: EmptySet, fs: FirstSet, alpha: list[Symbol]) -> frozenset[TS]:
    match alpha:
        case [NT(nt), *rest] if es[nt]:
            return fs[nt] | first(es, fs, rest)
        case [NT(nt), *rest]:
            return fs[nt]
        case [t, *rest]:
            return frozenset([t])
        case []:
            return frozenset()

def update_first(g: Grammar, es: EmptySet, fs: FirstSet):
    for n in g.nonterminals:
        fn = fs[n]
        for rule in g.productions_with_lhs(n):
            fn = fn | first(es, fs, rule.rhs)
        fs[n] = fn

def fixed_point(current_map: dict, update: Callable[[dict], None]) -> dict:
    next_map = None
    while next_map is None or any(current_map[k] != next_map[k] for k in current_map):
        next_map = current_map
        current_map = current_map.copy()
        update(current_map)
    return current_map

def calculate_empty(g: Grammar) -> EmptySet:
    es = initial_empty(g)
    return fixed_point(es, partial(update_empty, g))

def calculate_first(g: Grammar, es: EmptySet) -> FirstSet:
    fs = initial_first(g)
    return fixed_point(fs, partial(update_first, g, es))

es = calculate_empty(expr_grammar_)
fs = calculate_first(expr_grammar_, es)

###

class GrammarAnalysis:
    ## abstract methods
    def bottom(self) -> Any:
        pass
    def empty(self) -> Any:
        pass
    def singleton(self, term) -> Any:
        pass
    def join(self, x, y) -> Any:
        pass
    def concat(self, x, y) -> Any:
        pass
    def equal(self, x, y) -> bool:
        pass

    def initial_analysis(self, g: Grammar) -> dict[NTS]:
        return { n : self.bottom() for n in g.nonterminals }
    def rhs_analysis(self, fs: dict[NTS], alpha: list[Symbol]):
        r = self.empty()
        for sym in alpha:
            match sym:
                case NT(nt):
                    r = self.concat(r, fs[nt])
                case term:
                    r = self.concat(r, self.singleton(term))
        return r
    def update_analysis(self, g: Grammar, fs: dict):
        for rule in g.rules:
            match rule:
                case Production(nt, alpha):
                    fs[nt] = self.join(self.rhs_analysis(fs, alpha), fs[nt])
    def run(self, g: Grammar):
        initial_map = self.initial_analysis(g)
        update_map = partial(self.update_analysis, g)
        return fixed_point(initial_map, update_map)


@dataclass
class First_K_Analysis (GrammarAnalysis):
    k: int
    def bottom(self):
        return frozenset([])
    def empty(self):
        return frozenset({ "" })
    def singleton(self, term):
        return frozenset({ term })
    def join(self, sl1, sl2):
        return sl1 | sl2
    def concat(self, x, y) -> Any:
        return frozenset({ (sx+sy)[:self.k] for sx in x for sy in y })
    def equal(self, x, y) -> bool:
        return  x == y

@dataclass
class Follow_K_Analysis(First_K_Analysis):
    first_k: dict

    def initial_analysis(self, g: Grammar):
        r = super().initial_analysis(g)
        r[g.start] = self.empty()
        return r

    def update_analysis(self, g: Grammar, fs: dict):
        for rule in g.rules:
            match rule:
                case Production(nt, alpha):
                    for i in range(len(alpha)):
                        match alpha[i]:
                            case NT(n):
                                rst = self.rhs_analysis(self.first_k, alpha[i+1:])
                                fs[n] = self.join(fs[n], self.concat(rst, fs[nt]))

### general first_1 analysis

first1analysis = First_K_Analysis(1)
first1 = first1analysis.run(expr_grammar_)

### deterministic parser

def accept(g: Grammar, k: int, inp: list[TS]) -> Optional[list[TS]]:
    fika = First_K_Analysis(k)
    first_k = fika.run(g)
    foka = Follow_K_Analysis(k, first_k)
    follow_k = foka.run(g)
    def lookahead(rule: Production) -> frozenset[str]:
        return fika.concat(fika.rhs_analysis(first_k,rule.rhs), follow_k[rule.lhs])
    def accept_symbol(sym: Symbol, inp: list[TS]) -> Optional[list[TS]]:
        match sym:
            case NT(nt):
                prefix = "".join(inp[:k])
                candidates = [rule for rule in g.productions_with_lhs(nt) 
                                   if prefix in lookahead(rule)]
                if len(candidates) > 1:
                    print("Grammar is not LL("+str(k)+")")
                if len(candidates) > 0:
                    return accept_list(candidates[0].rhs, inp)
            case t:
                if inp[:1] == [t]:
                    return inp[1:]
    def accept_list(alpha: list[Symbol], inp: list[TS]) -> Optional[list[TS]]:
        for sym in alpha:
            inp = accept_symbol(sym, inp)
            if inp is None:
                break
        return inp

    return accept_symbol(NT(g.start), inp)

### convenience

def accept_expr(inp: str) -> Optional[list[TS]]:
    return accept(expr_grammar_, 1, list(inp))
