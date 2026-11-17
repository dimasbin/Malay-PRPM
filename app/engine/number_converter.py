"""
Modul Konversi Angka ke Kalimat Terbilang (Bahasa Melayu PRPM & Kustom).
Mengubah angka numerik di dalam kalimat menjadi kata bilangan secara full offline.
Mendukung:
- Bilangan bulat & ribuan/jutaan/bilion: 1000 -> seribu, 800 -> lapan ratus (atau delapan ratus)
- Bilangan bertingkat: ke-1 -> pertama, ke-2 -> kedua
- Ribuan & perpuluhan gabungan: 1,250.50 -> seribu dua ratus lima puluh perpuluhan lima sifar
- Mata wang Ringgit Malaysia: RM1000 / RM 1000 / RM1000.00 -> RM seribu
- Bilangan negatif: -5 -> negatif lima
- Peratusan: 20% -> dua puluh peratus
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class NumberConversionIssue:
    original: str
    replacement: str
    start: int
    end: int
    reason: str


class NumberConverter:
    """Konverter angka ke kalimat terbilang Bahasa Melayu."""

    _NUM_CORE_PATTERN = (
        r"(?:"
        r"\d{1,3}(?:,\d{3})+\.\d+"   # gabungan ribuan koma + desimal (1,250.50)
        r"|\d{1,3}(?:,\d{3})+"       # ribuan koma (1,000)
        r"|\d{1,3}(?:\.\d{3})+"      # ribuan titik (10.000)
        r"|\d+[\.,](?:\d{1,2}|\d{4,})"  # desimal (3.5, 12.05)
        r"|\d+"                      # bilangan bulat
        r")"
    )

    def __init__(self, eight_word: str = "lapan", zero_word: str = "sifar") -> None:
        """
        Inisialisasi konverter angka (Default: Baku Penuh PRPM Malaysia 'lapan' & 'sifar').
        :param eight_word: 'lapan' (baku PRPM Malaysia) atau 'delapan'.
        :param zero_word: 'sifar' (baku PRPM Malaysia) atau 'kosong'.
        """
        self.eight_word = eight_word if eight_word in ("lapan", "delapan") else "lapan"
        self.zero_word = zero_word if zero_word in ("sifar", "kosong", "nol") else "sifar"
        self._units = [
            "",
            "satu",
            "dua",
            "tiga",
            "empat",
            "lima",
            "enam",
            "tujuh",
            self.eight_word,
            "sembilan",
        ]

    def int_to_words(self, n: int) -> str:
        """Mengubah bilangan bulat (integer) menjadi kata terbilang."""
        if n < 0:
            return f"negatif {self.int_to_words(-n)}"
        if n == 0:
            return self.zero_word

        return self._convert_positive(n).strip()

    def _convert_positive(self, n: int) -> str:
        if n == 0:
            return ""
        if n < 10:
            return self._units[n]
        if n == 10:
            return "sepuluh"
        if n == 11:
            return "sebelas"
        if n < 20:
            return f"{self._units[n - 10]} belas"
        if n < 100:
            puluh = n // 10
            sisa = n % 10
            if sisa == 0:
                return f"{self._units[puluh]} puluh"
            return f"{self._units[puluh]} puluh {self._units[sisa]}"
        if n < 200:
            sisa = n - 100
            if sisa == 0:
                return "seratus"
            return f"seratus {self._convert_positive(sisa)}"
        if n < 1000:
            ratus = n // 100
            sisa = n % 100
            if sisa == 0:
                return f"{self._units[ratus]} ratus"
            return f"{self._units[ratus]} ratus {self._convert_positive(sisa)}"
        if n < 2000:
            sisa = n - 1000
            if sisa == 0:
                return "seribu"
            return f"seribu {self._convert_positive(sisa)}"
        if n < 1_000_000:
            ribu = n // 1000
            sisa = n % 1000
            ribu_str = f"{self._convert_positive(ribu)} ribu"
            if sisa == 0:
                return ribu_str
            return f"{ribu_str} {self._convert_positive(sisa)}"
        if n < 1_000_000_000:
            juta = n // 1_000_000
            sisa = n % 1_000_000
            juta_str = f"{self._convert_positive(juta)} juta"
            if sisa == 0:
                return juta_str
            return f"{juta_str} {self._convert_positive(sisa)}"
        if n < 1_000_000_000_000:
            bilion = n // 1_000_000_000
            sisa = n % 1_000_000_000
            bilion_str = f"{self._convert_positive(bilion)} bilion"
            if sisa == 0:
                return bilion_str
            return f"{bilion_str} {self._convert_positive(sisa)}"

        trilion = n // 1_000_000_000_000
        sisa = n % 1_000_000_000_000
        trilion_str = f"{self._convert_positive(trilion)} trilion"
        if sisa == 0:
            return trilion_str
        return f"{trilion_str} {self._convert_positive(sisa)}"

    def decimal_to_words(self, int_part_str: str, frac_part_str: str) -> str:
        """Mengubah angka desimal menjadi teks terbilang (menggunakan 'perpuluhan')."""
        int_val = int(int_part_str.replace(",", "").replace(".", ""))
        int_words = self.int_to_words(int_val)
        frac_words_list = []
        for ch in frac_part_str:
            if ch.isdigit():
                d = int(ch)
                frac_words_list.append(self.zero_word if d == 0 else self._units[d])
        frac_words = " ".join(frac_words_list)
        return f"{int_words} perpuluhan {frac_words}".strip()

    def ordinal_to_words(self, n: int) -> str:
        """Mengubah angka bertingkat (ke-1, ke-2) menjadi kata bilangan tingkat."""
        if n == 1:
            return "pertama"
        return f"ke{self.int_to_words(n)}"

    def _numeric_str_to_words(self, num_str: str, strip_zero_cents: bool = False) -> str:
        """Mengubah representasi angka string (termasuk ribuan & perpuluhan) menjadi kalimat terbilang."""
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d+", num_str):
            int_part, frac_part = num_str.split(".", 1)
            if strip_zero_cents and set(frac_part) == {"0"}:
                return self.int_to_words(int(int_part.replace(",", "")))
            return self.decimal_to_words(int_part, frac_part)

        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", num_str):
            return self.int_to_words(int(num_str.replace(",", "")))

        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", num_str):
            return self.int_to_words(int(num_str.replace(".", "")))

        if re.fullmatch(r"\d+[\.,](?:\d{1,2}|\d{4,})", num_str):
            sep = "." if "." in num_str else ","
            int_part, frac_part = num_str.split(sep, 1)
            if strip_zero_cents and set(frac_part) == {"0"}:
                return self.int_to_words(int(int_part))
            return self.decimal_to_words(int_part, frac_part)

        return self.int_to_words(int(num_str))

    def convert_numbers_in_text(self, text: str) -> Tuple[str, List[NumberConversionIssue]]:
        """Mendeteksi dan mengonversi seluruh ekspresi angka di dalam teks menjadi kalimat terbilang."""
        issues: List[NumberConversionIssue] = []

        pattern = re.compile(
            rf"(?P<ordinal>\b[kK]e-(?P<ord_num>\d+)\b)"
            rf"|(?P<currency>\bRM\s*(?P<rm_num>{self._NUM_CORE_PATTERN}))"
            rf"|(?P<percent>(?<!\w)(?P<pct_sign>-?)(?P<pct_num>{self._NUM_CORE_PATTERN})%)"
            rf"|(?P<negative>(?<!\w)-(?P<neg_num>{self._NUM_CORE_PATTERN}))"
            rf"|(?P<plain>\b{self._NUM_CORE_PATTERN}\b)"
        )

        result_parts: List[str] = []
        last_idx = 0

        for match in pattern.finditer(text):
            start, end = match.span()
            original = match.group(0)
            replacement = original
            reason = ""

            if match.group("ordinal"):
                num_val = int(match.group("ord_num"))
                replacement = self.ordinal_to_words(num_val)
                if original[0].isupper():
                    replacement = replacement.capitalize()
                reason = f"Angka tingkat '{original}' diubah menjadi kata bilangan tingkat '{replacement}'."
            elif match.group("currency"):
                num_words = self._numeric_str_to_words(
                    match.group("rm_num"), strip_zero_cents=True
                )
                replacement = f"RM {num_words}"
                reason = f"Nilai mata wang '{original}' diubah menjadi '{replacement}'."
            elif match.group("percent"):
                pct_words = self._numeric_str_to_words(match.group("pct_num"))
                prefix = "negatif " if match.group("pct_sign") == "-" else ""
                replacement = f"{prefix}{pct_words} peratus"
                reason = f"Peratusan '{original}' diubah menjadi '{replacement}'."
            elif match.group("negative"):
                neg_words = self._numeric_str_to_words(match.group("neg_num"))
                replacement = f"negatif {neg_words}"
                reason = f"Angka negatif '{original}' diubah menjadi '{replacement}'."
            elif match.group("plain"):
                replacement = self._numeric_str_to_words(original)
                reason = f"Angka '{original}' diubah menjadi kalimat terbilang '{replacement}'."

            result_parts.append(text[last_idx:start])
            result_parts.append(replacement)
            issues.append(
                NumberConversionIssue(
                    original=original,
                    replacement=replacement,
                    start=start,
                    end=end,
                    reason=reason,
                )
            )
            last_idx = end

        result_parts.append(text[last_idx:])
        return "".join(result_parts), issues
