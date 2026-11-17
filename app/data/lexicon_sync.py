"""
Modul Impor & Sinkronisasi Leksikon Kamus Lokal (SQLite Full Offline).
Mendukung:
1. Impor berkas kamus lokal berformat Hunspell (.dic) maupun teks biasa (.txt)
   ke dalam tabel prpm_words atau english_words.
2. Sinkronisasi opsional saat online dari sumber open-source standar DBP/Malaysia
   (syafiqhadzir/hunspell-ms) dan kamus Inggris LibreOffice (en_GB.dic).
"""

from __future__ import annotations
import os
import re
import sqlite3
import tempfile
import urllib.request
from typing import Dict, Iterable, List, Set, Tuple

from app.data.seed_lexicon import DB_PATH, MS_STANDARDIZATION, PRPM_WORDS, init_database

HUNSPELL_MS_URL = "https://raw.githubusercontent.com/syafiqhadzir/hunspell-ms/master/ms_MY.dic"
HUNSPELL_EN_GB_URL = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_GB.dic"

# Kata tugas pendek Bahasa Inggris yang harus tetap dikenali sebagai Bahasa Inggris
# meskipun muncul sebagai singkatan pada berkas .dic eksternal.
ENGLISH_FUNCTION_GUARD: Set[str] = {
    "am", "an", "are", "as", "be", "do", "go", "had", "has", "he", "his",
    "in", "is", "it", "me", "my", "no", "not", "of", "on", "or", "so",
    "to", "up", "us", "we", "add", "at", "by", "ok",
}

_WORD_RE = re.compile(r"^[a-z]+(?:-[a-z]+)*$")
_PROPER_WORD_RE = re.compile(r"^[A-Z][a-z]{2,}(?:-[A-Z][a-z]+)*$")


def parse_wordlist_lines(lines: Iterable[str]) -> Set[str]:
    """Memilah kata dasar berhuruf kecil dari baris berkas Hunspell (.dic) atau daftar kata (.txt)."""
    words: Set[str] = set()
    for idx, raw in enumerate(lines):
        line = raw.lstrip("\ufeff").strip()
        if not line or line.startswith("#"):
            continue
        if idx == 0 and line.isdigit():
            continue
        base = line.split("/", 1)[0].strip()
        if len(base) < 2:
            continue
        lower = base.lower()
        if base != lower:
            continue
        if _WORD_RE.fullmatch(lower):
            words.add(lower)
    return words


def parse_proper_nouns_lines(lines: Iterable[str]) -> Dict[str, str]:
    """Memilah Kata Nama Khas (Title Case >= 3 huruf) dari berkas Hunspell (.dic)."""
    propers: Dict[str, str] = {}
    for idx, raw in enumerate(lines):
        line = raw.lstrip("\ufeff").strip()
        if not line or line.startswith("#"):
            continue
        if idx == 0 and line.isdigit():
            continue
        base = line.split("/", 1)[0].strip()
        if _PROPER_WORD_RE.fullmatch(base):
            propers[base.lower()] = base
    return propers


def import_wordlist_file(
    db_path: str,
    file_path: str,
    target: str = "prpm",
    source: str = "user",
) -> Tuple[int, int]:
    """
    Mengimpor berkas .dic atau .txt ke database SQLite offline.
    Mengembalikan (jumlah_kata_terbaca, jumlah_kata_baru_ditambahkan).
    """
    if target not in ("prpm", "english"):
        raise ValueError("Target impor harus 'prpm' atau 'english'.")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Berkas kamus '{file_path}' tidak ditemukan.")

    init_database(db_path)

    with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
        parsed = parse_wordlist_lines(f)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    existing_non_std = {
        row[0].lower()
        for row in cur.execute("SELECT non_standard FROM ms_standardization").fetchall()
    }
    non_std_blocklist = existing_non_std | set(k.lower() for k in MS_STANDARDIZATION.keys()) | {"pasal"}

    if target == "prpm":
        blocked = non_std_blocklist | (ENGLISH_FUNCTION_GUARD - {w.lower() for w in PRPM_WORDS})
        filtered = sorted(w for w in parsed if w not in blocked)
        before = cur.execute("SELECT COUNT(*) FROM prpm_words").fetchone()[0]
        cur.executemany(
            "INSERT OR IGNORE INTO prpm_words (word, source) VALUES (?, ?)",
            [(w, source) for w in filtered],
        )
        conn.commit()
        after = cur.execute("SELECT COUNT(*) FROM prpm_words").fetchone()[0]
    else:
        filtered = sorted(w for w in parsed if w not in non_std_blocklist)
        before = cur.execute("SELECT COUNT(*) FROM english_words").fetchone()[0]
        cur.executemany(
            "INSERT OR IGNORE INTO english_words (word, source) VALUES (?, ?)",
            [(w, source) for w in filtered],
        )
        conn.commit()
        after = cur.execute("SELECT COUNT(*) FROM english_words").fetchone()[0]

    conn.close()
    return len(filtered), max(0, after - before)


def import_proper_nouns_from_file(
    db_path: str,
    file_path: str,
    source: str = "sync",
) -> Tuple[int, int]:
    """Mengimpor Kata Nama Khas (Title Case) yang tidak bertindih dengan kata umum ke tabel proper_nouns."""
    init_database(db_path)
    with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
        parsed = parse_proper_nouns_lines(f)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    common_words = (
        {r[0].lower() for r in cur.execute("SELECT word FROM prpm_words").fetchall()}
        | {r[0].lower() for r in cur.execute("SELECT word FROM english_words").fetchall()}
        | {r[0].lower() for r in cur.execute("SELECT non_standard FROM ms_standardization").fetchall()}
    )

    filtered = [
        (low, prop, source)
        for low, prop in sorted(parsed.items())
        if low not in common_words
    ]
    before = cur.execute("SELECT COUNT(*) FROM proper_nouns").fetchone()[0]
    cur.executemany(
        "INSERT OR IGNORE INTO proper_nouns (lower_form, proper_form, source) VALUES (?, ?, ?)",
        filtered,
    )
    conn.commit()
    after = cur.execute("SELECT COUNT(*) FROM proper_nouns").fetchone()[0]
    conn.close()
    return len(filtered), max(0, after - before)


def sync_online_lexicons(
    db_path: str = DB_PATH,
    include_english: bool = True,
    timeout: int = 20,
) -> Dict[str, Tuple[int, int]]:
    """
    Mengunduh kamus open-source Melayu (hunspell-ms) & Inggris (LibreOffice en_GB.dic)
    lalu memasukkannya secara permanen ke SQLite offline.
    """
    init_database(db_path)
    summary: Dict[str, Tuple[int, int]] = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        ms_path = os.path.join(tmpdir, "ms_MY.dic")
        with urllib.request.urlopen(HUNSPELL_MS_URL, timeout=timeout) as resp:
            with open(ms_path, "wb") as out_f:
                out_f.write(resp.read())
        summary["prpm_words"] = import_wordlist_file(
            db_path, ms_path, target="prpm", source="sync"
        )

        en_path = os.path.join(tmpdir, "en_GB.dic")
        if include_english:
            with urllib.request.urlopen(HUNSPELL_EN_GB_URL, timeout=timeout) as resp:
                with open(en_path, "wb") as out_f:
                    out_f.write(resp.read())
            summary["english_words"] = import_wordlist_file(
                db_path, en_path, target="english", source="sync"
            )

        # Impor Kata Nama Khas murni (Title Case yang tidak bertindih dengan kata umum)
        p_ms_parsed, p_ms_added = import_proper_nouns_from_file(db_path, ms_path, source="sync")
        p_en_parsed, p_en_added = (0, 0)
        if include_english:
            p_en_parsed, p_en_added = import_proper_nouns_from_file(db_path, en_path, source="sync")
        summary["proper_nouns"] = (p_ms_parsed + p_en_parsed, p_ms_added + p_en_added)

    return summary
