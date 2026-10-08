"""Plate furniture in the manner of engraved charts: neatline, loupes, captions."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

from .render import Theme, draw
from .typography import SMALL_CAPS_FAMILY, register_fonts

SERIF = "ETbb"

# Type scale, in points.
TITLE = 20.0
HEADING = 12.0
BODY = 9.5
NOTE = 8.0


def plate(width: float, height: float, extent, theme: Theme, size: float = 14.0):
    """A figure with a chart border and one equal-aspect axes spanning `extent`.

    `extent` is (x0, x1, y0, y1) in data units; `width` and `height` set the aspect of the page.
    """
    register_fonts()
    fig = plt.figure(figsize=(size, size * height / width), facecolor=theme.ground)
    _neatline(fig, theme)
    margin_x, margin_y = 0.04, 0.04 * width / height
    ax = fig.add_axes([margin_x, margin_y, 1 - 2 * margin_x, 1 - 2 * margin_y])
    ax.set_facecolor(theme.ground)
    x0, x1, y0, y1 = extent
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _neatline(fig: plt.Figure, theme: Theme, segments: int = 64) -> None:
    """Double rule with an alternating scale band between, as on a nautical chart's border."""
    frame = fig.add_axes([0, 0, 1, 1], zorder=-1)
    frame.set_xlim(0, 1)
    frame.set_ylim(0, 1)
    frame.axis("off")
    width, height = fig.get_size_inches()
    aspect = width / height
    mx, my = 0.014, 0.014 * aspect
    bx, by = 0.0035, 0.0035 * aspect
    for x, y, lw in [(mx, my, 0.9), (mx + bx, my + by, 0.4)]:
        frame.add_patch(
            Rectangle((x, y), 1 - 2 * x, 1 - 2 * y, fill=False, edgecolor=theme.ink, lw=lw)
        )
    across, down = segments, round(segments / aspect)
    step_x, step_y = (1 - 2 * mx) / across, (1 - 2 * my) / down
    style = {"color": theme.ink_dim, "lw": 0}
    for i in range(0, across, 2):
        for y in (my, 1 - my - by):
            frame.add_patch(Rectangle((mx + i * step_x, y), step_x, by, **style))
    for i in range(0, down, 2):
        for x in (mx, 1 - mx - bx):
            frame.add_patch(Rectangle((x, my + i * step_y), bx, step_y, **style))


def _outer_tangents(c1, r1, c2, r2):
    c1, c2 = np.asarray(c1, float), np.asarray(c2, float)
    d = c2 - c1
    base = np.arctan2(d[1], d[0])
    spread = np.arccos((r1 - r2) / np.hypot(*d))
    lines = []
    for sign in (1, -1):
        unit = np.array([np.cos(base + sign * spread), np.sin(base + sign * spread)])
        lines.append((c1 + r1 * unit, c2 + r2 * unit))
    return lines


def loupe(
    ax: plt.Axes,
    cells: np.ndarray,
    colours: Sequence[str | None],
    theme: Theme,
    source: tuple[float, float],
    source_radius: float,
    centre: tuple[float, float],
    radius: float,
    offset: tuple[float, float] = (0.0, 0.0),
) -> plt.Axes:
    """A circular magnified view of the cells around `source`, drawn at `centre`.

    A ring marks the source; outer tangent lines join it to the lens.
    """
    shifted = cells + np.asarray(offset)
    near = np.hypot(*(shifted.mean(axis=1) - source).T) < source_radius * 1.6
    inset = ax.inset_axes(
        [centre[0] - radius, centre[1] - radius, 2 * radius, 2 * radius], transform=ax.transData
    )
    inset.set_xlim(source[0] - source_radius, source[0] + source_radius)
    inset.set_ylim(source[1] - source_radius, source[1] + source_radius)
    inset.set_aspect("equal")
    inset.axis("off")
    lens = Circle((0.5, 0.5), 0.5, transform=inset.transAxes, facecolor=theme.ground, lw=0)
    inset.add_patch(lens)
    nearby = [colours[i] for i in np.flatnonzero(near)]
    for collection in draw(inset, shifted[near], nearby, theme):
        collection.set_clip_path(lens)
        collection.set_linewidth(0.3)

    ring = {"fill": False, "edgecolor": theme.ink, "zorder": 5}
    ax.add_patch(Circle(centre, radius, linewidth=0.9, **ring))
    ax.add_patch(Circle(centre, radius * 1.03, linewidth=0.35, **ring))
    ax.add_patch(Circle(source, source_radius, linewidth=0.6, **ring))
    for start, end in _outer_tangents(source, source_radius, centre, radius):
        ax.plot(*np.column_stack([start, end]), color=theme.ink, lw=0.4, alpha=0.7, zorder=4)
    return inset


def caption(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    theme: Theme,
    size: float = BODY,
    small_caps: bool = True,
    italic: bool = False,
    dim: bool = False,
    **kwargs,
):
    """Text in ETbb: small capitals by default, or roman or italic; `dim` for secondary text."""
    return ax.text(
        x,
        y,
        text,
        family=SMALL_CAPS_FAMILY if small_caps and not italic else SERIF,
        style="italic" if italic else "normal",
        size=size,
        color=theme.ink_dim if dim else theme.ink,
        **kwargs,
    )
