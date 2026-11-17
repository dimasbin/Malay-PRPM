"""
Orkestrator Pipeline Utama Pemeriksa & Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) Full Offline.
Mengintegrasikan:
0. Normalisasi & proteksi tag anotasi [OVERLAP/]...[/OVERLAP] sesuai peraturan PM.
1. Konversi Angka ke Kalimat Terbilang Baku (1000 -> seribu, 800 -> lapan ratus / delapan ratus, RM1000 -> RM seribu, -5, 20%, 1,250.50).
2. Pemeriksaan & Pembakuan Kata PRPM Malaysia:
   - Mode 'annotation' (Default, peraturan PM): Kata lisan Group 1 (tak, nak, je, kat, jap, pastu, kot, ni, tu, dah, sorang, lah, kan) ditulis apa adanya; loghat Group 2 (ade, saye, ape, kite, ambik, balek) dibakukan.
   - Mode 'baku': Pembakuan penuh PRPM DBP Malaysia.
   - Kata Bahasa Inggris tidak diganti.
3. Pemeriksaan Titik ('.'), Koma (','), dan Tanda Tanya ('?').
4. Pemeriksaan Penggunaan Huruf Kapital & Non-Kapital mengikut Tatabahasa Dewan.
"""

from __future__ import annotations
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from app.data.seed_lexicon import DB_PATH
from app.engine.capitalization_checker import CapitalizationChecker
from app.engine.lexicon_checker import LexiconChecker
from app.engine.number_converter import NumberConverter
from app.engine.overlap_handler import OverlapHandler
from app.engine.punctuation_checker import PunctuationChecker


@dataclass
class CorrectionItem:
    category: str  # 'OVERLAP_TAG', 'PRPM_KATA', 'PRPM_MAJMUK', 'PRPM_EJAAN', 'ANGKA', 'TANDA_BACA', 'KAPITAL'
    original: str
    replacement: str
    reason: str


@dataclass
class UnknownWordItem:
    word: str
    suggestions: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class PipelineResult:
    original_text: str
    corrected_text: str
    is_valid_without_changes: bool
    english_words_preserved: List[str] = field(default_factory=list)
    corrections: List[CorrectionItem] = field(default_factory=list)
    unknown_words: List[UnknownWordItem] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PRPMPipeline:
    """Pipeline Full Offline untuk pemeriksaan kalimat Bahasa Melayu (PRPM) + Campuran Inggris."""

    def __init__(
        self,
        db_path: str = DB_PATH,
        eight_word: str = "lapan",
        zero_word: str = "sifar",
        mode: str = "annotation",
    ) -> None:
        self.mode = mode if mode in ("annotation", "baku") else "annotation"
        self.lexicon_checker = LexiconChecker(db_path=db_path)
        if eight_word == "delapan":
            self.lexicon_checker.ms_standardization.pop("delapan", None)
            self.lexicon_checker.prpm_words.add("delapan")
        self.overlap_handler = OverlapHandler()
        self.number_converter = NumberConverter(
            eight_word=eight_word, zero_word=zero_word
        )
        self.punctuation_checker = PunctuationChecker()
        self.capitalization_checker = CapitalizationChecker(
            proper_nouns=self.lexicon_checker.proper_nouns,
            acronyms=self.lexicon_checker.acronyms,
            prpm_words=self.lexicon_checker.prpm_words,
            english_words=self.lexicon_checker.english_words,
            morphology=self.lexicon_checker.morphology,
        )

    def process(self, text: str) -> PipelineResult:
        """Memproses satu kalimat atau paragraf melalui seluruh tahapan pemeriksaan."""
        t0 = time.perf_counter()

        if not text or not text.strip():
            return PipelineResult(
                original_text=text,
                corrected_text=text,
                is_valid_without_changes=True,
                processing_time_ms=0.0,
            )

        all_corrections: List[CorrectionItem] = []
        raw_stripped = text.strip()
        working = raw_stripped

        # Tahap 0: Normalisasi & proteksi tag [OVERLAP/]...[/OVERLAP]
        working, overlap_pre_issues = self.overlap_handler.prepare(working)
        for oi in overlap_pre_issues:
            all_corrections.append(
                CorrectionItem(
                    category="OVERLAP_TAG",
                    original=oi.original,
                    replacement=oi.replacement,
                    reason=oi.reason,
                )
            )

        # Tahap 1: Konversi Angka ke Kalimat Terbilang
        working, num_issues = self.number_converter.convert_numbers_in_text(working)
        for ni in num_issues:
            all_corrections.append(
                CorrectionItem(
                    category="ANGKA",
                    original=ni.original,
                    replacement=ni.replacement,
                    reason=ni.reason,
                )
            )

        # Tahap 2: Pemeriksaan Kata PRPM Malaysia & Deteksi Kata Bahasa Inggris (Tidak Diganti)
        working, lex_issues, english_kept, unknown_issues = (
            self.lexicon_checker.check_and_standardize(working, mode=self.mode)
        )
        for li in lex_issues:
            cat_map = {
                "PRPM_BAKU": "PRPM_KATA",
                "PRPM_MAJMUK": "PRPM_MAJMUK",
                "PRPM_TYPO": "PRPM_EJAAN",
            }
            all_corrections.append(
                CorrectionItem(
                    category=cat_map.get(li.category, "PRPM_KATA"),
                    original=li.original,
                    replacement=li.replacement,
                    reason=li.reason,
                )
            )

        unknown_items = [
            UnknownWordItem(
                word=ui.word,
                suggestions=ui.suggestions,
                reason=ui.reason,
            )
            for ui in unknown_issues
        ]

        # Tahap 3: Pemeriksaan Tanda Baca (Titik, Koma, Tanya)
        working, punct_issues = self.punctuation_checker.check_and_fix(working)
        for pi in punct_issues:
            all_corrections.append(
                CorrectionItem(
                    category="TANDA_BACA",
                    original=pi.original,
                    replacement=pi.replacement,
                    reason=pi.reason,
                )
            )

        # Tahap 4: Pemeriksaan Huruf Kapital & Non-Kapital
        working, cap_issues = self.capitalization_checker.check_and_fix(working)
        for ci in cap_issues:
            all_corrections.append(
                CorrectionItem(
                    category="KAPITAL",
                    original=ci.original,
                    replacement=ci.replacement,
                    reason=ci.reason,
                )
            )

        # Tahap 5: Kembalikan tag [OVERLAP/]...[/OVERLAP] & masukkan tanda baca ke dalam [/OVERLAP]
        working, overlap_post_issues = self.overlap_handler.finalize(working, raw_stripped)
        for oi in overlap_post_issues:
            all_corrections.append(
                CorrectionItem(
                    category="OVERLAP_TAG",
                    original=oi.original,
                    replacement=oi.replacement,
                    reason=oi.reason,
                )
            )

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        is_unchanged = working == raw_stripped and len(all_corrections) == 0

        return PipelineResult(
            original_text=text,
            corrected_text=working,
            is_valid_without_changes=is_unchanged,
            english_words_preserved=english_kept,
            corrections=all_corrections,
            unknown_words=unknown_items,
            processing_time_ms=elapsed_ms,
        )
