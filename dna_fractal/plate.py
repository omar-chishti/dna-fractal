"""Plate furniture in the manner of engraved charts: neatline, graticule, loupes, captions."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

from .render import Theme, draw
from .typography import SMALL_CAPS_FAMILY, register_fonts

SERIF = "ETbb"


def plate(width: float, height: float, extent, theme: Theme, size: float = 14.0):
    """A figure with a chart border and one equal-aspect axes spanning `extent`.

    `extent` is (x0, x1, y0, y1) in data units; `width` and `height` set the aspect of the page.
    """
    register_fonts()
    fig = plt.figure(figsize=(size, size * height / width), facecolor=theme.ground)
    _neatline(fig, theme)
    ax = fig.add_axes([0.035, 0.035 * width / height, 0.93, 1 - 0.07 * width / height])
    ax.set_facecolor(theme.ground)
    x0, x1, y0, y1 = extent
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _neatline(fig: plt.Figure, theme: Theme, segments: int = 48) -> None:
    """Double rule with an alternating scale band between, as on a nautical chart's border."""
    frame = fig.add_axes([0, 0, 1, 1], zorder=-1)
    frame.set_xlim(0, 1)
    frame.set_ylim(0, 1)
    frame.axis("off")
    width, height = fig.get_size_inches()
    mx, my = 0.012, 0.012 * width / height
    band_x, band_y = 0.006, 0.006 * width / height
    for inset_x, inset_y, lw in [(mx, my, 1.1), (mx + band_x, my + band_y, 0.5)]:
        frame.add_patch(
            Rectangle(
                (inset_x, inset_y),
                1 - 2 * inset_x,
                1 - 2 * inset_y,
                fill=False,
                edgecolor=theme.ink,
                linewidth=lw,
            )
        )
    step_x = (1 - 2 * mx) / segments
    step_y = (1 - 2 * my) / round(segments * height / width)
    for i in range(0, segments, 2):
        for y in (my, 1 - my - band_y):
            frame.add_patch(Rectangle((mx + i * step_x, y), step_x, band_y, color=theme.ink, lw=0))
    for i in range(0, round(segments * height / width), 2):
        for x in (mx, 1 - mx - band_x):
            frame.add_patch(Rectangle((x, my + i * step_y), band_x, step_y, color=theme.ink, lw=0))


def graticule(ax: plt.Axes, theme: Theme, step: float = 1 / 32, major: int = 8) -> None:
    """Faint graph-paper ruling across the axes, every `major`-th line heavier."""
    for limits, rule in [(ax.get_xlim(), ax.axvline), (ax.get_ylim(), ax.axhline)]:
        for at in np.arange(np.ceil(limits[0] / step) * step, limits[1], step):
            alpha = 0.10 if round(at / step) % major == 0 else 0.04
            rule(at, color=theme.ink, alpha=alpha, lw=0.4, zorder=0)


def _outer_tangents(c1, r1, c2, r2):
    c1, c2 = np.asarray(c1, float), np.asarray(c2, float)
    d = c2 - c1
    distance = np.hypot(*d)
    base = np.arctan2(d[1], d[0])
    spread = np.arccos((r1 - r2) / distance)
    lines = []
    for sign in (1, -1):
        angle = base + sign * spread
        unit = np.array([np.cos(angle), np.sin(angle)])
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
    label: str | None = None,
) -> plt.Axes:
    """A circular magnified view of the cells around `source`, drawn at `centre`.

    A ring marks the source; outer tangent lines join it to the lens.
    """
    shifted = cells + np.asarray(offset)
    centroids = shifted.mean(axis=1)
    near = np.hypot(*(centroids - source).T) < source_radius * 1.6
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
    ax.add_patch(Circle(centre, radius, linewidth=1.1, **ring))
    ax.add_patch(Circle(centre, radius * 1.035, linewidth=0.4, **ring))
    ax.add_patch(Circle(source, source_radius, linewidth=0.7, **ring))
    for start, end in _outer_tangents(source, source_radius, centre, radius):
        ax.plot(*np.column_stack([start, end]), color=theme.ink, lw=0.5, alpha=0.8, zorder=4)
    if label:
        caption(ax, centre[0], centre[1] - radius * 1.18, label, theme, size=8.5, ha="center")
    return inset


def caption(ax, x, y, text, theme: Theme, size=10.0, small_caps=True, italic=False, **kw):
    """Text in ETbb: small capitals by default, or roman or italic."""
    family = SMALL_CAPS_FAMILY if small_caps and not italic else SERIF
    return ax.text(
        x,
        y,
        text,
        family=family,
        style="italic" if italic else "normal",
        size=size,
        color=theme.ink,
        **kw,
    )
