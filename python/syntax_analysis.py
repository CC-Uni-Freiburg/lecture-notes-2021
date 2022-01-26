from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Iterator, TypeVar

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

### an example grammar

expr_grammar = Grammar(
    ['T', 'E', 'F'],
    ['x', '2', '(', ')', '+', '*'],
    [Production('T', [NT('E')])
    ,Production('T', [NT('T'), '+', NT('E')])
    ,Production('E', [NT('F')])
    ,Production('E', [NT('E'), '*', NT('F')])
    ,Production('F', ['x'])
    ,Production('F', ['2'])
    ,Production('F', ['(', NT('T'), ')'])],
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

def fixed_point(current_map: dict, update: Callable[[FirstSet], None]) -> dict:
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