"""Drawing values onto Sierpiński cells with matplotlib."""

from collections.abc import Sequence
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

from .geometry import SQRT3_2

# The poster's colours: CSS named colours, except AT, which was black and vanished on the
# black ground.
POSTER_PALETTE = {
    "TT": "red", "AG": "lime", "II": "cyan", "DI": "brown", "AT": "#02A451",
    "CC": "blue", "CT": "pink", "AA": "yellow", "DD": "orange", "GG": "green",
    "T": "indigo", "G": "grey", "A": "gold", "D": "navy", "AC": "magenta",
    "I": "violet", "GT": "teal", "C": "silver", "--": "purple", "CG": "lavender",
}  # fmt: skip


@dataclass(frozen=True)
class Theme:
    ground: str
    ink: str
    ink_dim: str
    padding_fill: str | None
    padding_edge: str | None
    missing: str


PLATE = Theme(
    ground="black",
    ink="#ebe6da",
    ink_dim="#8f8a80",
    padding_fill=None,
    padding_edge="#ebe6da30",
    missing="#262626",
)

IBS_PALETTE = {0: "#ff5a36", 1: "#a3adb8", 2: "#46505b"}


def colours_for(values: Sequence, palette: dict, n_cells: int, missing: str) -> list[str | None]:
    """One colour per cell: values in order, then None for each padding cell."""
    if len(values) > n_cells:
        raise ValueError(f"{len(values)} values do not fit in {n_cells} cells")
    colours: list[str | None] = [palette.get(v, missing) for v in values]
    return colours + [None] * (n_cells - len(colours))


def flip(cells: np.ndarray) -> np.ndarray:
    """The same cells reflected top to bottom, apex down, occupying the same height."""
    flipped = cells.copy()
    flipped[..., 1] = SQRT3_2 - flipped[..., 1]
    return flipped


def draw(
    ax: plt.Axes,
    cells: np.ndarray,
    colours: Sequence[str | None],
    theme: Theme,
    offset: tuple[float, float] = (0.0, 0.0),
) -> list[PolyCollection]:
    """Fill each cell with its colour; draw padding cells (None) in the theme's padding style.

    Hairline edges in the face colour close the seams between filled cells.
    """
    polys = cells + np.asarray(offset)
    padding = np.array([c is None for c in colours])
    filled = [c for c in colours if c is not None]
    collections = [
        PolyCollection(polys[~padding], facecolors=filled, edgecolors=filled, linewidths=0.05)
    ]
    if padding.any():
        collections.append(
            PolyCollection(
                polys[padding],
                facecolors=theme.padding_fill or "none",
                edgecolors=theme.padding_edge or theme.padding_fill,
                linewidths=0.15 if theme.padding_edge else 0.05,
            )
        )
    for collection in collections:
        ax.add_collection(collection)
    return collections
