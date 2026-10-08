import numpy as np
import pytest

from dna_fractal.geometry import SQRT3_2, level_for, sierpinski_cells, subtriangle


def area(cells):
    (x0, y0), (x1, y1), (x2, y2) = cells[:, 0].T, cells[:, 1].T, cells[:, 2].T
    return np.abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)) / 2


@pytest.mark.parametrize("level", [0, 1, 4, 7])
def test_cell_count_and_area(level):
    cells = sierpinski_cells(level)
    assert cells.shape == (3**level, 3, 2)
    whole = SQRT3_2 / 2
    assert area(cells).sum() == pytest.approx(whole * 0.75**level)
    assert np.allclose(area(cells), area(cells)[0])


def test_visit_order_is_top_then_left_then_right():
    cells = sierpinski_cells(1)
    centroids = cells.mean(axis=1)
    assert centroids[0, 1] > centroids[1, 1]
    assert centroids[1, 0] < centroids[2, 0]
    assert centroids[1, 1] == pytest.approx(centroids[2, 1])


def test_first_cell_holds_the_apex_and_last_holds_the_right_corner():
    cells = sierpinski_cells(5)
    assert np.allclose(cells[0, 0], [0.5, SQRT3_2])
    assert np.allclose(cells[-1, 2], [1.0, 0.0])


def test_consecutive_cells_stay_close():
    centroids = sierpinski_cells(6).mean(axis=1)
    steps = np.linalg.norm(np.diff(centroids, axis=0), axis=1)
    assert steps.max() <= 0.5 + 1e-9
    assert np.median(steps) == pytest.approx(2**-6, rel=1e-6)


@pytest.mark.parametrize(("n", "level"), [(1, 0), (3, 1), (4, 2), (59_049, 10), (59_050, 11)])
def test_level_for(n, level):
    assert level_for(n) == level


def test_subtriangle_matches_subdivided_geometry():
    cells = sierpinski_cells(4)
    block = cells[subtriangle(4, "21")]
    # Bottom-right, then its bottom-left: a quarter-scale copy with its left corner at (0.5, 0).
    assert np.allclose(block, sierpinski_cells(2) / 4 + [0.5, 0.0])


def test_subtriangle_rejects_bad_paths():
    with pytest.raises(ValueError):
        subtriangle(2, "3")
    with pytest.raises(ValueError):
        subtriangle(2, "000")
