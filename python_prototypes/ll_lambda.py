#TODO include # end marker? for follow set at leasT?
#TODO these nontabular approaches are probably quite inefficient? memoization?

#TODO understand this section from c&J:
# A shorter way of
# saying this is that we add α to the [A,a] entry of the parse table for all terminal sym-
# bols a in FIRST(α FOLLOW(A)). This last set consists of the union of the FIRST
# sets of the sentential forms αb for all symbols b in FOLLOW(A).
# If a token in a FOLLOW set causes the addition of a right-hand side to an entry
# that already contains a right-hand side due to a token in a FIRST set, we have a
# FIRST/FOLLOW conflict, and the grammar is not LL(1). It is even possible to have
# a FOLLOW/FOLLOW conflict: an entry receives two right-hand sides, both brought
# in by tokens from FOLLOW sets. This happens if more than one alternative of a
# non-terminal can produce ε.

import string
from textwrap import dedent
from collections import defaultdict
from itertools import chain


def is_t(sym):
    return sym in string.punctuation or sym.islower()


def read_grammar(s):
    acc = 0
    return {e[0]: [(v, acc := acc + 1) for v in e[1:]] for line in s.splitlines() for e in [line.split()]}


#TODO this doesnt exactly follow C&H algorithm
# homogeneous treatment of nt and t
#TODO check parentsets are right
#TODO test
def FIRST(grammar, _str, parentset=None):  # TODO may need modifications on the recursion checking if
    if _str == "":
        return {"ε"}

    head, tail = _str[0], _str[1:]
    parentset = set() if parentset is None else (parentset | {head})

    if not tail and (is_t(head) or head == "ε"):  # terminal
        return {head}
    elif not tail:  # nonterminal: union of FIRSTs of alternatives
        return set.union(*[FIRST(grammar, alt, parentset) for alt, _ in grammar[head]])

    if "ε" in (r := FIRST(grammar, head, parentset)):
        r = (r - {"ε"}) | FIRST(grammar, _str[1:], parentset)
    return r if r else {"ε"}  # TODO how do I make sure if the whole string is nulled I return epsilon? there is no other way to get the empty set right?


class Fix:
    # maxiter is to help with infrec
    @staticmethod
    def fix(f, y, maxiter=10000): # TODO is this correct
        x = None
        i = 0
        while x != y and i < maxiter:
            x, y = y, f(y)
            i += 1
        if i == maxiter:
            raise RecursionError("Iteration limit exceeded, last values: (%s, %s)" % (x, y))
        return y

    @classmethod
    def check(cls):
        import math
        assert(cls.fix(lambda x: math.sqrt(x), 2) == 1.0)

        def assertException(f, e):
            try:
                f()
            except e:
                return
            else:
                raise AssertionError("%s not raised" % e.__name__)

        assertException(lambda: cls.fix(lambda x: math.sqrt(x), 2, 10), RecursionError)


Fix.check()
fix = Fix.fix

def _FOLLOW(grammar, nt, parentset=None):  # TODO check if this handles recursive rules ok
    if parentset == None:
        parentset = set()

    fset = set()
    if nt == "S":
        fset |=  {"#"}  # TODO is this correct?
    for lhs, rhs in grammar.items():
        for alt, _ in rhs:
            i = 0
            while (idx := alt.find(nt, i)) != -1:
                if "ε" in (r := FIRST(grammar, alt[idx+1:])):
                    r = (r - {"ε"}) | (set() if lhs in parentset else _FOLLOW(grammar, lhs, parentset | {lhs}))  # TODO is this correct
                fset |= r
                i = idx+1
    return fset

# TODO should be memoized at least or something
def FOLLOW(grammar, nt):
    def state(f, grammar):
        def wrapped(state):
            for nt in grammar:
                state[nt] |= f(grammar, nt)
            # print(state) #TODO seems like I dont need to fixpoint this?
            return state
        return wrapped

    return fix(state(_FOLLOW, grammar), defaultdict(set))[nt]


# as an implementation detail we assume here that there are no first/first conflicts and the language is ll;
# the dictionary maps >rules of a nt< to each of their respective first terminals,
# so if multiple alternatives in a rule have a same first terminal the behaviour is undefined
def gen_table(grammar, terminalish="#"):

    err = lambda: "error"
    table = defaultdict(lambda: defaultdict(lambda: "error"))
    #table.update({lhs: {rule[1][0]: rule for rule in rhs} for lhs, rhs in grammar.items()})
    #table.update({lhs: defaultdict(err, {list(FIRST(grammar, rule))[0]: _rule for _rule in rhs for rule, i in [_rule]}) for lhs, rhs in grammar.items()})
    for lhs, rhs in grammar.items():
        for alt, i in rhs:
            for t in set.union(*[FIRST(grammar, alt + e) for e in FOLLOW(grammar, lhs)]):
                table[lhs][t] = alt, i
    table.update({c: defaultdict(err, {c: "pop" if c != "#" else "accept"}) for c in terminalish + "#"})

    return table


def parse(inp, table):
    anal, pred = list(), ["#", "S"]
    for c in chain(inp, "#"): #TODO need to add hash handling to handle e.g. emptying the stack at the end
        while True:
            print(anal, pred)
            if pred:  # TODO is this correct? # wrong, needs to empty simultaneously with hash and inp
                action = table[(v := pred.pop())][c]
                if v == "ε":
                    continue  # TODO is this the correct behaviour?
            else:
                action = "error"

            if action == "pop":
                print(c)
                break
            elif action == "error":
                raise ValueError
            elif action == "accept":
                print("accepted")
                return True
            else:
                pred.extend(reversed(action[0]))
                anal.append(action[1])


    print(anal, pred)
    return anal, pred


def test1():
    grammar = dedent("""
        S ab
        B b aBb
        """).strip()

    grammar = read_grammar(grammar)
    assert FIRST(grammar, "S") == {'a'}
    assert FIRST(grammar, "B") == {'a', 'b'}


def test2():
    grammar = dedent("""
        S FS Q (S)S
        F !s
        Q ?s
        """).strip()

    grammar = read_grammar(grammar)
    assert FIRST(grammar, "S") == {'?', '!', '('}
    assert FIRST(grammar, "F") == {'!'}
    assert FIRST(grammar, "Q") == {'?'}

    table = gen_table(grammar, "!?()s")
    inp = "!s(!s?s)?s"
    print(parse(inp, table))
    # TODO assert table


def test3():
    grammar = dedent("""
        S GQ (S)S
        G FG ε
        F !s
        Q ?s
        """).strip()

    grammar = read_grammar(grammar)
    assert FOLLOW(grammar, "S") == {')', "#"}  # TODO correct?
    assert FOLLOW(grammar, "G") == {'?'}
    assert FOLLOW(grammar, "F") == {'!', '?'}
    assert FOLLOW(grammar, "Q") == {')', "#"}

    table = gen_table(grammar, "!?()s")
    assert {e:v[0] for e, v in table["S"].items()} == {"(": "(S)S", "!": "GQ", "?": "GQ"}
    assert {e:v[0] for e, v in table["G"].items()} == {"!": "FG", "?": "ε"}
    assert {e:v[0] for e, v in table["F"].items()} == {"!": "!s"}
    assert {e:v[0] for e, v in table["Q"].items()} == {"?": "?s"}
    #todo assert all others

    #inp = "!s(!s?s)?s" # C&G says test3 and test2 describe the same grammar but actually they dont?? (figure 8.7, 8.9)
    inp = "(!s?s)?s"
    print(parse(inp, table))


def test4():
    grammar = dedent("""
        S TE
        E +TE ε
        T FU
        U *FU ε
        F (S) i
        """).strip()

    grammar = read_grammar(grammar)
    table = gen_table(grammar, "i()+*")
    assert {e: v[0] for e, v in table["S"].items()} == {"(": "TE", "i": "TE"}
    assert {e: v[0] for e, v in table["E"].items()} == {")": "ε", "+": "+TE", "#": "ε"}
    assert {e: v[0] for e, v in table["T"].items()} == {"(": "FU", "i": "FU"}
    assert {e: v[0] for e, v in table["U"].items()} == {")": "ε", "*": "*FU", "+": "ε", "#": "ε"}
    assert {e: v[0] for e, v in table["F"].items()} == {"(": "(S)", "i": "i"}
    inp = "i+i*i"
    print(parse(inp, table))


def main():
    test1()
    test2()
    test3()
    test4()


if __name__ == "__main__":
    main()
