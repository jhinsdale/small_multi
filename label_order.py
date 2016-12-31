#!/usr/bin/env python3

from small_multi import toposort


def main():
    seqs = [
        [1, 4, 7],
        [1, 2, 4],
        [3, 5, 6, 7],
        [2, 3, 6],
    ]
    print(total_order(seqs))


# Merge partial orderings into a total ordering by topo-sorting an order graph
def total_order(seqs):
    ordering = {}
    for seq in seqs:
        if len(seq) <= 1:
            continue
        for i in range(len(seq) - 1):
            ordering.setdefault(seq[i + 1], set()).add(seq[i])
    result = []
    for ties in toposort(ordering):
        for item in sorted(ties):
            result.append(item)
    return result


if __name__ == "__main__":
    main()
