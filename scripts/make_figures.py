"""Render the plates into figures/ from the Corpasome files in data/corpasome/."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from dna_fractal import align, read_23andme
from dna_fractal.plates import genome_plate, ibs_plate

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "corpasome"
FIGURES = ROOT / "figures"

ROLES = ["father", "mother", "daughter", "aunt"]
PAIRS = [
    ("father", "mother", "unrelated"),
    ("mother", "aunt", "sisters"),
    ("father", "daughter", "parent, child"),
    ("mother", "daughter", "parent, child"),
]


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    people = {role: read_23andme(DATA / f"{role}.zip") for role in ROLES}
    genome_plate(people["father"], "1", "Corpas family  ·  father", "plate i").savefig(
        FIGURES / "plate_1.png", dpi=180, facecolor="black"
    )
    ibs_plate(align(people, "1"), PAIRS, "1", "Corpas family", "plate ii").savefig(
        FIGURES / "plate_2.png", dpi=220, facecolor="black"
    )


if __name__ == "__main__":
    main()
