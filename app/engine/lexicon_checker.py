"""
Modul Pemeriksa Penggunaan Kata Berdasarkan PRPM Malaysia & Detektor Campuran Bahasa Inggris.
Aturan Kerja:
1. Kata Bahasa Melayu yang tidak baku / bahasa pasar / salah eja dibakukan mengikut PRPM DBP Malaysia.
2. Kata Majmuk Mantap (15 kata DBP) ditulis rapat, manakala kata majmuk biasa ditulis terpisah.
3. Kata Bahasa Inggris dikenali melalui Offline English Lexicon dan TIDAK DIGANTI (tetap dipertahankan).
"""

from __future__ import annotations
import re
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from app.data.seed_lexicon import DB_PATH, init_database
from app.engine.morphology import MorphologyAnalyzer


@dataclass
class LexiconIssue:
    original: str
    replacement: str
    category: str  # 'PRPM_BAKU', 'PRPM_MAJMUK', 'PRPM_TYPO'
    reason: str


class LexiconChecker:
    """Pemeriksa kata Bahasa Melayu PRPM dengan dukungan bypass Bahasa Inggris."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = init_database(db_path)
        self.prpm_words: Set[str] = set()
        self.ms_standardization: Dict[str, Tuple[str, str]] = {}
        self.compound_rules: Dict[str, Tuple[str, str]] = {}
        self.english_words: Set[str] = set()
        self.proper_nouns: Dict[str, str] = {}
        self.acronyms: Set[str] = set()
        self._load_from_db()

        # Tambahan bentuk berimbuhan tidak baku -> baku PRPM
        self._affixed_standardization: Dict[str, Tuple[str, str]] = {
            "dipahami": ("difahami", "Bentuk pasif baku PRPM daripada 'faham' ialah 'difahami'."),
            "memahami": ("memahami", ""),  # sudah baku
            "kepahaman": ("kefahaman", "Kata terbitan baku PRPM daripada 'faham' ialah 'kefahaman'."),
            "pemahaman": ("kefahaman", "Dalam PRPM, 'kefahaman' atau 'pemahaman' digunakan; 'kefahaman' diutamakan."),
            "dipikirkan": ("difikirkan", "Ejaan baku PRPM ialah 'difikirkan' (kata dasar 'fikir')."),
            "berpikir": ("berfikir", "Ejaan baku PRPM ialah 'berfikir' (kata dasar 'fikir')."),
            "terpikir": ("terfikir", "Ejaan baku PRPM ialah 'terfikir' (kata dasar 'fikir')."),
            "dibutuhkan": ("diperlukan", "Padanan baku PRPM ialah 'diperlukan'."),
            "membutuhkan": ("memerlukan", "Padanan baku PRPM ialah 'memerlukan'."),
            "diresmikan": ("dirasmikan", "Ejaan baku PRPM ialah 'dirasmikan' (kata dasar 'rasmi')."),
            "meresmikan": ("merasmikan", "Ejaan baku PRPM ialah 'merasmikan' (kata dasar 'rasmi')."),
            "membedakan": ("membezakan", "Ejaan baku PRPM ialah 'membezakan' (kata dasar 'beza')."),
            "dibedakan": ("dibezakan", "Ejaan baku PRPM ialah 'dibezakan' (kata dasar 'beza')."),
            "takkan": ("tidak akan", "Singkatan lisan 'takkan' dibakukan menjadi 'tidak akan'."),
        }

        self.morphology = MorphologyAnalyzer(
            prpm_roots=self.prpm_words,
            english_roots=self.english_words,
        )

        # Indeks kata PRPM berdasarkan huruf pertama dan panjang untuk koreksi typo cepat
        self._prpm_by_first_char: Dict[str, List[str]] = {}
        for w in self.prpm_words:
            if len(w) >= 5:
                first_ch = w[0]
                self._prpm_by_first_char.setdefault(first_ch, []).append(w)

    def _load_from_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT word FROM prpm_words")
        self.prpm_words = {row[0].lower() for row in cur.fetchall()}

        cur.execute("SELECT non_standard, standard_word, reason FROM ms_standardization")
        self.ms_standardization = {
            row[0].lower(): (row[1], row[2]) for row in cur.fetchall()
        }

        cur.execute("SELECT wrong_phrase, correct_phrase, reason FROM compound_rules")
        self.compound_rules = {
            row[0].lower(): (row[1], row[2]) for row in cur.fetchall()
        }

        cur.execute("SELECT word FROM english_words")
        self.english_words = {row[0].lower() for row in cur.fetchall()}

        cur.execute("SELECT lower_form, proper_form FROM proper_nouns")
        self.proper_nouns = {row[0].lower(): row[1] for row in cur.fetchall()}

        cur.execute("SELECT acronym FROM acronyms")
        self.acronyms = {row[0].upper() for row in cur.fetchall()}

        conn.close()

    def check_and_standardize(
        self, text: str
    ) -> Tuple[str, List[LexiconIssue], List[str]]:
        """
        Memeriksa penggunaan kata berdasarkan PRPM Malaysia dan mempertahankan kata Bahasa Inggris.
        Mengembalikan:
        - Teks yang telah dibakukan kata Melayu-nya
        - Daftar LexiconIssue (koreksi kata PRPM)
        - Daftar kata Bahasa Inggris yang terdeteksi dan dipertahankan
        """
        issues: List[LexiconIssue] = []
        english_kept: List[str] = []

        # Tahap 1: Pemeriksaan Frasa / Kata Majmuk Mantap DBP (contoh: 'kerja sama' -> 'kerjasama')
        extra_phrases = {
            "macam mana": (
                "bagaimana",
                "Frasa lisan 'macam mana' dibakukan menjadi 'bagaimana' mengikut PRPM.",
            ),
            "rumah sakit": (
                "hospital",
                "Padanan baku PRPM Malaysia bagi 'rumah sakit' ialah 'hospital'.",
            ),
            "tidak ada": (
                "tiada",
                "Frasa 'tidak ada' boleh diringkaskan secara baku menjadi 'tiada' mengikut PRPM.",
            ),
        }
        all_phrases = {**self.compound_rules, **extra_phrases}

        for wrong_phrase, (correct_phrase, reason) in all_phrases.items():
            pattern = re.compile(rf"\b{re.escape(wrong_phrase)}\b", re.IGNORECASE)

            def _replace_phrase(match: re.Match) -> str:
                orig = match.group(0)
                repl = correct_phrase
                if orig[0].isupper():
                    repl = repl[0].upper() + repl[1:]
                issues.append(
                    LexiconIssue(
                        original=orig,
                        replacement=repl,
                        category="PRPM_MAJMUK",
                        reason=reason,
                    )
                )
                return repl

            text = pattern.sub(_replace_phrase, text)

        # Tahap 2: Pemeriksaan Token demi Token
        token_pattern = re.compile(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b")
        result_parts: List[str] = []
        last_idx = 0

        for match in token_pattern.finditer(text):
            start, end = match.span()
            orig_word = match.group(0)
            lower_word = orig_word.lower()

            result_parts.append(text[last_idx:start])
            replacement = orig_word

            # 2.1 Cek apakah kata berada di kamus pembakuan langsung (ms_standardization)
            if lower_word in self.ms_standardization:
                std_word, reason = self.ms_standardization[lower_word]
                replacement = self._preserve_initial_case(orig_word, std_word)
                issues.append(
                    LexiconIssue(
                        original=orig_word,
                        replacement=replacement,
                        category="PRPM_BAKU",
                        reason=reason,
                    )
                )
            # 2.2 Cek apakah kata berada di kamus berimbuhan tidak baku (_affixed_standardization)
            elif lower_word in self._affixed_standardization:
                std_word, reason = self._affixed_standardization[lower_word]
                if reason:
                    replacement = self._preserve_initial_case(orig_word, std_word)
                    issues.append(
                        LexiconIssue(
                            original=orig_word,
                            replacement=replacement,
                            category="PRPM_BAKU",
                            reason=reason,
                        )
                    )
            # 2.3 Cek apakah kata tidak baku ditempeli partikel/klitik (-nya, -lah, -kah)
            elif self._check_clitic_standardization(lower_word) is not None:
                std_word, reason = self._check_clitic_standardization(lower_word)  # type: ignore
                replacement = self._preserve_initial_case(orig_word, std_word)
                issues.append(
                    LexiconIssue(
                        original=orig_word,
                        replacement=replacement,
                        category="PRPM_BAKU",
                        reason=reason,
                    )
                )
            # 2.4 Cek apakah sudah merupakan kata baku Melayu PRPM, Kata Nama Khas, atau Akronim
            elif (
                self.morphology.is_valid_malay_word(lower_word)
                or lower_word in self.proper_nouns
                or orig_word.upper() in self.acronyms
            ):
                replacement = orig_word
            # 2.5 Cek apakah kata merupakan kata Bahasa Inggris (TIDAK DIGANTI)
            elif self.morphology.is_valid_english_word(lower_word):
                replacement = orig_word
                if orig_word not in english_kept:
                    english_kept.append(orig_word)
            # 2.6 Cek apakah merupakan salah ketik (typo) dari kata baku PRPM Malaysia
            else:
                typo_fix = self._find_prpm_typo_correction(lower_word)
                if typo_fix is not None:
                    replacement = self._preserve_initial_case(orig_word, typo_fix)
                    issues.append(
                        LexiconIssue(
                            original=orig_word,
                            replacement=replacement,
                            category="PRPM_TYPO",
                            reason=f" Pembetulan ejaan kata mengikut PRPM Malaysia: '{orig_word}' -> '{replacement}'.",
                        )
                    )

            result_parts.append(replacement)
            last_idx = end

        result_parts.append(text[last_idx:])
        return "".join(result_parts), issues, english_kept

    def _check_clitic_standardization(self, lower_word: str) -> Optional[Tuple[str, str]]:
        """Memeriksa kata tidak baku yang diikuti akhiran -nya, -lah, atau -kah (misal: 'jawabannya' -> 'jawapannya')."""
        for suffix in ("nya", "lah", "kah"):
            if lower_word.endswith(suffix) and len(lower_word) > len(suffix) + 2:
                stem = lower_word[: -len(suffix)]
                if stem in self.ms_standardization:
                    std_stem, base_reason = self.ms_standardization[stem]
                    if " " not in std_stem:
                        new_word = f"{std_stem}{suffix}"
                        return (
                            new_word,
                            f"{base_reason} ('{lower_word}' -> '{new_word}')",
                        )
        return None

    def _find_prpm_typo_correction(self, lower_word: str) -> Optional[str]:
        """
        Mencari koreksi salah ketik (Damerau-Levenshtein distance == 1)
        terhadap kamus PRPM untuk kata dengan panjang >= 5 huruf.
        """
        if len(lower_word) < 5:
            return None

        candidates = self._prpm_by_first_char.get(lower_word[0], [])
        best_match: Optional[str] = None

        for cand in candidates:
            if abs(len(cand) - len(lower_word)) > 1:
                continue
            if self._damerau_levenshtein_distance_1(lower_word, cand):
                best_match = cand
                break

        return best_match

    @staticmethod
    def _damerau_levenshtein_distance_1(s1: str, s2: str) -> bool:
        """Mengembalikan True jika jarak edit Damerau-Levenshtein antara s1 dan s2 tepat 1."""
        if s1 == s2:
            return False
        len1, len2 = len(s1), len(s2)
        if abs(len1 - len2) > 1:
            return False

        # Panjang sama: substitusi 1 huruf atau transposisi 2 huruf bersebelahan
        if len1 == len2:
            diffs = [i for i in range(len1) if s1[i] != s2[i]]
            if len(diffs) == 1:
                return True
            if len(diffs) == 2 and diffs[1] == diffs[0] + 1:
                i = diffs[0]
                return s1[i] == s2[i + 1] and s1[i + 1] == s2[i]
            return False

        # Perbedaan panjang 1: penyisipan atau penghapusan 1 huruf
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1

        i = j = diffs = 0
        while i < len1 and j < len2:
            if s1[i] == s2[j]:
                i += 1
                j += 1
            else:
                diffs += 1
                if diffs > 1:
                    return False
                j += 1
        return True

    @staticmethod
    def _preserve_initial_case(orig: str, replacement: str) -> str:
        if not orig or not replacement:
            return replacement
        if orig[0].isupper() and not orig.isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    # ========================================================================
    # MANAJEMEN KAMUS LOKAL (TAMBAH KATA BARU SECARA OFFLINE)
    # ========================================================================
    def add_prpm_word(self, word: str) -> None:
        w = word.strip().lower()
        if not w:
            return
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR IGNORE INTO prpm_words (word) VALUES (?)", (w,))
        conn.commit()
        conn.close()
        self.prpm_words.add(w)

    def add_standardization_rule(self, non_standard: str, standard_word: str, reason: str) -> None:
        ns = non_standard.strip().lower()
        sw = standard_word.strip().lower()
        if not ns or not sw:
            return
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO ms_standardization (non_standard, standard_word, reason) VALUES (?, ?, ?)",
            (ns, sw, reason),
        )
        conn.execute("INSERT OR IGNORE INTO prpm_words (word) VALUES (?)", (sw,))
        conn.commit()
        conn.close()
        self.ms_standardization[ns] = (sw, reason)
        self.prpm_words.add(sw)

    def add_english_word(self, word: str) -> None:
        w = word.strip().lower()
        if not w:
            return
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR IGNORE INTO english_words (word) VALUES (?)", (w,))
        conn.commit()
        conn.close()
        self.english_words.add(w)
