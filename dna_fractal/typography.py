"""ETbb, a Bembo revival (MIT licence), set up for matplotlib with true small capitals.

matplotlib cannot switch on OpenType features, so `small_caps_font` writes a derived copy of the
font in which lowercase letters map straight to their small-capital glyphs, digits to old-style
figures, and every advance width carries the letterspacing small capitals are set with.
"""

from pathlib import Path

import matplotlib
from fontTools.ttLib import TTFont
from matplotlib import font_manager

FONTS = Path(__file__).parent / "fonts"
REGULAR = FONTS / "ETbb-Regular.otf"
ITALIC = FONTS / "ETbb-Italic.otf"

SMALL_CAPS_FAMILY = "ETbb SC"
TRACKING = 0.08


def _single_substitutions(font: TTFont, tag: str) -> dict[str, str]:
    gsub = font["GSUB"].table
    mapping: dict[str, str] = {}
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag != tag:
            continue
        for index in record.Feature.LookupListIndex:
            lookup = gsub.LookupList.Lookup[index]
            for subtable in lookup.SubTable:
                if lookup.LookupType == 7:
                    subtable = subtable.ExtSubTable
                mapping.update(getattr(subtable, "mapping", {}))
    return mapping


def small_caps_font(destination: Path, tracking: float = TRACKING) -> Path:
    """Write the small-capitals variant of ETbb Regular and return its path."""
    font = TTFont(REGULAR)
    swaps = _single_substitutions(font, "smcp") | _single_substitutions(font, "onum")
    for table in font["cmap"].tables:
        table.cmap = {code: swaps.get(glyph, glyph) for code, glyph in table.cmap.items()}

    extra = round(tracking * font["head"].unitsPerEm)
    metrics = font["hmtx"].metrics
    for glyph, (advance, lsb) in metrics.items():
        if advance:
            metrics[glyph] = (advance + extra, lsb)

    names = {1: SMALL_CAPS_FAMILY, 4: SMALL_CAPS_FAMILY, 6: "ETbbSC-Regular", 16: SMALL_CAPS_FAMILY}
    for record in font["name"].names:
        if record.nameID in names:
            record.string = names[record.nameID]

    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(destination)
    return destination


def register_fonts() -> None:
    """Make ETbb, ETbb Italic and ETbb SC available to matplotlib by family name."""
    derived = Path(matplotlib.get_cachedir()) / "dna-fractal" / f"ETbbSC-{TRACKING:.3f}.otf"
    if not derived.exists():
        small_caps_font(derived)
    for path in (REGULAR, ITALIC, derived):
        font_manager.fontManager.addfont(str(path))
