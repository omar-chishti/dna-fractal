"""Plate furniture in the manner of engraved plates: Oxford rule, loupes, keys, captions.

Text and key layout are measured in points from a data-space anchor, so spacing and swatch
sizes are identical on every plate whatever its data scale.
"""

import math
from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.transforms import ScaledTranslation

from .render import Theme, draw
from .typography import SMALL_CAPS_FAMILY, register_fonts

SERIF = "ETbb"

# Type scale, in points.
TITLE = 32.0
HEADING = 17.0
BODY = 13.5
NOTE = 11.0

SWATCH = 11.0
TRIANGLE = [(0.0, 0.433), (-0.5, -0.433), (0.5, -0.433), (0.0, 0.433)]
# Drop from a swatch's centre to the label baseline that centres small capitals on it.
SMALL_CAPS_DROP = 0.23 * BODY

KeyItem = tuple[str | None, str]


def plate(width: float, height: float, extent, theme: Theme, size: float = 14.0):
    """A figure framed by an Oxford rule, with one equal-aspect axes spanning `extent`.

    `extent` is (x0, x1, y0, y1) in data units; `width` and `height` set the aspect of the page.
    """
    register_fonts()
    fig = plt.figure(figsize=(size, size * height / width), facecolor=theme.ground)
    _oxford_rule(fig, theme)
    margin_x, margin_y = 0.05, 0.05 * width / height
    ax = fig.add_axes([margin_x, margin_y, 1 - 2 * margin_x, 1 - 2 * margin_y])
    ax.set_facecolor(theme.ground)
    x0, x1, y0, y1 = extent
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _oxford_rule(fig: plt.Figure, theme: Theme, inset: float = 18.0, gap: float = 4.0) -> None:
    """A heavy outer rule and a fine inner one, `inset` and `inset + gap` points from the edge."""
    frame = fig.add_axes([0, 0, 1, 1], zorder=-1)
    frame.axis("off")
    width, height = fig.get_size_inches() * 72
    style = {"fill": False, "edgecolor": theme.ink, "joinstyle": "miter"}
    for offset, lw in [(inset, 2.0), (inset + gap + 1.0, 0.6)]:
        x, y = offset / width, offset / height
        frame.add_patch(Rectangle((x, y), 1 - 2 * x, 1 - 2 * y, lw=lw, **style))


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
    dx: float = 0.0,
    dy: float = 0.0,
    **kwargs,
):
    """Text in ETbb at (x, y), shifted (dx, dy) points.

    Small capitals by default, or roman or italic; `dim` for secondary text.
    """
    kwargs.setdefault("color", theme.ink_dim if dim else theme.ink)
    return ax.annotate(
        text,
        (x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        family=SMALL_CAPS_FAMILY if small_caps and not italic else SERIF,
        style="italic" if italic else "normal",
        size=size,
        **kwargs,
    )


def _points(ax: plt.Axes, dx: float, dy: float):
    return ax.transData + ScaledTranslation(dx / 72, dy / 72, ax.figure.dpi_scale_trans)


def width(ax: plt.Axes, artist) -> float:
    """An artist's rendered width in points."""
    renderer = ax.figure.canvas.get_renderer()
    return artist.get_window_extent(renderer).width * 72 / ax.figure.dpi


def _points_per_unit(ax: plt.Axes) -> float:
    (x0, _), (x1, _) = ax.transData.transform([(0, 0), (1, 0)])
    return (x1 - x0) * 72 / ax.figure.dpi


def swatch(ax, x, y, colour: str | None, theme: Theme, dx=0.0, dy=0.0, size=SWATCH) -> None:
    """An equilateral triangle centred (dx, dy) points from (x, y); None draws an outline."""
    style = (
        {"markerfacecolor": "none", "markeredgecolor": theme.ink_dim, "markeredgewidth": 0.7}
        if colour is None
        else {"markerfacecolor": colour, "markeredgewidth": 0}
    )
    ax.plot([x], [y], marker=TRIANGLE, markersize=size, transform=_points(ax, dx, dy), **style)


def key(
    ax: plt.Axes,
    x: float,
    y: float,
    groups: Sequence[Sequence[KeyItem]],
    theme: Theme,
    rows: int = 2,
    lead: str | None = None,
) -> float:
    """A key whose top-left corner is (x, y), grouped by spacing alone. Returns its width.

    Items are (colour, label), filled row by row in up to `rows` rows; a None colour draws an
    outline swatch. `lead` is a dim label set before the first row.
    """
    row_height, label_gap, column_gap, group_gap = 24.0, 8.0, 20.0, 44.0
    left = 0.0
    if lead:
        text = caption(ax, x, y, lead, theme, size=NOTE, dim=True,
                       dy=-SWATCH / 2 - SMALL_CAPS_DROP, va="baseline")  # fmt: skip
        left = width(ax, text) + label_gap * 2
    for items in groups:
        columns = math.ceil(len(items) / rows)
        for c in range(columns):
            widest = 0.0
            for i in range(c, len(items), columns):
                colour, label = items[i]
                cy = -(i // columns) * row_height - SWATCH / 2
                swatch(ax, x, y, colour, theme, dx=left + SWATCH / 2, dy=cy)
                text = caption(
                    ax, x, y, label, theme,
                    dx=left + SWATCH + label_gap, dy=cy - SMALL_CAPS_DROP, va="baseline",
                )  # fmt: skip
                widest = max(widest, width(ax, text))
            left += SWATCH + label_gap + widest + column_gap
        left += group_gap - column_gap
    return left - group_gap


def title_block(ax, x, y, kicker: str, title: str, subtitle: str, theme: Theme) -> None:
    """Right-aligned kicker, italic title and subtitle hanging from the top-right corner (x, y)."""
    right = {"ha": "right", "va": "top"}
    caption(ax, x, y, kicker, theme, size=NOTE, dim=True, **right)
    caption(ax, x, y, title, theme, size=TITLE, italic=True, dy=-(NOTE + 6), **right)
    caption(ax, x, y, subtitle, theme, dy=-(NOTE + TITLE + 16), **right)


def footer(
    ax: plt.Axes,
    x0: float,
    x1: float,
    y: float,
    groups: Sequence[Sequence[KeyItem]],
    title: tuple[str, str, str],
    theme: Theme,
    rows: int = 2,
    lead: str | None = None,
) -> None:
    """A rule from x0 to x1 at height y; below it the key on the left, the title on the right."""
    ax.plot([x0, x1], [y, y], color=theme.ink_dim, lw=0.4)
    top = y - 22 / _points_per_unit(ax)
    title_block(ax, x1, top, *title, theme)
    key_top = top - (NOTE + 12) / _points_per_unit(ax)
    key(ax, x0, key_top, groups, theme, rows=rows, lead=lead)
