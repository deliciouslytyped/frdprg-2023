# References:
#  file:///C:/Users/Lenovo/Downloads/vaszil_forditok.pdf
#  Alfred V. Aho, Monica S. Lam, Ravi Sethi, Jeffrey D. Ullman - Compilers - Principles, Techniques, and Tools-Pearson_Addison Wesley (2006).pdf


from textwrap import dedent
import string
from collections import defaultdict
from itertools import combinations
from functools import reduce

class Orsum: # todo callable?
    @staticmethod
    def orsum(iterable, start): # TODO make this a generator somehow?
        for i in iterable:
            start |= i
        return start

    @classmethod
    def check(cls):
        assert cls.orsum([{1, 2, 3}, {3, 4, 5}, {4, 5, 6}], frozenset()) == frozenset([1, 2, 3, 4, 5, 6])

orsum = Orsum.orsum
Orsum.check()

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


# TODO define syntax for grammar definitions
# terminals are uncapitalized words or symbols
# nonterminals are capitalized words
# right hand side alternatives must be separated by " | "
# left hand and right hand must be separated by " -> "
# currently it is assumed that the left hand of the first rule is the start symbol.
# the terminal epsilon is handled as a special case for the empty string/terminal,
#   as an implementation detail, only one epsilon is allowed on a right hand side by the epsilon elimination algorithm
# TODO the following is unimplemented currently:
# if the first two lines dont contain an arrow (otherwise error) then the first line
#  is taken to contain the start symbol and the second line the alphabet.
#  if an alphabet is defined, this enables assertions about it #TODO
def hazi_to_grammar(grmr):
    # add arrows to rules and separate alternatives, also separate adjacent characters with a space (rule right sides)
    # so transform something like S A BC D to S -> A | B C | D
    grmr = "\n".join(
        l.split()[0] + " -> " + " | ".join(
            map(lambda x: " ".join(x) if x != "epsilon" else x, l.split()[1:]) #TODO test epsilon
        ) if i >= 2 else l
        for i, l in enumerate(grmr.splitlines()))
    # split nonterminals
    return grmr

class Cases:
    grmr1 = dedent("""
        E -> E + E | E * E | num
        """).strip()

    # a CYK házi
    # TODO itt miért van különszedve az egyelemű és kételemű S jobboldal?
    grmr2 = hazi_to_grammar(dedent("""
        S
        a b
        S A B E C X Y Z
        S YB XA
        E YB XA
        A a YE XC
        B b XE YZ
        C AA
        X b
        Y a
        Z BB
        """).strip())

    leftrec1 = dedent("""
        A -> A a | b
        """).strip()

class MetaGrammar:
    @staticmethod
    def is_terminal(s: str): # TODO is this missing anything
        return s.lower() == s or s in string.punctuation

    @staticmethod
    def is_nonterminal(s: str):
        return s[0].isupper() and (len(s) == 1 or s[1:].isalnum())

class GrammarT: # TODO or you could probably just inherit from dict?
    def __init__(self, s, start=None, d=None):
        self.start = None
        self.alphabet = None  # only if defined in the second line of the grammar
        if not d:
            self.g = self.read(s)
        else:
            assert start
            self.start = start
            self.g = d

    def __repr__(self):  # TODO topologically sorted?
        ret = "\n".join(f'{k} -> {" | ".join(v)}' for k, v in self.g.items())
        return 'GrammarT("""%s""")' % ret

    # def __len__(self): # TODO number of rules or rule alternatives?

    def __getitem__(self, item):
        return self.g.__getitem__(item)

    def __eq__(self, other):
        return Z3Eq.eq(self, other)

    #TODO toposort / ordereddict (how to deal with cycles?)
    def read(self, s : str): # TODO handle alphabet and start symbol definition lines
        #TODO find start symbol by attempting topological sort?
        lines = s.splitlines()
        maybe_start = lines[0].split()
        if len(maybe_start) == 1:  # assume start symbol and alphabet declaration
            self.start = maybe_start[0]
            self.alphabet = lines[1].split()
            lines = lines[2:]
        else:
            self.start = lines[0].split(" -> ")[0]
        grmr = defaultdict(list)
        for l in lines:
            k, v = l.split(" -> ")
            grmr[k].extend(v.split(" | "))
        return grmr

    def terminals(self):
        grmr_items = set(sum([x.split() for x in sum(self.g.values(), [])], []))
        return {e for e in grmr_items if MetaGrammar.is_terminal(e)}

    def nonterminals(self):  # TODO technically shouldnt it be enough to just look at the left hand sides for nonterminals?
        return set(self.g.keys()) | orsum((self._nonterminals_of(left) for left in self.g.keys()), frozenset())
        #grmr_items = set(self.g.keys()) | set(sum([x.split() for x in sum(self.g.values(), [])], []))
        #return {e for e in grmr_items if MetaGrammar.is_nonterminal(e)}

    def _nonterminals_of(self, nt):
        # The nt in self.g condition is because g is a defaultdict so accesses will create empty rules for nts that dont have a rule entry
        if nt in self.g:
            return orsum(({x for x in alt.split() if MetaGrammar.is_nonterminal(x)} for alt in self.g[nt]), frozenset())
        else:
            return frozenset()

    def nonterminals_of(self, iterable): # TODO not sure if this is correct
        try:
            i = iter(iterable)
            if issubclass(iterable.__class__, str):
                raise TypeError
        except TypeError: # assume one item
            return self._nonterminals_of(iterable)
        else: # assume set of items
            return orsum((self._nonterminals_of(x) for x in iterable), frozenset())

    # undecidable? # can we do something with z3?
    def is_ambiguous(self):
        raise NotImplementedError

    # TODO should this use the nullable approahc or assume epsilons are eliminated first?
    # TODO
    # for each rule, any is in it's in it's own closure, its leftrec
    # TODO check if this is correct
    # TODO two definitions of leftrec? 1) any rule is left rec, 2) S is left rec? 3) it is a parent of a leftrec rule?
    #  Aho 4.3.3 lists \exists rule such that A *=> Aa as the def.
    def is_left_rec(self, nt=None):
        if not nt:
            lrs = frozenset()
            for r in self.g.keys():
                nts = fix(lambda x: frozenset(x) | self.nonterminals_of(x), self.nonterminals_of(r))
                if r in nts: # TODO this is wrong; the condition needs to be that ...A... has a nullable prefix
                    lrs |= {r}
            return lrs

        else:
            nts = fix(lambda x: frozenset(x) | self.nonterminals_of(x), self.nonterminals_of(nt))
            return nt in nts

    #  if lr is not specified, do the below for every rule (does the grammar have any epsilon rules?)
    # TODO/NOTE prefix if set does not make sense with idx=None? because every alternative could have a different prefix of interest
    #  if lr is specified, return if the rule right side is nullable up to prefix
    #  i.e. if prefix is the default -1, the whole rule can return the empty string #TODO/NOTE https://stackoverflow.com/questions/11337941/python-negative-zero-slicing
    #  otherwise prefix is the index inclusive up to which the rule is prefixable with epsilon
    #
    #  idx specifies the index of a specific alternative in the rule #TODO
    #
    #  This is used in LRE. TODO should this be used or should epsilons be eliminated first?
    #TODO tests
    #TODO can / should also be done with the full FIRST set algorithmll_lambdafree.py
    def is_nullable(self, lr=None, prefix=None, idx=None):  # TODO what do I need to do here again?
        assert not idx and prefix # idx implies prefix
        if lr:
            alts = [self.g[lr][idx]] if idx else self.g[lr]
            for alt in alts:
                altnullable = True
                for sym in alt[:prefix]: # TODO need to iter over alternatives
                    if sym == "epsilon":
                        continue
                    if MetaGrammar.is_terminal(sym):
                        altnullable = False #TODO needs to pass all alternatives
                        break
                    if self.is_nullable(sym):
                        continue
                if altnullable:
                    return True
            return False
        else:
            raise NotImplementedError

    def has_chain_rules(self):
        raise NotImplementedError

    def has_epsilon_rules(self): #TODO test
        for v in self.g.values():
            if v == ["epsilon"]:
                return True
        return False

    def reachable_nts(self):
        nts = fix(lambda x: frozenset(x) | self.nonterminals_of(x), self.nonterminals_of(self.start))
        return nts

    def reachable_ts(self):
        nts = self.reachable_nts()
        return (sym for nt in nts for alt in self.g[nt] for sym in alt.split())

    def has_reachable_epsilon_rules(self): #TODO test
        return "epsilon" in self.reachable_ts()

    # TODO
    # TODO look at https://en.wikipedia.org/wiki/Left_recursion#cite_note-Moore2000-2 and its wiki page
    #  The wiki page suggests that LRE algorithms may change the semantics?
    # TODO assert that there exists nonrecursive alternatives (bach ivan 3.17 formula megjegyzés)
    # TODO NOTE whats this on about cycles? ez a láncszabályos cucc?

    #TODO OK so I can LRE an indirect recursion if i have the chain, but how do I find the cains?
    # in bach he just convers the whole thing to greibach normal form

    # based on
    #  https://www.geeksforgeeks.org/removing-direct-and-indirect-left-recursion-in-a-grammar/
    #  https://en.wikipedia.org/wiki/Left_recursion
    #  bach ivan resz
    #  aho & co compilers book
    #  grune & ceriel eps-elim, unit-elim, cyk, lre sections
    # https://www.geeksforgeeks.org/converting-context-free-grammar-greibach-normal-form/
    def LRE(self, no_epsilon=False): # per grune and jacobs 6.4
        # Precondition by aho figure 4.11
        #  INPUT: Grammar G with no cycles or epsilon productions # TODO this means no epsilon rules right? #TODO can we leave epsilons in with the nullable check? (less modifications to the grammar) #TODO would it be equivalent to epsilon elimination, lre elimination, then epsilon reintroduction?, where does this fall in relation to chomsky normalization?
        assert self.has_cycles() == False and self.is_nullable() == False

        # Assert leftrec eliminiation succeeded, Aho 4.3.3 suggests the above procedure doesnt always work? # TODO
        assert bool(self.is_left_rec()) == False
        return self

    # https://www.geeksforgeeks.org/converting-context-free-grammar-greibach-normal-form/
    # https://en.wikipedia.org/wiki/Greibach_normal_form
    def GNF(self):
        pass

    # TODO
    def left_factor(self):
        raise NotImplementedError

    ### CNF ###
    # http://informatikdidaktik.de/InformaticaDidactica/LangeLeiss2009
    # https://en.wikipedia.org/wiki/Chomsky_normal_form

    #TODO alias these to, or alias to these, more descriptive names, or not

    def START(self): # TODO test
        assert "S0" not in self.nonterminals() #TODO functiinality to generate new symbols
        self.g["S0"] = [ self.g[self.start] ]
        self.start = "S0"
        return self

    def TERM(self):
        return self

    def BIN(self):
        return self

    def UNIT(self):
        #It is generally permitted that the start symbol is the only one that may produce epsilon

        return self

    #TODO https://en.wikipedia.org/wiki/Chomsky_normal_form#DEL:_Eliminate_%CE%B5-rules
    def DEL(self): # per grune and jacobs
        import copy #TODO
        d = copy.deepcopy(self.g)
        #tofix = list()
        #epsilons = [ (k, i) for k, v in d.items() for i, e in enumerate(v) if e == "epsilon" ]
        #for k, v in d.items():
        #    alts = list()
        #    for alt in v:
        #        pass
        #    d[k] = alts
        ##for k, v in d.items():
        ##    for i, e in enumerate(v):
        ##        if nullable(e[0]):
        ##            pass
        ##        elif all(nullable, e.split()):
        ##            pass

        #epsilons = lambda: ((k, i) for k, v in d.items() for i, e in enumerate(v) if e == "epsilon")
        ##TODO does this need a try catch stopiteration
        #while eps := next(epsilons()):
        #    k, i = eps

        findepsilon = lambda d, eliminated: ((k, i) for k, v in d.items() for i, e in enumerate(v) if e == "epsilon" and k not in eliminated)
        #new = list()
        #done = list()
        #while eps := next(findepsilon(d)): # TODO deleting changes alternative indexes / cyk back and forth, 1) dont care full mutation 2) should replace rules and add new ones etc
        #    eps_k, eps_i = eps
        #    for k, v in d:
        #        for i, e in enumerate(v):
        #            for j, r in enumerate(e.split()):
        #                if r == eps:
        #                    new.append((k, e.replace(r, f"{r}prime", 1))) #TODO need some kind of symbol generator
        #                    new.append((k, e.replace(r, "", 1))) #TODO need some kind of symbol generatorx

        eliminated = list()
        try:
            while eps := next(findepsilon(d, eliminated)):
                eps_k, eps_i = eps
                #d[eps_k].pop(eps_i) # TODO what if empty # dont remove because book?
                #if not d[eps_k]: # TODO should remove rule if removing epsilon is the last one?
                #    del d[eps_k]
                while eps_k in GrammarT(None, start=self.start, d=d).reachable_nts(): #TODO this will cause introduction of empty prime rules as it computes the nt closure on defauldict
                    for k, v in d.items():
                        for i, alt in enumerate(v):
                            finish_alt, itt = False, enumerate(alt.split()) #for k, sym in enumerate(alt.split())
                            try:
                                while not finish_alt and (v := next(itt)): #TODO
                                    j, sym = v
                                    if sym == eps_k:
                                        d[k].append(alt.replace(sym, f"{sym}prime", 1)) #TODO need some kind of symbol generator
                                        with_removed = alt.split()
                                        with_removed.remove(eps_k)
                                        if with_removed: # not empty
                                            d[k].append(" ".join(with_removed)) #TODO need some kind of symbol generatorx
                                        d[k].pop(i) #TODO explain this; not removing due to see book?
                                        finish_alt = True
                            except StopIteration:
                                pass

                eliminated.append(eps_k)
        except StopIteration:
            pass

        def all_syms_exist(alt):
            for sym in alt:
                if sym not in GrammarT(start=self.start, d=d):
                    return False
            return True

        for k in d:
            d[k] = [alt for alt in d[k] if all_syms_exist(alt)]

        self.g = d
        return self

    ### LL grammar ops ###

    def FIRST(self, rule):
        return self

    def FOLLOW(self, rule):
        return self

    #TODO

class TestGrammarT:  # TODO # TODO I should really be using unittest for this shouldnt I?
    @classmethod
    def check(cls):
        cls.test_grmr1()
        cls.test_grmr2()
        #cls.test_nullable()
        cls.test_leftrec1()
        cls.test_epsilon()
        cls.test_unit_rules()

    @staticmethod
    def test_grmr1():
        g = GrammarT(Cases.grmr1)
        print(g)
        assert g._nonterminals_of("E") == {"E"}
        #assert g._nonterminals_of(["E", "E", "E"]) == {"E"} # only accepts one item
        assert g.nonterminals_of("E") == {"E"}
        assert g.nonterminals_of(["E", "E", "E"]) == {"E"}
        #assert g._terminals_of("") #TODO
        assert g.nonterminals() == {"E"}
        assert g.terminals() == {"*", "+", "num"}
        assert g.start == "E"
        #assert g. # TODO assert rule set
        #TODO I think book said ambiguity is undecidable so we cant test that?
        assert bool(g.is_left_rec())
        pass # assert g.LRE().is_left_rec() is False

    @staticmethod
    def test_grmr2(): # TODO
        g = GrammarT(Cases.grmr2)
        assert g.is_left_rec() == {'Z', 'C', 'A', 'B', 'E'} # TODO check this
        assert bool(g.is_left_rec("S")) is False
        assert g.nonterminals() - g.is_left_rec() == {"Y", "S", "X"} # TODO check this #TODO probably wrong, previous definition of is_left_rec didnt account for nullable prefixes
        print(g)
        #rr = g.z3()
        #pass

    @staticmethod
    def test_leftrec1():
        g = GrammarT(Cases.leftrec1)
        #assert g.LRE() == GrammarT(dedent("""
        #    A -> b A2
        #    A2 -> a A2 | epsilon
        #    """).strip())
        #assert g.LRE(no_epsilon=True) == GrammarT(dedent("""
        #    A -> b A2
        #    A2 -> a A2 | epsilon
        #    """).strip())
        #print(g)

    @staticmethod
    def test_epsilon():
        g = GrammarT("""B -> A\nA -> epsilon""")
        #assert g.has_epsilon_rules()
        #assert not g.DEL().has_epsilon_rules()
        assert g.has_reachable_epsilon_rules()
        assert not g.DEL().has_reachable_epsilon_rules()

    @staticmethod
    def test_unit_rules():
        g = GrammarT("""A -> A""")
        assert g.has_chain_rules() # TODO
        assert g.UNIT().has_chain_rules()

    @staticmethod
    def test_nullable():
        g = GrammarT(dedent("""
            A -> epsilon
            B -> A
            C -> b A
            D -> A B
            E -> A C b
            F -> A A b
            """).strip())
        assert g.is_nullable("A")
        assert g.is_nullable("B")
        assert not g.is_nullable("C")
        assert g.is_nullable("D")
        assert not g.is_nullable("E", -1)
        assert g.is_nullable("F", -1)


flip = lambda f: lambda a, b: f(b, a)
foldr = lambda f, l: reduce(flip(f), reversed(l))

from z3 import *
class Z3Eq:
    @staticmethod
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

    @staticmethod
    def ruleset_eq(idom, jdom, rs1: Array, rs2: Array):
        assert rs1.sort() == ArraySort(StringSort(), SetSort(ArraySort(IntSort(), StringSort())))
        assert rs2.sort() == ArraySort(StringSort(), SetSort(ArraySort(IntSort(), StringSort())))
        constr = list()
        for i in idom:  # forall i there exists j such that the set of alternatives for the rule are the same
            expr = lambda a, b: Or(
                And(SetUnion(Select(rs1, i), Select(rs2, a)) == Select(rs1, i),
                    SetUnion(Select(rs1, i), Select(rs2, a)) == Select(rs2, a)),
                b)
            constr.append(foldr(expr, list(jdom) + [False]))
        return constr

    @classmethod
    def eq(cls, g1, g2):
        s1, r1, constr1 = cls.to_ruleset(g1, 1)
        s2, r2, constr2 = cls.to_ruleset(g2, 2)
        constr3 = cls.ruleset_eq(s1.values(), s2.values(), r1, r2)
        s = Solver()
        constraints = constr1 + constr2 + constr3
        s.add(*constraints)
        if s.check() == sat:
            return True
        else:
            return False

    @classmethod
    def check(cls):
        # TODO refactor
        _grmr1 = dedent("""
            A -> A a | b
            """).strip()

        _grmr2 = dedent("""
            B -> B a | b
            """).strip()

        grmr1 = GrammarT(_grmr1)
        grmr2 = GrammarT(_grmr2)

        assert cls.eq(grmr1, grmr2)
        assert not cls.eq(GrammarT("A -> c"), GrammarT("B -> a b"))
        assert not cls.eq(GrammarT("A -> c"), GrammarT("B -> a"))
        assert cls.eq(GrammarT("A -> c"), GrammarT("B -> c"))
        # assert not eq(GrammarT("A -> c | A"), GrammarT("B -> c | A"))  # TODO does this count? the latter grammar is ill defined
        assert cls.eq(GrammarT("A -> c | A"), GrammarT("B -> c | B"))
        assert not cls.eq(GrammarT("A -> c | A"), GrammarT("B -> c | a B"))
        assert cls.eq(GrammarT("A -> c | A\nA -> c"), GrammarT("B -> c | A\nA -> c"))
        assert not cls.eq(GrammarT("A -> c | A\nA -> b"), GrammarT("B -> c | A\nA -> b"))


if __name__ == "__main__":
    #TestGrammarT.check()
    GrammarT(dedent("""
        S -> L a M
        L -> L M
        L -> epsilon
        M -> M M
        M -> epsilon""").strip()).DEL()

