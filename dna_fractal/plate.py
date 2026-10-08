"""Plate furniture in the manner of engraved charts: neatline, loupes, keys, captions.

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
TITLE = 22.0
HEADING = 13.0
BODY = 10.5
NOTE = 8.5

SWATCH = 9.0
TRIANGLE = [(0.0, 0.433), (-0.5, -0.433), (0.5, -0.433), (0.0, 0.433)]
# Drop from a swatch's centre to the label baseline that centres small capitals on it.
SMALL_CAPS_DROP = 0.23 * BODY

KeyItem = tuple[str | None, str]
KeyGroup = tuple[str, Sequence[KeyItem]]


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
    dx: float = 0.0,
    dy: float = 0.0,
    **kwargs,
):
    """Text in ETbb at (x, y), shifted (dx, dy) points.

    Small capitals by default, or roman or italic; `dim` for secondary text.
    """
    return ax.annotate(
        text,
        (x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        family=SMALL_CAPS_FAMILY if small_caps and not italic else SERIF,
        style="italic" if italic else "normal",
        size=size,
        color=theme.ink_dim if dim else theme.ink,
        **kwargs,
    )


def _points(ax: plt.Axes, dx: float, dy: float):
    return ax.transData + ScaledTranslation(dx / 72, dy / 72, ax.figure.dpi_scale_trans)


def _width(ax: plt.Axes, artist) -> float:
    renderer = ax.figure.canvas.get_renderer()
    return artist.get_window_extent(renderer).width * 72 / ax.figure.dpi


def swatch(ax, x, y, colour: str | None, theme: Theme, dx=0.0, dy=0.0, size=SWATCH) -> None:
    """An equilateral triangle centred (dx, dy) points from (x, y); None draws an outline."""
    style = (
        {"markerfacecolor": "none", "markeredgecolor": theme.ink_dim, "markeredgewidth": 0.6}
        if colour is None
        else {"markerfacecolor": colour, "markeredgewidth": 0}
    )
    ax.plot([x], [y], marker=TRIANGLE, markersize=size, transform=_points(ax, dx, dy), **style)


def key(
    ax: plt.Axes,
    x: float,
    y: float,
    groups: Sequence[KeyGroup],
    theme: Theme,
    rows: int = 2,
) -> float:
    """A grouped key whose top-left corner is (x, y). Returns its width in points.

    Each group has a dim small-caps heading over a hairline, then its items filled row by row
    in up to `rows` rows. Items are (colour, label); a None colour draws an outline swatch.
    """
    row_height, label_gap, column_gap, group_gap = 17.0, 6.0, 14.0, 30.0
    top_of_items = -(NOTE + 13.0)
    left = 0.0
    for heading, items in groups:
        head = caption(ax, x, y, heading, theme, size=NOTE, dim=True, dx=left, va="top")
        columns = math.ceil(len(items) / rows)
        column_left = left
        for c in range(columns):
            widest = 0.0
            for i in range(c, len(items), columns):
                colour, label = items[i]
                cy = top_of_items - (i // columns) * row_height - SWATCH / 2
                swatch(ax, x, y, colour, theme, dx=column_left + SWATCH / 2, dy=cy)
                label_x = column_left + SWATCH + label_gap
                text = caption(
                    ax, x, y, label, theme, dx=label_x, dy=cy - SMALL_CAPS_DROP, va="baseline"
                )
                widest = max(widest, _width(ax, text))
            column_left += SWATCH + label_gap + widest + column_gap
        group_width = max(column_left - column_gap - left, _width(ax, head))
        hairline(ax, x, y, group_width, theme, dx=left, dy=-(NOTE + 5.0))
        left += group_width + group_gap
    return left - group_gap


def _points_per_unit(ax: plt.Axes) -> float:
    (x0, _), (x1, _) = ax.transData.transform([(0, 0), (1, 0)])
    return (x1 - x0) * 72 / ax.figure.dpi


def hairline(ax, x, y, length, theme: Theme, dx=0.0, dy=0.0, dim=True) -> None:
    """A horizontal rule `length` points long, starting (dx, dy) points from (x, y)."""
    span = length / _points_per_unit(ax)
    colour = theme.ink_dim if dim else theme.ink
    ax.plot([x, x + span], [y, y], color=colour, lw=0.4, transform=_points(ax, dx, dy))


def title_block(ax, x, y, title: str, subtitle: str, notes: Sequence[str], theme: Theme) -> None:
    """Right-aligned title, subtitle and dim note lines hanging from the top-right corner (x, y)."""
    right = {"ha": "right", "va": "top"}
    caption(ax, x, y, title, theme, size=TITLE, italic=True, **right)
    caption(ax, x, y, subtitle, theme, dy=-(TITLE + 8), **right)
    for i, note in enumerate(notes):
        dy = -(TITLE + BODY + 16 + i * (NOTE + 5))
        caption(ax, x, y, note, theme, size=NOTE, dim=True, dy=dy, **right)


def footer(
    ax: plt.Axes,
    x0: float,
    x1: float,
    y: float,
    groups: Sequence[KeyGroup],
    title: tuple[str, str, Sequence[str]],
    theme: Theme,
    rows: int = 2,
) -> None:
    """A rule from x0 to x1 at height y, the key below it on the left, the title on the right.

    The key's headings and the title share a top edge.
    """
    ax.plot([x0, x1], [y, y], color=theme.ink_dim, lw=0.4)
    top = y - 16 / _points_per_unit(ax)
    key(ax, x0, top, groups, theme, rows=rows)
    title_block(ax, x1, top, *title, theme)
