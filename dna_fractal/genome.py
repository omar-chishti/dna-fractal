"""Reading 23andMe raw data and comparing genotypes between people."""

from collections import Counter
from pathlib import Path

import pandas as pd

CHROMOSOMES = [*map(str, range(1, 23)), "X", "Y", "MT"]

# End of the p11 band on GRCh37, from UCSC hg19 cytoBand.txt (the boundary between the arms).
CENTROMERES = {
    "1": 125_000_000, "2": 93_300_000, "3": 91_000_000, "4": 50_400_000,
    "5": 48_400_000, "6": 61_000_000, "7": 59_900_000, "8": 45_600_000,
    "9": 49_000_000, "10": 40_200_000, "11": 53_700_000, "12": 35_800_000,
    "13": 17_900_000, "14": 17_600_000, "15": 19_000_000, "16": 36_600_000,
    "17": 24_000_000, "18": 17_200_000, "19": 26_500_000, "20": 27_500_000,
    "21": 13_200_000, "22": 14_700_000, "X": 60_600_000, "Y": 12_500_000,
}  # fmt: skip

NO_CALL = "--"


def read_23andme(path: str | Path) -> pd.DataFrame:
    """Read a 23andMe raw data file, plain or zipped, in file order.

    Columns: rsid, chromosome (ordered categorical), position, genotype. The column header is
    commented out in 23andMe's exports but not always in edited copies, so either form reads.
    """
    df = pd.read_csv(
        path,
        sep="\t",
        comment="#",
        names=["rsid", "chromosome", "position", "genotype"],
        dtype=str,
    )
    df = df[df["rsid"] != "rsid"].reset_index(drop=True)
    df["position"] = df["position"].astype("int64")
    df["chromosome"] = pd.Categorical(df["chromosome"], categories=CHROMOSOMES, ordered=True)
    return df


def chromosome(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """One chromosome's SNPs, sorted by position."""
    snps = df[df["chromosome"] == name]
    return snps.sort_values("position", kind="stable").reset_index(drop=True)


def arms(df: pd.DataFrame, name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A chromosome's SNPs split at the centromere into the p arm and the q arm."""
    snps = chromosome(df, name)
    on_p = snps["position"] < CENTROMERES[name]
    return snps[on_p].reset_index(drop=True), snps[~on_p].reset_index(drop=True)


def align(genomes: dict[str, pd.DataFrame], name: str) -> pd.DataFrame:
    """Genotypes of several people on one chromosome, one column each, indexed by rsid.

    Rows are the SNPs every person was typed at, sorted by position.
    """
    per_person = {person: chromosome(df, name).set_index("rsid") for person, df in genomes.items()}
    table = pd.concat(
        [snps["genotype"].rename(person) for person, snps in per_person.items()],
        axis=1,
        join="inner",
    )
    first = next(iter(per_person.values()))
    table.insert(0, "position", first["position"].reindex(table.index))
    return table.sort_values("position", kind="stable")


def _shared_alleles(a: str, b: str) -> int | None:
    if NO_CALL in (a, b) or len(a) != 2 or len(b) != 2:
        return None
    return sum((Counter(a) & Counter(b)).values())


def ibs(a: pd.Series, b: pd.Series) -> pd.Series:
    """Identity by state: how many alleles (0, 1 or 2) two people share at each SNP.

    Missing where either call is a no-call or not diploid.
    """
    pairs = pd.Series(list(zip(a, b, strict=True)), index=a.index)
    lookup = {pair: _shared_alleles(*pair) for pair in set(pairs)}
    return pairs.map(lookup).astype("Int8")


def _mendelian_error(child: str, father: str, mother: str) -> bool | None:
    if NO_CALL in (child, father, mother) or not len(child) == len(father) == len(mother) == 2:
        return None
    return not any(sorted(f + m) == sorted(child) for f in father for m in mother)


def mendelian_errors(child: pd.Series, father: pd.Series, mother: pd.Series) -> pd.Series:
    """True where the child's genotype cannot be formed from one allele of each parent."""
    trios = pd.Series(list(zip(child, father, mother, strict=True)), index=child.index)
    lookup = {trio: _mendelian_error(*trio) for trio in set(trios)}
    return trios.map(lookup).astype("boolean")
