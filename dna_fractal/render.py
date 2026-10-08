"""Drawing values onto Sierpiński cells with matplotlib."""

from collections.abc import Sequence

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

PADDING = "white"
BACKGROUND = "black"

IBS_PALETTE = {0: "#ff3b30", 1: "#5a5a5a", 2: "#262626"}
MISSING = "#101010"


def colours_for(values: Sequence, palette: dict, n_cells: int, padding: str = PADDING) -> list:
    """One colour per cell: values in order, then padding for the cells left over."""
    if len(values) > n_cells:
        raise ValueError(f"{len(values)} values do not fit in {n_cells} cells")
    colours = [palette.get(v, MISSING) for v in values]
    return colours + [padding] * (n_cells - len(colours))


def flip(cells: np.ndarray) -> np.ndarray:
    """The same cells reflected top to bottom, apex down, occupying the same height."""
    flipped = cells.copy()
    flipped[..., 1] = SQRT3_2 - flipped[..., 1]
    return flipped


def draw(ax: plt.Axes, cells: np.ndarray, colours: Sequence, offset=(0.0, 0.0)) -> None:
    """Fill each cell with its colour. Hairline edges in the face colour close the seams."""
    polys = cells + np.asarray(offset)
    ax.add_collection(
        PolyCollection(polys, facecolors=colours, edgecolors=colours, linewidths=0.05)
    )


def canvas(width: float, height: float = SQRT3_2, size: float = 8.0, margin: float = 0.03):
    """A black figure with equal-aspect axes framing [0, width] x [0, height]."""
    fig, ax = plt.subplots(figsize=(size, size * height / width), facecolor=BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(-margin, width + margin)
    ax.set_ylim(-margin, height + margin)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    return fig, ax
