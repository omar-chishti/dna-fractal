"""The two plates: one genome on one chromosome, and identity by state between pairs."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .genome import CENTROMERES, arms, ibs
from .geometry import SQRT3_2, sierpinski_cells
from .plate import BODY, HEADING, caption, footer, loupe, plate, width
from .render import IBS_PALETTE, PLATE, POSTER_PALETTE, Theme, colours_for, draw, flip

LEVEL = 10

GENOTYPE_GROUPS = [
    ["AA", "CC", "GG", "TT"],
    ["AC", "AG", "AT", "CG", "CT", "GT"],
    ["DD", "II", "DI"],
    ["A", "C", "G", "T", "D", "I"],
]


def _page(extent, inches: float) -> tuple[float, float]:
    x0, x1, y0, y1 = extent
    return inches, inches * (y1 - y0) / (x1 - x0)


def _blocks(cells: np.ndarray, depth: int) -> tuple[np.ndarray, int]:
    size = 3 ** (LEVEL - depth)
    return cells.reshape(-1, size, 3, 2).mean(axis=(1, 2)), size


def _nearest_block(cells: np.ndarray, target, filled: int, depth: int = 4) -> np.ndarray:
    """Centre of the depth-`depth` sub-triangle nearest `target` that holds only data."""
    centres, size = _blocks(cells, depth)
    distance = np.hypot(*(centres - np.asarray(target)).T)
    distance[(np.arange(len(centres)) + 1) * size > filled] = np.inf
    return centres[np.argmin(distance)]


def _genotype_key(present: set[str]) -> list[list[tuple[str | None, str]]]:
    groups = [
        [(POSTER_PALETTE[call], call.lower()) for call in group if call in present]
        for group in GENOTYPE_GROUPS
    ]
    other = [(POSTER_PALETTE["--"], "no call")] if "--" in present else []
    return [group for group in groups if group] + [[*other, (None, "padding")]]


def genome_plate(
    genome: pd.DataFrame, chromosome: str, subtitle: str, kicker: str, theme: Theme = PLATE
) -> plt.Figure:
    """A chromosome as a diptych: the p arm upright, the q arm inverted beside it."""
    cells = sierpinski_cells(LEVEL)
    flipped = flip(cells)
    p, q = arms(genome, chromosome)
    p_colours = colours_for(list(p["genotype"]), POSTER_PALETTE, len(cells), theme.missing)
    q_colours = colours_for(list(q["genotype"]), POSTER_PALETTE, len(cells), theme.missing)

    extent = (-0.06, 1.56, -0.26, 0.97)
    fig, ax = plate(*_page(extent, 16.0), extent, theme)
    draw(ax, cells, p_colours, theme)
    draw(ax, flipped, q_colours, theme, offset=(0.5, 0))

    p_source = tuple(_nearest_block(cells, (0.33, 0.52), len(p)))
    loupe(ax, cells, p_colours, theme, p_source, 0.022, (0.13, 0.69), 0.17)
    q_source = tuple(_nearest_block(flipped, (0.66, 0.30), len(q)) + [0.5, 0])
    loupe(ax, flipped, q_colours, theme, q_source, 0.022, (1.37, 0.18), 0.17, offset=(0.5, 0))

    arm = {"size": HEADING, "small_caps": False, "ha": "center"}
    caption(ax, 0.5, SQRT3_2, f"{chromosome}p", theme, dy=10, va="bottom", **arm)
    caption(ax, 1.0, 0.0, f"{chromosome}q", theme, dy=-10, va="top", **arm)

    key = _genotype_key(set(p["genotype"]) | set(q["genotype"]))
    footer(ax, 0.0, 1.5, -0.08, key, (kicker, f"Chromosome {chromosome}", subtitle), theme)
    return fig


def _source_block(cells: np.ndarray, none_shared: np.ndarray) -> np.ndarray:
    """Centre of the upper-half sub-triangle with the most cells sharing no allele."""
    centres, size = _blocks(cells, 4)
    padded = np.r_[none_shared, np.zeros(len(cells) - len(none_shared), bool)]
    counts = np.add.reduceat(padded, np.arange(0, len(cells), size)).astype(float)
    counts[centres[:, 1] < 0.40] = -1
    return centres[np.argmax(counts)]


def ibs_plate(
    table: pd.DataFrame,
    pairs: Sequence[tuple[str, str, str]],
    chromosome: str,
    subtitle: str,
    kicker: str,
    theme: Theme = PLATE,
) -> plt.Figure:
    """Identity by state on a chromosome's q arm for four pairs, in a two-by-two grid.

    `table` is `align(...)` output; `pairs` are (person, person, relationship). Every panel's
    loupe looks at the sub-triangle where the first pair shares no allele most often.
    """
    cells = sierpinski_cells(LEVEL)
    centroids = cells.mean(axis=1)
    q_arm = table[table["position"] >= CENTROMERES[chromosome]]
    shared = {(a, b): ibs(q_arm[a], q_arm[b]) for a, b, _ in pairs}

    source = _source_block(cells, shared[pairs[0][:2]].eq(0).fillna(False).to_numpy())
    side = -1 if source[0] < 0.5 else 1

    extent = (-0.04, 2.32, -0.44, 2.06)
    fig, ax = plate(*_page(extent, 11.5), extent, theme, size=11.5)
    for k, (a, b, relation) in enumerate(pairs):
        offset = ((k % 2) * 1.24 + 0.02, (1 - k // 2) * 1.12 + 0.12)
        values = shared[(a, b)]
        colours = colours_for(list(values), IBS_PALETTE, len(cells), theme.missing)
        draw(ax, cells, colours, theme, offset=offset)

        none = np.flatnonzero(values.eq(0).fillna(False).to_numpy())
        marks = centroids[none] + offset
        ax.scatter(*marks.T, s=1.4, color=IBS_PALETTE[0], lw=0, zorder=3)
        lens = (offset[0] + 0.5 + side * 0.34, offset[1] + 0.66)
        loupe(ax, cells, colours, theme, tuple(source + offset), 0.02, lens, 0.14, offset=offset)

        centre = (offset[0] + 0.5, offset[1])
        caption(ax, *centre, f"{a} & {b}", theme, size=HEADING, dy=-12, va="top", ha="center")
        line = {"size": BODY, "dy": -(12 + HEADING + 8), "va": "top"}
        rel = caption(ax, *centre, f"{relation}  ·  ", theme, dim=True, ha="right", **line)
        number = f"{len(none):,}"
        count = caption(ax, *centre, number, theme, ha="left", color=IBS_PALETTE[0], **line)
        shift = (width(ax, rel) - width(ax, count)) / 2
        for text in (rel, count):
            text.xyann = (text.xyann[0] + shift, text.xyann[1])

    key = [[(IBS_PALETTE[2], "two"), (IBS_PALETTE[1], "one"), (IBS_PALETTE[0], "none")]]
    title = (kicker, f"Identity by state on {chromosome}q", subtitle)
    footer(ax, 0.02, 2.28, -0.12, key, title, theme, rows=1, lead="alleles shared")
    return fig
