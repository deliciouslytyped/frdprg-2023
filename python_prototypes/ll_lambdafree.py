import string
from textwrap import dedent
from collections import defaultdict


def is_t(sym):
    return sym in string.punctuation or sym.islower()


def read_grammar(s):
    acc = 0
    return {e[0]: [(v, acc := acc + 1) for v in e[1:]] for line in s.splitlines() for e in [line.split()]}


#TODO this doesnt exactly follow C&H algorithm
# homogeneous treatment of nt and t
def FIRST(grammar, _sym, parentset=None):  # TODO may need modifications on the recursion checking if
    _sym = _sym[0] # extract the sym from the (rule, idx) pair in the grammar

    if parentset is None:
        parentset = set()

    if is_t(_sym):
        return frozenset((_sym,))

    return frozenset.union(*[(set() if sym in parentset else FIRST(grammar, sym, parentset | {sym})) # union is invariant over left recursion
                       for alt in grammar[_sym] for sym in [alt[0][0]]])  # TODO handle empty when not lambdafree?


# as an implementation detail we assume here that there are no first/first conflicts and the language is ll;
# the dictionary maps >rules of a nt< to each of their respective first terminals,
# so if multiple alternatives in a rule have a same first terminal the behaviour is undefined
def gen_table(grammar, terminalish="#"):

    err = lambda: "error"
    table = defaultdict(lambda: defaultdict())
    #table.update({lhs: {rule[1][0]: rule for rule in rhs} for lhs, rhs in grammar.items()})
    table.update({lhs: defaultdict(err, {list(FIRST(grammar, rule[0]))[0]: rule for rule in rhs}) for lhs, rhs in grammar.items()})
    table.update({c: defaultdict(err, {c: "pop" if c != "#" else "accept"}) for c in terminalish})

    return table


def parse(inp, table):
    anal, pred = list(), list("S")
    for c in inp:
        while True:
            print(anal, pred)
            if pred:  # TODO is this correct? # wrong, needs to empty simultaneously with hash and inp
                action = table[(v := pred.pop())][c]
            else:
                action = "error"

            if action == "pop":
                print(c)
                break
            elif action == "error":
                raise ValueError
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


def main():
    test1()
    test2()


if __name__ == "__main__":
    main()
