import unicodedata
import re
from pathlib import Path
from typing import Optional


def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    without_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return without_accents.lower().strip()


def sanitize_identifier(text: str) -> str:
    norm = normalize_text(text)
    norm = re.sub(r"^desafio[_\s-]*tecnico[_\s-]*ai[_\s-]*eng[_\s-]*", "", norm)
    clean = re.sub(r"[^a-z0-9_]+", "_", norm).strip("_")
    return clean or "table"


def find_file_by_pattern(directory: Path, pattern_keyword: str, extension: str) -> Optional[Path]:
    target = normalize_text(pattern_keyword)
    ext = extension.lower().strip(".")

    for file_path in directory.glob(f"*.{ext}"):
        if target in normalize_text(file_path.stem):
            return file_path
    return None