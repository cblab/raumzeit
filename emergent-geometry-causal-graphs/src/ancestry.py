from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ancestry:
    """Stores parent relations and birth step for each node id."""

    parents: list[list[int]] = field(default_factory=list)
    birth_step: list[int] = field(default_factory=list)


def create_ancestry(max_nodes: int) -> Ancestry:
    return Ancestry(parents=[[] for _ in range(max_nodes)], birth_step=[-1 for _ in range(max_nodes)])


def register_node(a: Ancestry, node_id: int, step: int, parents: list[int] | None = None) -> None:
    a.birth_step[node_id] = int(step)
    a.parents[node_id] = list(parents or [])


def node_parents(a: Ancestry, node_id: int) -> list[int]:
    return list(a.parents[node_id])


def lineage(a: Ancestry, node_id: int, max_depth: int = 8) -> set[int]:
    """Returns ancestor set using bounded breadth-first expansion."""

    frontier = [node_id]
    out: set[int] = set()
    depth = 0
    while frontier and depth < max_depth:
        nxt: list[int] = []
        for u in frontier:
            for p in a.parents[u]:
                if p not in out:
                    out.add(p)
                    nxt.append(p)
        frontier = nxt
        depth += 1
    return out


def shared_ancestor_fraction(a: Ancestry, i: int, j: int, max_depth: int = 8) -> float:
    ai = lineage(a, i, max_depth=max_depth)
    aj = lineage(a, j, max_depth=max_depth)
    if not ai and not aj:
        return 0.0
    inter = len(ai & aj)
    union = len(ai | aj)
    if union == 0:
        return 0.0
    return inter / union
