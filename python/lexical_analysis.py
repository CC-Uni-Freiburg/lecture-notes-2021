from dataclasses import dataclass
from functools import reduce
from typing import Callable, Iterable, Iterator

'''
The first phase of a compiler is called `lexical analysis` implemented by a `scanner` or `lexer`.
It breaks a program into a sequence `lexemes`: 
    meaningful substrings of the input.
It also transforms lexemes into `tokens`: 
    symbolic representations of lexemes with some internalized information.

The classic, state-of-the-art method to specify lexemes is by regular expressions.
'''

'''
1. Representation of regular expressions.
'''

@dataclass
class Regexp:
    'abstract class for AST of regular expressions'
    def is_null(self):
        return False

@dataclass
class Null (Regexp):
    'empty set: {}'
    def is_null(self):
        return True
@dataclass
class Epsilon (Regexp):
    'empty word: { "" }'
@dataclass
class Symbol (Regexp):
    'single symbol: { "a" }'
    sym: str
@dataclass
class Concat(Regexp):
    'concatenation: r1.r2'
    left: Regexp
    right: Regexp
@dataclass
class Alternative(Regexp):
    'alternative: r1|r2'
    left: Regexp
    right: Regexp
@dataclass
class Repeat(Regexp):
    'Kleene star: r*'
    body: Regexp

## smart constructors for regular expressions
## goal: construct regexps in "normal form"
## * avoid Null() subexpressions
## * Epsilon() subexpressions as much as possible
## * nest concatenation and alternative to the right
null = Null()
epsilon = Epsilon()
symbol  = Symbol
def concat(r1, r2):
    match (r1, r2):
        case (Null(), _) | (_, Null()):
            return null
        case (Epsilon(), _):
            return r2
        case (_, Epsilon()):
            return r1
        case (Concat(r11, r12), _):
            return Concat(r11, concat(r12, r2))
        case _:
            return Concat(r1, r2)
def alternative(r1, r2):
    match (r1, r2):
        case (Null(), _):
            return r2
        case (_, Null()):
            return r1
        case (Alternative(r11, r12), _):
            return Alternative(r11, alternative(r12, r2))
        case _:
            return Alternative(r1, r2)
def repeat(r: Regexp) -> Regexp:
    match r:
        case Null() | Epsilon():
            return epsilon
        case Repeat(r1):        # r** == r*
            return r
        case _:
            return Repeat(r)

## utilities to construct regular expressions
def optional(r : Regexp) -> Regexp:
    'construct r?'
    return alternative(r, epsilon)

def repeat_one(r : Regexp) -> Regexp:
    'construct r+'
    return concat(r, repeat(r))

def concat_list(rs : Iterable[Regexp]) -> Regexp:
    return reduce(lambda out, r: concat(out, r), rs, epsilon)

def alternative_list(rs : Iterable[Regexp]) -> Regexp:
    return reduce(lambda out, r: alternative(out, r), rs, null)

## a few examples for regular expressions (taken from JavaScript definition)
'''
⟨digit⟩ ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
⟨hexdigit⟩ ::= ⟨digit⟩ | A | B | C | D | E | F | a | b | c | d | e | f 
⟨hexprefix⟩ ::= 0x | 0X
⟨sign⟩ ::= ⟨empty⟩ | -
⟨empty⟩ ::=
⟨integer-literal⟩ ::= ⟨sign⟩ ⟨digit⟩+ | ⟨sign⟩ ⟨hexprefix⟩ ⟨hexdigit⟩+
⟨letter⟩ ::= A | B | C | ...| Z | a | b | c | ...| z 
⟨identifier-start⟩ ::= ⟨letter⟩ | $ | _
⟨identifier-part⟩ ::= ⟨identifier-start⟩ | ⟨digit⟩ 
⟨identifier⟩ ::= ⟨identifier-start⟩ ⟨identifier-part⟩*
'''
def class_regexp(s: str) -> Regexp:
    'returns a regexp for the alternative of all characters in s'
    return alternative_list(map(symbol, s))

def string_regexp(s: str) -> Regexp:
    'returns a regexp for the concatenation of all characters in s'
    return concat_list(map(symbol, s))

def char_range_regexp(c1: str, c2: str) -> Regexp:
    return alternative_list(map(symbol, map(chr, range(ord(c1), ord(c2)+1))))

digit = class_regexp("0123456789")
hexdigit = alternative(digit, class_regexp("ABCDEFabcdef"))
hexprefix = alternative(string_regexp("0x"), string_regexp("0X"))
sign = optional(symbol('-'))
integer_literal = concat(sign, repeat_one(digit))
integer_literal_js = alternative( concat(sign, repeat_one(digit)),
                            concat_list([sign, hexprefix, repeat_one(hexdigit)]))

lc_letter = alternative_list(map(symbol, map(chr, range(ord('a'), ord('z')+1))))
uc_letter = alternative_list(map(symbol, map(chr, range(ord('A'), ord('Z')+1))))
letter = alternative(lc_letter, uc_letter)
identifier_start = alternative_list([letter, symbol('$'), symbol('_')])
identifier_part = alternative(identifier_start, digit)
identifier = concat(identifier_start, repeat(identifier_part))

blank_characters = "\t "
line_end_characters = "\n\r"
white_space = repeat_one(class_regexp(blank_characters + line_end_characters))

'''
2. Executing regular expressions

The standard method to 'execute' regular expressions is to transform them into finite automata.
Here we use a different method to execute them directly using `derivatives`.
This method uses regular expressions themselves as states of an automaton without constructing it.

We consider a regexp a final state if it accepts the empty word "".
This condition can be checked by a simple function on the regexp.
'''
def accepts_empty(r : Regexp) -> bool:
    'check if r accepts the empty word'
    match r:
        case Null() | Symbol(_):
            return False
        case Epsilon() | Repeat(_):
            return True
        case Concat(r1, r2):
            return accepts_empty(r1) and accepts_empty(r2)
        case Alternative(r1, r2):
            return accepts_empty(r1) or accepts_empty(r2)

'''
The transition function of a (deterministic) finite automaton maps 
state `r0` and symbol `s` to the next state, say, `r1`.
If the state `r0` recognizes any words `w` that start with `s` (w[0] == s),
then state `r1` recognizes all those words `w` with the first letter removed (w[1:]).
This construction is called the `derivative` of a language by symbol `s`:

derivative(L, s) = { w[1:] | w in L and w[0] == s }

If L is the language recognized by regular expression `r0`, 
then we can effectively compute a regular expression for derivative(L, s)!
As follows:
'''
def after_symbol(s : str, r : Regexp) -> Regexp:
    'produces regexp after r consumes symbol s'
    match r:
        case Null() | Epsilon():
            return null
        case Symbol(s_expected):    
            return epsilon if s == s_expected else null
        case Alternative(r1, r2):
            return alternative(after_symbol(s, r1), after_symbol(s, r2))
        case Concat(r1, r2):
            return alternative(concat(after_symbol(s, r1), r2), 
                            after_symbol(s, r2) if accepts_empty(r1) else null)
        case Repeat(r1):
            return concat(after_symbol(s, r1), Repeat(r1))

## matching against a regular expression
def matches(r : Regexp, ss: str) -> bool:
    i = 0
    while i < len(ss):
        r = after_symbol(ss[i], r)
        if r.is_null():
            return False
        i += 1
    # reached end of string
    return accepts_empty(r)

########################################################################
'''
3. Lexer descriptions

A lexer (scanner) is different from a finite automaton in several aspects.

1. The lexer must classify the next lexeme from a choice of several regular expressions.
   It cannot match a single regexp, but it has to keep track and manage matching for
   several regexps at the same time.
2. The lexer follows the `maximum munch` rule, which says that the next lexeme is
   the longest prefix that matches one of the regular expressions.
3. Once a lexeme is identified, the lexer must turn it into a token and attribute.

Re maximum munch consider this input:

ifoundsalvationinapubliclavatory

Suppose that `if` is a keyword, why should the lexer return <identifier> for this input?

Similarly:

returnSegment

would count as an identifier even though starting with the keyword `return`.

These requirements motivate the following definitions.

A lex_action 
* takes some (s : str, i : int position in s, j : int pos in s)
* consumes the lexeme sitting at s[i:j]
* returns (token for s[i:j], some k >= j)
'''

class Token: pass # abstract class of tokens

Position = int      # input position
lex_result = tuple[Token, Position]
lex_action = Callable[[str, Position, Position], lex_result]

# a lexer rule attaches a lex_action to a regular expression
@dataclass
class Lex_rule:
    re : Regexp
    action: lex_action

# a lexer tries to match its input to a list of lex rules
Lex_state = list[Lex_rule]

# reading a symbol advances the regular expression of each lex rule
def next_state(state: Lex_state, ss: str, i: int):
    return list(filter(lambda rule: not (rule.re.is_null()),
                 [Lex_rule(after_symbol(ss[i], rule.re), rule.action) 
                  for rule in state]))

def initial_state(rules: list[Lex_rule]) -> Lex_state:
    return rules

def matched_rules(state: Lex_state) -> Lex_state:
    return [rule for rule in state if accepts_empty(rule.re)]

def is_stuck(state: Lex_state) -> bool:
    return not state

#####################################################################
class ScanError (Exception): pass

@dataclass
class Match:
    action: lex_action
    final : Position

@dataclass
class Scan:
    spec: Lex_state

    def scan_one(self) -> Callable[[str, Position], lex_result]:
        return lambda ss, i: self.scan_one_token(ss, i)

    def scan_one_token(self, ss: str, i: Position) -> lex_result:
        state = self.spec
        j = i
        last_match = None
        while j < len(ss) and not is_stuck(state):
            state = next_state(state, ss, j); j += 1
            all_matches = matched_rules(state)
            if all_matches:
                this_match = all_matches[0]
                last_match = Match(this_match.action, j)

        match last_match:
            case None:
                raise ScanError("no lexeme found:", ss[i:])
            case Match(action, final):
                return action(ss, i, final)
        raise ScanError("internal error: last_match=", last_match)

def make_scanner(scan_one: Callable[[str, Position], lex_result], ss: str) -> Iterator[Token]:
    i = 0
    while i < len(ss):
        (token, i) = scan_one(ss, i)
        yield (token)

## example: excerpt from JavaScript scanner

escaped_char = concat(symbol('\\'), alternative(symbol('\\'), symbol('"')))
content_char = alternative_list([symbol(chr(a)) 
                                for a in range(ord(' '), 128)
                                if a not in [ord('\\'), ord('"')]])
string_literal = concat_list([symbol('"'), repeat(alternative(escaped_char, content_char)), symbol('"')])

@dataclass 
class Return(Token): pass
@dataclass
class Intlit(Token): value: int
@dataclass
class Ident(Token):  name: str
@dataclass
class Lparen(Token): pass
@dataclass
class Rparen(Token): pass
@dataclass
class Slash(Token): pass
@dataclass
class Strlit(Token): value: str

string_spec: Lex_state = [
    Lex_rule(escaped_char,  lambda ss, i, j: (ss[i+1], j)),
    Lex_rule(content_char, lambda ss, i, j: (ss[i], j))
]
string_token = Scan(string_spec).scan_one()

def strlit(ss: str) -> Strlit:
    "use subsidiary scanner to transform string content"
    return Strlit("".join(make_scanner(string_token, ss)))
        

js_spec: Lex_state = [
    Lex_rule(string_regexp("return"), lambda ss, i, j: (Return(), j)),
    Lex_rule(integer_literal, lambda ss, i, j: (Intlit(int(ss[i:j])), j)),
    Lex_rule(identifier,      lambda ss, i, j: (Ident(ss[i:j]), j)),
    Lex_rule(white_space,     lambda ss, i, j: js_token(ss, j)),
    Lex_rule(symbol("("),     lambda ss, i, j: (Lparen(), j)),
    Lex_rule(symbol(")"),     lambda ss, i, j: (Rparen(), j)),
    Lex_rule(symbol("/"),     lambda ss, i, j: (Slash(), j)),
    Lex_rule(string_literal,  lambda ss, i, j: (strlit(ss[i+1:j-1]), j))
]
js_token = Scan(js_spec).scan_one()

def example1():
    return js_token("   42...", 0)

def example2():
    sc = make_scanner(js_token, "return Segment (pi / 2)")
    for ta in sc:
        print(ta)

def example3():
    sc = make_scanner(js_token, 'return "foobar\\"..."')
    for ta in sc:
        print(ta)