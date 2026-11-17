"""
Modul Penanganan Tag [OVERLAP/]...[/OVERLAP] Sesuai Peraturan Anotasi PM:
1. Tag tanpa tanda baca menempel langsung ke kata:
   'I go to [OVERLAP/]school[/OVERLAP] today.'
2. Tanda baca yang mengikuti kata bertindih wajib berada DI DALAM tag penutup:
   'I go to school [OVERLAP/]today.[/OVERLAP]'
3. Spasi antar kata berada di luar tag (sebelum [OVERLAP/] dan selepas [/OVERLAP]),
   TIDAK PERNAH di dalam tag.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple

OPEN_TAG = "[OVERLAP/]"
CLOSE_TAG = "[/OVERLAP]"
OPEN_SENTINEL = "\uE000"
CLOSE_SENTINEL = "\uE001"


@dataclass
class OverlapIssue:
    original: str
    replacement: str
    reason: str


class OverlapHandler:
    """Normalisasi, proteksi sentinel, dan validasi tag [OVERLAP/]...[/OVERLAP]."""

    _OPEN_RE = re.compile(r"\[overlap/\]", re.IGNORECASE)
    _CLOSE_RE = re.compile(r"\[/overlap\]", re.IGNORECASE)

    def prepare(self, text: str) -> Tuple[str, List[OverlapIssue]]:
        """
        Menormalkan spasi/huruf pada tag [OVERLAP/]...[/OVERLAP] dan menggantinya dengan
        karakter sentinel sementara agar tahap NLP (angka, kamus, tanda baca, kapital) tidak merusak tag.
        """
        if not text or not self._OPEN_RE.search(text) and not self._CLOSE_RE.search(text):
            return text, []

        issues: List[OverlapIssue] = []
        working = text

        # 1. Normalkan huruf besar tag jika tertulis huruf kecil/campuran
        for pat, canonical in ((self._OPEN_RE, OPEN_TAG), (self._CLOSE_RE, CLOSE_TAG)):
            for m in pat.finditer(working):
                if m.group(0) != canonical:
                    issues.append(
                        OverlapIssue(
                            original=m.group(0),
                            replacement=canonical,
                            reason=f"Penulisan tag '{m.group(0)}' dibakukan menjadi '{canonical}'.",
                        )
                    )
            working = pat.sub(canonical, working)

        # 2. Pastikan spasi di luar tag tidak menempel ke kata luar (kecuali tanda buka kurung/kutip)
        missing_before = re.compile(r"(?<=[A-Za-z0-9.,?!])\[OVERLAP/\]")
        if missing_before.search(working):
            issues.append(
                OverlapIssue(
                    original="[OVERLAP/]",
                    replacement=" [OVERLAP/]",
                    reason="Ditambahkan spasi sebelum tag pembuka '[OVERLAP/]'.",
                )
            )
            working = missing_before.sub(f" {OPEN_TAG}", working)

        missing_after = re.compile(r"\[/OVERLAP\](?=[A-Za-z0-9])")
        if missing_after.search(working):
            issues.append(
                OverlapIssue(
                    original="[/OVERLAP]",
                    replacement="[/OVERLAP] ",
                    reason="Ditambahkan spasi selepas tag penutup '[/OVERLAP]'.",
                )
            )
            working = missing_after.sub(f"{CLOSE_TAG} ", working)

        # 3. Hapus spasi di dalam tag ([OVERLAP/] kata -> [OVERLAP/]kata, kata [/OVERLAP] -> kata[/OVERLAP])
        inner_open_space = re.compile(r"\[OVERLAP/\]\s+")
        if inner_open_space.search(working):
            issues.append(
                OverlapIssue(
                    original="[OVERLAP/] ",
                    replacement=OPEN_TAG,
                    reason="Spasi selepas tag '[OVERLAP/]' dihapus kerana spasi wajib berada di luar tag.",
                )
            )
            working = inner_open_space.sub(OPEN_TAG, working)

        inner_close_space = re.compile(r"\s+\[/OVERLAP\]")
        if inner_close_space.search(working):
            issues.append(
                OverlapIssue(
                    original=" [/OVERLAP]",
                    replacement=CLOSE_TAG,
                    reason="Spasi sebelum tag '[/OVERLAP]' dihapus kerana spasi wajib berada di luar tag.",
                )
            )
            working = inner_close_space.sub(CLOSE_TAG, working)

        # 4. Cek keseimbangan pasangan tag
        open_count = working.count(OPEN_TAG)
        close_count = working.count(CLOSE_TAG)
        if open_count != close_count:
            issues.append(
                OverlapIssue(
                    original=f"([OVERLAP/]={open_count}, [/OVERLAP]={close_count})",
                    replacement="Periksa pasangan tag",
                    reason=(
                        f"Bilangan tag pembuka [OVERLAP/] ({open_count}) dan penutup [/OVERLAP] ({close_count}) "
                        "tidak seimbang."
                    ),
                )
            )

        # 5. Ganti dengan sentinel sementara agar tahap NLP berikutnya transparan
        working = working.replace(OPEN_TAG, OPEN_SENTINEL).replace(CLOSE_TAG, CLOSE_SENTINEL)
        return working, issues

    def finalize(self, text: str, raw_input: str) -> Tuple[str, List[OverlapIssue]]:
        """
        Memasukkan tanda baca penutup ke dalam [/OVERLAP] mengikut peraturan PM,
        lalu mengembalikan karakter sentinel ke tag [OVERLAP/] dan [/OVERLAP].
        """
        if OPEN_SENTINEL not in text and CLOSE_SENTINEL not in text:
            return text, []

        issues: List[OverlapIssue] = []

        # Pindahkan tanda baca tepat setelah CLOSE_SENTINEL ke dalam tag penutup
        outside_punct_pat = re.compile(rf"{CLOSE_SENTINEL}\s*([.,?!:;]+)")
        had_outside_in_raw = bool(
            re.search(r"\[/OVERLAP\]\s*[.,?!:;]+", raw_input, re.IGNORECASE)
        )
        if outside_punct_pat.search(text) and had_outside_in_raw:
            issues.append(
                OverlapIssue(
                    original="[/OVERLAP]<tanda_baca>",
                    replacement="<tanda_baca>[/OVERLAP]",
                    reason=(
                        "Mengikut peraturan PM, tanda baca selepas kata bertindih wajib diletakkan "
                        "di dalam tag penutup '[/OVERLAP]'."
                    ),
                )
            )

        working = outside_punct_pat.sub(rf"\1{CLOSE_SENTINEL}", text)

        # Cegah tanda baca ganda tepat sebelum CLOSE_SENTINEL jika terjadi penggabungan
        working = re.sub(rf"([.,?!])\1+{CLOSE_SENTINEL}", rf"\1{CLOSE_SENTINEL}", working)

        # Kembalikan sentinel ke tag asli
        working = working.replace(OPEN_SENTINEL, OPEN_TAG).replace(CLOSE_SENTINEL, CLOSE_TAG)

        # Pastikan ada spasi sesudah [/OVERLAP] bila diikuti kata berikutnya
        working = re.sub(r"\[/OVERLAP\](?=[A-Za-z0-9])", f"{CLOSE_TAG} ", working)

        return working, issues
