# core/dna.py
from __future__ import annotations

import re
from typing import Tuple

DNA_ALLOWED = set("ACGTN")


def normalize_dna(raw: str) -> str:
    if raw is None:
        return ""
    return re.sub(r"\s+", "", raw.upper())


def is_valid_dna(seq: str) -> bool:
    if not seq:
        return False
    return all(ch in DNA_ALLOWED for ch in seq)


def parse_fasta(text: str) -> str:
    if not text:
        return ""
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(">"):
            continue
        lines.append(ln)
    return "\n".join(lines)


def load_uploaded_fasta(file_bytes: bytes) -> str:
    try:
        raw = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        raw = ""
    return parse_fasta(raw)


def dna_length_hint(seq: str) -> Tuple[str, str]:
    n = len(seq)
    if n == 0:
        return ("warn", "No sequence yet.")
    if n < 30:
        return ("warn", "Sequence looks very short for a meaningful demo.")
    if n > 50000:
        return ("warn", "Sequence is very long; UI may become slow. Consider a shorter demo input.")
    return ("ok", f"Length: {n}")
