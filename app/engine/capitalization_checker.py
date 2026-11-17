"""
Modul Pemeriksa Huruf Kapital dan Non-Kapital (Case Normalization) Mengikut Tatabahasa Dewan PRPM.
Menangani:
1. Huruf pertama pada awal kalimat dan selepas tanda noktah ('.'), tanda tanya ('?'), atau tanda seru ('!') wajib kapital.
2. Kata Nama Khas (nama orang, jenama/produk, hari, bulan, negara, negeri, bandar, bahasa) wajib diawali huruf kapital.
3. Akronim rasmi ('PRPM', 'DBP', 'UiTM', 'KWSP', 'RM', dll.) ditulis dengan huruf kapital yang tepat.
4. Kata tugas tengah nama orang ('bin', 'binti', 'al-') kekal huruf kecil di tengah kalimat.
5. Kata biasa (Melayu maupun Inggris dalam kamus umum) di tengah kalimat yang salah kapital diubah ke huruf kecil,
   sedangkan nama diri/merek tak dikenal yang berpola Title Case dipertahankan sebagai Kata Nama Khas.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from app.engine.morphology import MorphologyAnalyzer


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
        "cimb": "CIMB",
    }

    # Jenama yang bertindih dengan kata biasa Inggris/Melayu: dipertahankan jika memang ditulis kapital
    CASE_SENSITIVE_BRANDS: Set[str] = {
        "Chrome", "Word", "Teams", "Zoom", "Excel", "Apple", "Grab",
        "Windows", "Linux", "Proton", "Perodua", "Notion", "Slack",
        "Oracle", "Java", "Python", "Android", "Google", "WhatsApp",
    }

    # Kontraksi kata ganti 'I' dalam Bahasa Inggris
    _EN_I_CONTRACTIONS: Dict[str, str] = {
        "i'm": "I'm",
        "i've": "I've",
        "i'll": "I'll",
        "i'd": "I'd",
    }

    _TITLE_ABBR_PREFIX_RE = re.compile(r"(?:^|\s)(?:Dr|En|Pn|Hj|Hjh|Prof|Tn)\.$")
    _NAME_PRECEDERS_RE = re.compile(
        r"(?:^|\s)(?:(?:Dr|En|Pn|Hj|Hjh|Prof|Tn)\.|(?:encik|puan|cik|tuan|datuk|dato|tun|bin|binti))\s*$",
        re.IGNORECASE,
    )
    _TITLE_WORDS_BEFORE_NAME = {
        "encik", "puan", "cik", "tuan", "datuk", "dato", "tun",
        "haji", "hajah", "profesor", "doktor",
    }
    _FOLLOWING_PROPER_NAME_RE = re.compile(r"^\s+[A-Z][a-z]+")

    def __init__(
        self,
        proper_nouns: Dict[str, str],
        acronyms: Set[str],
        prpm_words: Optional[Set[str]] = None,
        english_words: Optional[Set[str]] = None,
        morphology: Optional[MorphologyAnalyzer] = None,
    ) -> None:
        self.proper_nouns = proper_nouns
        self.acronyms = {a.upper() for a in acronyms}
        self.prpm_words = prpm_words or set()
        self.english_words = english_words or set()
        self.morphology = morphology or MorphologyAnalyzer(
            prpm_roots=self.prpm_words,
            english_roots=self.english_words,
        )
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
            # Kasus C: Jenama sensitif huruf kapital yang ditulis sesuai bentuk jenamanya (Chrome, Zoom, Excel)
            elif orig_word in self.CASE_SENSITIVE_BRANDS:
                target_word = orig_word
            # Kasus D: Kata Nama Khas tunggal (contoh: isnin -> Isnin, malaysia -> Malaysia, google -> Google)
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
            # Kasus E: Kata ganti 'I' dan kontraksi Bahasa Inggris (i'm -> I'm, i've -> I've)
            elif lower_word in self._EN_I_CONTRACTIONS:
                target_word = self._EN_I_CONTRACTIONS[lower_word]
                if orig_word != target_word:
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=f"Kata ganti diri Bahasa Inggeris '{target_word}' wajib diawali huruf kapital.",
                        )
                    )
            elif orig_word == "I":
                target_word = "I"
            # Kasus F: Singkatan gelar bertitik (Dr., En., Pn., Hj., Hjh., Prof., Tn.) atau panggilan sebelum nama orang
            elif lower_word in ("dr", "en", "pn", "hj", "hjh", "prof", "tn") and working[end : end + 1] == ".":
                target_word = lower_word[0].upper() + lower_word[1:]
                if orig_word != target_word:
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=f"Singkatan gelaran '{target_word}.' wajib diawali huruf kapital.",
                        )
                    )
            elif lower_word in self._TITLE_WORDS_BEFORE_NAME and self._FOLLOWING_PROPER_NAME_RE.match(working[end:]):
                target_word = lower_word[0].upper() + lower_word[1:]
                if orig_word != target_word:
                    issues.append(
                        CapitalizationIssue(
                            original=orig_word,
                            replacement=target_word,
                            reason=f"Kata gelaran/panggilan '{target_word}' sebelum nama khas wajib diawali huruf kapital.",
                        )
                    )
            # Kasus G: Kata berada di awal kalimat -> Huruf pertama wajib kapital, sisanya huruf kecil
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
            # Kasus H: Kata Title Case/Mixed Case di tengah kalimat yang BUKAN kata umum kamus atau berada di posisi nama orang -> pelihara
            elif self._is_likely_proper_noun_token(
                orig_word, lower_word, prefix_slice, working[end:]
            ):
                target_word = orig_word
            # Kasus I: Kata biasa di tengah kalimat -> Wajib huruf kecil (non-kapital)
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

    def _is_likely_proper_noun_token(
        self,
        orig_word: str,
        lower_word: str,
        prefix_slice: str = "",
        suffix_slice: str = "",
    ) -> bool:
        """
        Menentukan apakah token berhuruf kapital di tengah kalimat kemungkinan merupakan
        Kata Nama Khas (nama orang, merek, tempat) yang tidak boleh dipaksa jadi huruf kecil.
        """
        if not orig_word[0].isupper() or orig_word.isupper():
            return False
        if lower_word in ("bin", "binti"):
            return False
        if self._NAME_PRECEDERS_RE.search(prefix_slice) or re.match(r"^\s+(?:bin|binti)\b", suffix_slice, re.IGNORECASE):
            return True
        is_common_word = (
            self.morphology.is_valid_malay_word(lower_word)
            or self.morphology.is_valid_english_word(lower_word)
        )
        return not is_common_word

    def _is_at_sentence_start(self, prefix_slice: str) -> bool:
        """Menentukan apakah posisi saat ini adalah awal teks atau tepat setelah tanda akhir kalimat (. ? !)."""
        stripped = prefix_slice.strip()
        if not stripped:
            return True
        if self._TITLE_ABBR_PREFIX_RE.search(stripped):
            return False
        return stripped[-1] in (".", "?", "!")
