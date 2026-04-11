"""Core causal set data structure for calibration experiments."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CausalSet:
    """Simple finite causal set with integer-labeled elements.

    Relations are stored as a directed adjacency map where ``x -> y`` means
    ``x ≺ y``.
    """

    _elements: set[int] = field(default_factory=set)
    _future: dict[int, set[int]] = field(default_factory=dict)

    def _ensure_element(self, x: int) -> None:
        self._elements.add(x)
        self._future.setdefault(x, set())

    def add_element(self, x: int) -> None:
        """Add a single element id if not already present."""
        self._ensure_element(x)

    def add_relation(self, x: int, y: int) -> None:
        """Add relation ``x ≺ y``.

        Raises:
            ValueError: If ``x == y`` or if adding this edge creates a cycle.
        """
        if x == y:
            raise ValueError("Reflexive relations are not allowed in a causal set.")

        self._ensure_element(x)
        self._ensure_element(y)

        if self.is_related(y, x):
            raise ValueError("Adding relation would create a cycle.")

        self._future[x].add(y)

    def is_related(self, x: int, y: int) -> bool:
        """Return ``True`` if ``x ≺ y`` via transitive reachability."""
        if x == y or x not in self._elements or y not in self._elements:
            return False

        visited: set[int] = set()
        stack = [x]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for nxt in self._future.get(current, set()):
                if nxt == y:
                    return True
                if nxt not in visited:
                    stack.append(nxt)
        return False

    def future_of(self, x: int) -> set[int]:
        """Return all elements to the causal future of ``x``."""
        if x not in self._elements:
            return set()
        return {y for y in self._elements if self.is_related(x, y)}

    def past_of(self, x: int) -> set[int]:
        """Return all elements to the causal past of ``x``."""
        if x not in self._elements:
            return set()
        return {y for y in self._elements if self.is_related(y, x)}

    def interval(self, x: int, y: int) -> set[int]:
        """Return the Alexandrov interval I(x, y) = {z | x ≺ z ≺ y}."""
        if not self.is_related(x, y):
            return set()
        return {
            z
            for z in self._elements
            if z not in {x, y} and self.is_related(x, z) and self.is_related(z, y)
        }

    def cardinality(self) -> int:
        """Return number of elements in the causal set."""
        return len(self._elements)

    def transitive_closure(self) -> dict[int, set[int]]:
        """Compute transitive closure reachability map."""
        closure: dict[int, set[int]] = {}
        for x in self._elements:
            closure[x] = self.future_of(x)
        return closure

    def validate_acyclic(self) -> bool:
        """Return ``True`` if no directed cycle is present."""
        visited: set[int] = set()
        active: set[int] = set()

        def dfs(node: int) -> bool:
            visited.add(node)
            active.add(node)
            for nxt in self._future.get(node, set()):
                if nxt not in visited:
                    if not dfs(nxt):
                        return False
                elif nxt in active:
                    return False
            active.remove(node)
            return True

        for element in self._elements:
            if element not in visited and not dfs(element):
                return False
        return True

    def validate_transitive(self) -> bool:
        """Return ``True`` if direct relations obey transitivity constraints.

        For all x->y and y->z, this verifies x reaches z.
        """
        for x in self._elements:
            for y in self._future.get(x, set()):
                for z in self._future.get(y, set()):
                    if not self.is_related(x, z):
                        return False
        return True

    @property
    def elements(self) -> set[int]:
        """Return a copy of element ids."""
        return set(self._elements)

    @property
    def direct_relations(self) -> dict[int, set[int]]:
        """Return a copy of direct adjacency relations."""
        return {k: set(v) for k, v in self._future.items()}
