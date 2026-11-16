"""
Modul Konversi Angka ke Kalimat Terbilang (Bahasa Melayu PRPM & Kustom).
Mengubah angka numerik di dalam kalimat menjadi kata bilangan secara full offline.
Contoh:
- 1000 -> seribu
- 800 -> delapan ratus (mode 'delapan') / lapan ratus (mode 'lapan' PRPM Malaysia)
- ke-2 -> kedua
- 3.5 -> tiga perpuluhan lima
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
        int_val = int(int_part_str)
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

    def convert_numbers_in_text(self, text: str) -> Tuple[str, List[NumberConversionIssue]]:
        """
        Mendeteksi semua ekspresi angka di dalam teks dan mengubahnya menjadi kalimat terbilang.
        Mendukung:
        - Bilangan tingkat: ke-1, ke-2, ke-100
        - Ribuan berpemisah koma atau titik: 1,000 / 1,250,000 / 10.000
        - Desimal: 3.5 / 12.75
        - Bilangan bulat biasa: 1000, 800, 25
        """
        issues: List[NumberConversionIssue] = []

        # Regex gabungan dengan urutan prioritas:
        # 1. Ordinal: \b[kK]e-(\d+)\b
        # 2. Ribuan dengan koma: \b\d{1,3}(?:,\d{3})+\b
        # 3. Ribuan dengan titik: \b\d{1,3}(?:\.\d{3})+\b (hanya jika grup 3 digit)
        # 4. Desimal dengan titik/koma (bukan ribuan 3 digit): \b(\d+)[\.,](\d{1,2}|\d{4,})\b
        # 5. Bilangan bulat standar: \b\d+\b
        pattern = re.compile(
            r"(?P<ordinal>\b[kK]e-(?P<ord_num>\d+)\b)"
            r"|(?P<thousand_comma>\b\d{1,3}(?:,\d{3})+\b)"
            r"|(?P<thousand_dot>\b\d{1,3}(?:\.\d{3})+\b)"
            r"|(?P<decimal>\b(?P<dec_int>\d+)[\.,](?P<dec_frac>\d{1,2}|\d{4,})\b)"
            r"|(?P<integer>\b\d+\b)"
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
            elif match.group("thousand_comma"):
                clean_num = int(original.replace(",", ""))
                replacement = self.int_to_words(clean_num)
                reason = f"Angka ribuan '{original}' diubah menjadi kalimat terbilang '{replacement}'."
            elif match.group("thousand_dot"):
                clean_num = int(original.replace(".", ""))
                replacement = self.int_to_words(clean_num)
                reason = f"Angka ribuan '{original}' diubah menjadi kalimat terbilang '{replacement}'."
            elif match.group("decimal"):
                dec_int = match.group("dec_int")
                dec_frac = match.group("dec_frac")
                replacement = self.decimal_to_words(dec_int, dec_frac)
                reason = f"Angka perpuluhan '{original}' diubah menjadi kalimat terbilang '{replacement}'."
            elif match.group("integer"):
                num_val = int(original)
                replacement = self.int_to_words(num_val)
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
