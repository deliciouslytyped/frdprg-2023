# Terms: lhs - left hand side, rhs - right hand side

from textwrap import dedent
from itertools import product
from collections import defaultdict
from typing import *


# MyPy type aliases
Index = Mapping[str, Set[str]]  # reverse the grammar; pair of rhs nonterminals as a string -> set of possible lhs
Table = List[List[Set[str]]]  # The CYK "pyramid"
Grammar = Mapping[str, List[str]]  # lhs -> rhs
DiagonalRow = List[Set[str]]  # Used in the online mode, it's just an alias


class CYK:
    @staticmethod
    def read_grammar(grammar: str) -> Grammar:
        # We don't care about the metadata lines because we don't need them.
        # start, l2, l3 = grammar.splitlines()[:3]
        # alphabet = l2.split()
        # nonterminals = l3.split()
        return {x[0]: x[1:] for line in grammar.splitlines()[3:] for x in [line.split()]}

    # This "reverses" the grammar and yields an "index" that makes it easy
    # to look up the set of rules that can yield a given RHS.
    @staticmethod
    def build_index(grammar: Grammar) -> Index:
        index = defaultdict(set)
        for k, v in grammar.items():
            for alt in v:
                index[alt].add(k)
        return index

    # returns the set of lhs belonging to each element in a list of rhs, e.g. used like lhs_set_of(["AB", "CD"], index) -> {"E"}
    @staticmethod
    def lhs_set_of(alts: Iterable[str], index: Index) -> Set[str]:
        return set.union(*(index[alt] if alt in index else set() for alt in alts), set())

    # CYK with offline order traversal
    # This means the table is built diagonal by diagonal (like \ )
    # This allows to fill the table as the string is read from left to right
    #
    # Due to this, we can implement it as a generator
    #
    # See Grune & Jacobs (2008) (4.2.2 CYK Recognition with a Grammar in Chomsky Normal Form,
    #   Fig 4.9 "Different orders in which the recognition table can be computed")
    @classmethod
    def online_cyk(cls, index: Index, inp: Iterable[str]) -> Iterator[DiagonalRow]:
        table: Table = []  # The rows will be what are the \ shaped diagonals in the table of the offline parsing method
        # For each character in the input, we fill the diagonal belonging to it, starting wit the base case, and then
        # filling the rest of the diagonal, element by element. (Each element is a set of lhs).
        #
        # The index of the "diagonal" ("as a row") is the current length of the table
        for s in inp:
            assert s in index

            # we don't subtract one because the table is one short (the diagonal we are about to append)
            diag_idx = len(table)
            diagonal: DiagonalRow = [cls.lhs_set_of(s, index)]  # fill the base case of this diagonal
            for i in range(1, diag_idx+1):  # count from 1, because the base case is already filled
                diagonal.append(s := set())
                for offset in range(i):
                    # left diagonal index, right diagonal index, (in the "visible" orientation) in opposite offset directions
                    left = table[diag_idx - i + offset][offset]  # TODO yeah, this one is kind of complicated to explain
                    right = diagonal[i - 1 - offset]  # for the right side, we only need to index into the diagonal

                    # construct the cartesian product of currently viewed "child" entries, and collect their lhs set
                    alts = set(a + b for a, b in product(left, right))
                    s.update(cls.lhs_set_of(alts, index))

            # we've calculated the diagonal / next column of the online traversal.
            table.append(diagonal)
            yield diagonal

    # CYK with offline order traversal
    # This means the table is built row by row
    #
    # Everything is basically the same as the online mode except the indexing.
    @classmethod
    def offline_cyk(cls, index: Index, inp: str) -> Table:
        for c in inp:
            assert c in index

        inp_l = len(inp)
        table = [[set() for _ in range(inp_l - i)] for i in range(inp_l)]  # upper left triangular list of empty lists

        # initialize first row
        for i, c in enumerate(inp):
            table[0][i] = cls.lhs_set_of(c, index)

        for r in range(1, inp_l):  # start count from 1 because first row is already initialized
            for c in range(inp_l - r):  # for each cell in row
                for offset in range(r):  # for each along the "diagonal" / (for each string offset of the divider)
                    # left diagonal, right diagonal, in opposite offset directions
                    left = table[offset][c]  # coordinate relative to the first cell of the table
                    right = table[(r - 1) - offset][1 + c + offset]  # first coordinate relative to below top of pyramid
                    alts = set(a + b for a, b in product(left, right))
                    table[r][c].update(cls.lhs_set_of(alts, index))

        return table

    # Pretty-print the offline mode table
    @staticmethod
    def print_table(table: Table, inp: str) -> None:
        to_print = [["[%s]" % ", ".join(cell) for cell in row] for row in reversed(table)]
        max_cell_len = max([len(c) for row in to_print for c in row])
        to_print = [[cell.center(max_cell_len) for cell in row] for row in to_print]
        max_row = len(table[0]) * max_cell_len
        for r in to_print:
            print("".join(r).center(max_row))
        print(*(c.center(max_cell_len-1) for c in inp), end="")  # TODO There is an off-by-one here for some reason?? (remove the -1 to see it)
        print()
        print()


# Uses the test data from the homework
class TestCYK:
    grammar = dedent("""
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
        """).strip()

    @classmethod
    def main(cls):
        inp = "ababbabbaba"

        grammar = CYK.read_grammar(cls.grammar)
        index = CYK.build_index(grammar)
        offline_table = CYK.offline_cyk(index, inp)
        CYK.print_table(offline_table, inp)

        diagonals = list()
        for c, diagonal in zip(inp, CYK.online_cyk(index, inp)):
            diagonals.append(diagonal)
            # We can't really pretty-print in the online mode because
            # we don't know how big future cells will be
            print(c, diagonal)

        online_table: Table = list()
        size = len(diagonals[-1])
        for i in range(size):
            online_table.append([diagonals[j][i] for j in range(size) if i <= j])

        # Consistency test: the table of the online traversal should be the same as the offline traversal.
        assert offline_table == online_table
        # TODO assert some known good parses


if __name__ == "__main__":
    TestCYK.main()
