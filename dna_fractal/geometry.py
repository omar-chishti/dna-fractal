"""Sierpiński triangle cells, in the order a depth-first recursion visits them."""

import numpy as np

SQRT3_2 = np.sqrt(3) / 2


def sierpinski_cells(level: int) -> np.ndarray:
    """Leaf triangles of a level-`level` Sierpiński triangle with unit base.

    Returns an array of shape (3**level, 3, 2): one row per cell, three (x, y) vertices each,
    apex at the top. Cell i is the i-th leaf a recursion reaches when it visits the top,
    bottom-left and bottom-right sub-triangles in that order, so consecutive indices stay
    spatially close.
    """
    if level < 0:
        raise ValueError("level must be non-negative")
    cells = np.array([[[0.5, SQRT3_2], [0.0, 0.0], [1.0, 0.0]]])
    for _ in range(level):
        top, left, right = cells[:, 0], cells[:, 1], cells[:, 2]
        top_left = (top + left) / 2
        base = (left + right) / 2
        top_right = (right + top) / 2
        children = np.stack(
            [
                np.stack([top, top_left, top_right], axis=1),
                np.stack([top_left, left, base], axis=1),
                np.stack([top_right, base, right], axis=1),
            ],
            axis=1,
        )
        cells = children.reshape(-1, 3, 2)
    return cells


def level_for(n: int) -> int:
    """Smallest level whose triangle has at least `n` cells."""
    if n < 1:
        raise ValueError("n must be positive")
    level = 0
    while 3**level < n:
        level += 1
    return level


def subtriangle(level: int, path: str) -> slice:
    """Cell indices of the sub-triangle reached by `path`.

    `path` is a string of digits 0 (top), 1 (bottom-left) and 2 (bottom-right), read from the
    whole triangle inwards. Because cells are in visit order, every sub-triangle is one
    contiguous block.
    """
    if len(path) > level or any(step not in "012" for step in path):
        raise ValueError(f"invalid path {path!r} for level {level}")
    start, size = 0, 3**level
    for step in path:
        size //= 3
        start += int(step) * size
    return slice(start, start + size)
