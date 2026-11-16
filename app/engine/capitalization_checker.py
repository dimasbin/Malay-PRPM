"""
Modul Pemeriksa Huruf Kapital dan Non-Kapital (Case Normalization) Bahasa Melayu PRPM.
Menangani:
1. Huruf pertama pada awal kalimat dan selepas tanda noktah ('.'), tanda tanya ('?'), atau tanda seru ('!') wajib kapital.
2. Kata Nama Khas (hari, bulan, negara, negeri, bandar seperti 'Isnin', 'Kuala Lumpur', 'Malaysia') wajib diawali huruf kapital.
3. Akronim rasmi ('PRPM', 'DBP', 'UiTM', 'KWSP', dll.) ditulis dengan huruf kapital yang tepat.
4. Kata biasa (Melayu maupun Inggris) di tengah kalimat yang menggunakan huruf kapital secara salah diubah menjadi huruf kecil (non-kapital).
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


@dataclass
class CapitalizationIssue:
    original: str
    replacement: str
    reason: str


class CapitalizationChecker:
    """Pemeriksa penggunaan huruf kapital dan non-kapital."""

    # Akronim yang wajib selalu kapital walaupun diketik huruf kecil
    UNAMBIGUOUS_ACRONYMS: Dict[str, str] = {
        "prpm": "PRPM",
        "dbp": "DBP",
        "myr": "MYR",
        "uitm": "UiTM",
        "ukm": "UKM",
        "upm": "UPM",
        "usm": "USM",
        "utm": "UTM",
        "uiam": "UIAM",
        "unimas": "UNIMAS",
        "jpn": "JPN",
        "kpm": "KPM",
        "kkm": "KKM",
        "pdrm": "PDRM",
        "sprm": "SPRM",
        "kwsp": "KWSP",
        "perkeso": "PERKESO",
        "lhdn": "LHDN",
        "felda": "FELDA",
        "petronas": "PETRONAS",
    }

    def __init__(self, proper_nouns: Dict[str, str], acronyms: Set[str]) -> None:
        self.proper_nouns = proper_nouns
        self.acronyms = {a.upper() for a in acronyms}
        self._multi_word_propers = {
            k: v for k, v in self.proper_nouns.items() if " " in k
        }
        self._single_word_propers = {
            k: v for k, v in self.proper_nouns.items() if " " not in k
        }

    def check_and_fix(self, text: str) -> Tuple[str, List[CapitalizationIssue]]:
        """Memeriksa dan memperbaiki huruf kapital serta non-kapital pada kalimat."""
        if not text or not text.strip():
            return text, []

        issues: List[CapitalizationIssue] = []
        working = text

        # 1. Tangani Kata Nama Khas berbilang kata terlebih dahulu (contoh: 'kuala lumpur' -> 'Kuala Lumpur')
        # Gunakan placeholder sementara atau penanda rentang agar tidak diturunkan kembali pada tahap token
        protected_spans: List[Tuple[int, int]] = []
        for lower_phrase, proper_phrase in self._multi_word_propers.items():
            pattern = re.compile(rf"\b{re.escape(lower_phrase)}\b", re.IGNORECASE)

            def _repl_multi(match: re.Match) -> str:
                orig = match.group(0)
                if orig != proper_phrase:
                    issues.append(
                        CapitalizationIssue(
                            original=orig,
                            replacement=proper_phrase,
                            reason=f"Kata nama khas '{proper_phrase}' wajib menggunakan huruf besar pada awal setiap kata.",
                        )
                    )
                return proper_phrase

            working = pattern.sub(_repl_multi, working)

        # Catat semua posisi Kata Nama Khas berbilang kata yang sudah benar
        for _, proper_phrase in self._multi_word_propers.items():
            for m in re.finditer(rf"\b{re.escape(proper_phrase)}\b", working):
                protected_spans.append(m.span())

        def _is_protected(start: int, end: int) -> bool:
            for p_start, p_end in protected_spans:
                if start >= p_start and end <= p_end:
                    return True
            return False

        # 2. Evaluasi token kata demi kata berdasarkan posisi di dalam kalimat
        token_pattern = re.compile(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b")
        result_parts: List[str] = []
        last_idx = 0

        for match in token_pattern.finditer(working):
            start, end = match.span()
            orig_word = match.group(0)
            lower_word = orig_word.lower()

            result_parts.append(working[last_idx:start])

            if _is_protected(start, end):
                result_parts.append(orig_word)
                last_idx = end
                continue

            # Cek apakah kata ini berada di awal kalimat atau tepat setelah '.', '?', '!'
            prefix_slice = working[:start]
            is_sentence_start = self._is_at_sentence_start(prefix_slice)

            target_word = orig_word

            # Kasus A: Akronim tidak ambigu (misal: prpm -> PRPM, dbp -> DBP, uitm -> UiTM)
            if lower_word in self.UNAMBIGUOUS_ACRONYMS:
                target_word = self.UNAMBIGUOUS_ACRONYMS[lower_word]
                if orig_word != target_word:
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=f"Akronim rasmi '{target_word}' wajib ditulis dengan huruf besar.",
                        )
                    )
            # Kasus B: Kata sudah ditulis kapital penuh dan terdaftar di daftar akronim (misal: RM, KL, CEO, API, IT)
            elif orig_word.isupper() and len(orig_word) >= 2 and orig_word in self.acronyms:
                target_word = orig_word
            # Kasus C: Kata Nama Khas tunggal (contoh: isnin -> Isnin, malaysia -> Malaysia, januari -> Januari)
            elif lower_word in self._single_word_propers:
                target_word = self._single_word_propers[lower_word]
                if orig_word != target_word:
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=f"Kata nama khas '{target_word}' wajib diawali huruf kapital.",
                        )
                    )
            # Kasus D: Kata ganti 'I' dan kontraksinya (I'm, I've, I'll, I'd) dalam Bahasa Inggris
            elif orig_word in ("I", "I'm", "I've", "I'll", "I'd"):
                target_word = orig_word
            # Kasus E: Kata berada di awal kalimat -> Huruf pertama wajib kapital, sisanya huruf kecil
            elif is_sentence_start:
                target_word = lower_word[0].upper() + lower_word[1:]
                if orig_word != target_word:
                    reason = (
                        f"Kata pertama pada awal kalimat wajib diawali huruf kapital ('{orig_word}' -> '{target_word}')."
                        if orig_word[0].islower()
                        else f"Penggunaan huruf kapital pada kata awal kalimat dirapikan ('{orig_word}' -> '{target_word}')."
                    )
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=reason,
                        )
                    )
            # Kasus F: Kata biasa di tengah kalimat -> Wajib huruf kecil (non-kapital)
            else:
                target_word = lower_word
                if orig_word != target_word:
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=f"Kata biasa di tengah kalimat tidak menggunakan huruf kapital ('{orig_word}' -> '{target_word}').",
                        )
                    )

            result_parts.append(target_word)
            last_idx = end

        result_parts.append(working[last_idx:])
        return "".join(result_parts), issues

    @staticmethod
    def _is_at_sentence_start(prefix_slice: str) -> bool:
        """Menentukan apakah posisi saat ini adalah awal teks atau tepat setelah tanda akhir kalimat (. ? !)."""
        stripped = prefix_slice.strip()
        if not stripped:
            return True
        return stripped[-1] in (".", "?", "!")
