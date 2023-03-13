from z3 import *
from textwrap import dedent
from grammar_trf import GrammarT, MetaGrammar
from itertools import combinations
import string
from functools import reduce


flip = lambda f: lambda a, b: f(b, a)
foldr = lambda f, l: reduce(flip(f), reversed(l))


def to_ruleset(grmr: GrammarT, rulesetnum):
    syms = {x: String(f"r{rulesetnum}_{x}") for x in grmr.nonterminals()}
    distinct_constraints = [a != b for a, b in combinations(syms.values(), 2)]
    domain = list(string.ascii_uppercase[:len(syms)])
    domain_constraints = [foldr(lambda a, b: Or((x == a), b), domain + [False]) for x in syms.values()]

    constraints = list()
    rules = Array("rules%s" % rulesetnum, StringSort(), SetSort(ArraySort(IntSort(), StringSort())))
    for k, v in grmr.g.items():
        _alts = EmptySet(ArraySort(IntSort(), StringSort()))
        for i, alt in enumerate(v):
            _alt = Array(f"r{rulesetnum}_{k}{i}", IntSort(), StringSort())
            _alts = SetAdd(_alts, _alt)
            constraints.extend([Select(_alt, j) == (syms[e] if MetaGrammar.is_nonterminal(e) else e)
                                for j, e in enumerate(alt.split())])
            constraints.append(IsMember(_alt, Select(rules, syms[k])))
        constraints.append(IsSubset(Select(rules, syms[k]), _alts))
    return syms, rules, sum([distinct_constraints, domain_constraints, constraints], [])


def ruleset_eq(idom, jdom, rs1: Array, rs2: Array):
    assert rs1.sort() == ArraySort(StringSort(), SetSort(ArraySort(IntSort(), StringSort())))
    assert rs2.sort() == ArraySort(StringSort(), SetSort(ArraySort(IntSort(), StringSort())))
    constr = list()
    for i in idom: # forall i there exists j such that the set of alternatives for the rule are the same
        expr = lambda a, b: Or(
            And(SetUnion(Select(rs1, i), Select(rs2, a)) == Select(rs1, i),
                SetUnion(Select(rs1, i), Select(rs2, a)) == Select(rs2, a)),
            b)
        constr.append(foldr(expr, list(jdom) + [False]))
    return constr


def eq(g1, g2):
    s1, r1, constr1 = to_ruleset(g1, 1)
    s2, r2, constr2 = to_ruleset(g2, 2)
    constr3 = ruleset_eq(s1.values(), s2.values(), r1, r2)
    s = Solver()
    constraints = constr1 + constr2 + constr3
    s.add(*constraints)
    if s.check() == sat:
        return True
    else:
        return False

if __name__ == "__main__":  # TODO refactor
    _grmr1 = dedent("""
        A -> A a | b
        """).strip()

    _grmr2 = dedent("""
        B -> B a | b
        """).strip()

    grmr1 = GrammarT(_grmr1)
    grmr2 = GrammarT(_grmr2)

    assert eq(grmr1, grmr2)
    assert not eq(GrammarT("A -> c"), GrammarT("B -> a b"))
    assert not eq(GrammarT("A -> c"), GrammarT("B -> a"))
    assert eq(GrammarT("A -> c"), GrammarT("B -> c"))
    #assert not eq(GrammarT("A -> c | A"), GrammarT("B -> c | A"))  # TODO does this count? the latter grammar is ill defined
    assert eq(GrammarT("A -> c | A"), GrammarT("B -> c | B"))
    assert not eq(GrammarT("A -> c | A"), GrammarT("B -> c | a B"))
    assert eq(GrammarT("A -> c | A\nA -> c"), GrammarT("B -> c | A\nA -> c"))
    assert not eq(GrammarT("A -> c | A\nA -> b"), GrammarT("B -> c | A\nA -> b"))
