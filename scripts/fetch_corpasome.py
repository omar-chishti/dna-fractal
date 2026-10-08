"""Download the Corpas family's 23andMe genotypes (CC0) from figshare into data/corpasome/.

Manuel Corpas, "23andMe hg37", figshare, doi:10.6084/m9.figshare.4491215
"""

import hashlib
import urllib.request
from pathlib import Path

FILES = {
    "father": (7251299, "a6fcf9967b2109f2c1c192624ea97eaa"),
    "mother": (7251302, "7c1d32805bd4a453e8ef5221c835effd"),
    "daughter": (7251296, "93c0a1461f194d2808b97ee4a5599885"),
    "son": (7251305, "9be5a68bed18c198a68d54929c9e95a4"),
    "aunt": (7251293, "3a84c8f9ec7f97a09ab7d0c6e94420db"),
}

DATA = Path(__file__).resolve().parent.parent / "data" / "corpasome"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for role, (file_id, checksum) in FILES.items():
        path = DATA / f"{role}.zip"
        if path.exists() and md5(path) == checksum:
            print(f"{role}: present")
            continue
        urllib.request.urlretrieve(f"https://ndownloader.figshare.com/files/{file_id}", path)
        if md5(path) != checksum:
            path.unlink()
            raise RuntimeError(f"{role}: checksum mismatch, file removed")
        print(f"{role}: downloaded")


if __name__ == "__main__":
    main()
