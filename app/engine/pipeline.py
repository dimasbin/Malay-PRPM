"""
Orkestrator Pipeline Utama Pemeriksa & Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) Full Offline.
Mengintegrasikan:
1. Konversi Angka ke Kalimat Terbilang Baku (1000 -> seribu, 800 -> lapan ratus / delapan ratus).
2. Pemeriksaan & Pembakuan Kata PRPM Malaysia + Bypass Kata Bahasa Inggris (Tidak Diganti).
3. Pemeriksaan Titik ('.'), Koma (','), dan Tanda Tanya ('?').
4. Pemeriksaan Penggunaan Huruf Kapital & Non-Kapital.
"""

from __future__ import annotations
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from app.data.seed_lexicon import DB_PATH
from app.engine.capitalization_checker import CapitalizationChecker
from app.engine.lexicon_checker import LexiconChecker
from app.engine.number_converter import NumberConverter
from app.engine.punctuation_checker import PunctuationChecker


@dataclass
class CorrectionItem:
    category: str  # 'PRPM_KATA', 'PRPM_MAJMUK', 'PRPM_EJAAN', 'ANGKA', 'TANDA_BACA', 'KAPITAL'
    original: str
    replacement: str
    reason: str


@dataclass
class PipelineResult:
    original_text: str
    corrected_text: str
    is_valid_without_changes: bool
    english_words_preserved: List[str] = field(default_factory=list)
    corrections: List[CorrectionItem] = field(default_factory=list)
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
    ) -> None:
        self.lexicon_checker = LexiconChecker(db_path=db_path)
        if eight_word == "delapan":
            self.lexicon_checker.ms_standardization.pop("delapan", None)
            self.lexicon_checker.prpm_words.add("delapan")
        self.number_converter = NumberConverter(
            eight_word=eight_word, zero_word=zero_word
        )
        self.punctuation_checker = PunctuationChecker()
        self.capitalization_checker = CapitalizationChecker(
            proper_nouns=self.lexicon_checker.proper_nouns,
            acronyms=self.lexicon_checker.acronyms,
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
        working = text.strip()

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
        working, lex_issues, english_kept = self.lexicon_checker.check_and_standardize(
            working
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

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        is_unchanged = working == text.strip() and len(all_corrections) == 0

        return PipelineResult(
            original_text=text,
            corrected_text=working,
            is_valid_without_changes=is_unchanged,
            english_words_preserved=english_kept,
            corrections=all_corrections,
            processing_time_ms=elapsed_ms,
        )
