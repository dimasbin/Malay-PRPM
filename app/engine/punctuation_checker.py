"""
Modul Pemeriksa Tanda Baca (Titik '.', Koma ',', Tanya '?') Berdasarkan Kaidah Tatabahasa Dewan (PRPM).
Menangani:
1. Penghapusan spasi sebelum tanda titik, koma, dan tanda tanya.
2. Penambahan spasi setelah tanda titik, koma, dan tanda tanya jika rapat dengan kata berikutnya.
3. Penormalan tanda baca ganda ('..', ',,', '??').
4. Deteksi Ayat Tanya (kata tanya Melayu / partikel -kah) agar diakhiri tanda tanya ('?').
5. Penambahan tanda titik ('.') pada akhir Ayat Penyata yang belum memiliki tanda penutup.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PunctuationIssue:
    original: str
    replacement: str
    reason: str


class PunctuationChecker:
    """Pemeriksa tanda titik, koma, dan tanda tanya Bahasa Melayu PRPM."""

    # Kata tanya mutlak dalam Bahasa Melayu
    STRONG_QUESTION_WORDS = {
        "apakah",
        "siapakah",
        "bilakah",
        "mengapakah",
        "bagaimanakah",
        "adakah",
        "berapakah",
        "manakah",
        "kenapakah",
    }

    # Kata tanya yang menjadi penanda tanya jika di awal kalimat atau awal klausa setelah koma
    CONTEXTUAL_QUESTION_WORDS = {
        "apa",
        "siapa",
        "bila",
        "berapa",
        "mana",
        "mengapa",
        "kenapa",
        "bagaimana",
    }

    def check_and_fix(self, text: str) -> Tuple[str, List[PunctuationIssue]]:
        """Memeriksa dan memperbaiki tanda baca titik, koma, dan tanya pada kalimat."""
        if not text or not text.strip():
            return text, []

        issues: List[PunctuationIssue] = []
        working = text.strip()

        # 1. Hapus spasi sebelum tanda baca (.,?!)
        space_before_pattern = re.compile(r"\s+([.,?!:;])")
        for m in space_before_pattern.finditer(working):
            orig_seg = m.group(0)
            punct = m.group(1)
            issues.append(
                PunctuationIssue(
                    original=orig_seg,
                    replacement=punct,
                    reason=f"Spasi sebelum tanda baca '{punct}' dihapuskan mengikut kaidah penulisan baku.",
                )
            )
        working = space_before_pattern.sub(r"\1", working)

        # 2. Normalkan tanda baca berulang (.., ,,, ??, !., ,.)
        multi_punct_pattern = re.compile(r"([.,?!])\1+|,\.|;\.")
        for m in multi_punct_pattern.finditer(working):
            orig_seg = m.group(0)
            replacement_punct = orig_seg[-1] if orig_seg in (",.", ";.") else orig_seg[0]
            issues.append(
                PunctuationIssue(
                    original=orig_seg,
                    replacement=replacement_punct,
                    reason=f"Tanda baca ganda/tidak tepat '{orig_seg}' dibakukan menjadi '{replacement_punct}'.",
                )
            )
        working = re.sub(r",\.", ".", working)
        working = re.sub(r"([.,?!])\1+", r"\1", working)

        # 3. Tambahkan spasi setelah tanda baca (.,?!) jika menempel langsung dengan huruf
        missing_space_after_pattern = re.compile(r"([.,?!])([A-Za-z])")
        for m in missing_space_after_pattern.finditer(working):
            orig_seg = m.group(0)
            fixed_seg = f"{m.group(1)} {m.group(2)}"
            issues.append(
                PunctuationIssue(
                    original=orig_seg,
                    replacement=fixed_seg,
                    reason=f"Ditambahkan spasi selepas tanda baca '{m.group(1)}' ('{orig_seg}' -> '{fixed_seg}').",
                )
            )
        working = missing_space_after_pattern.sub(r"\1 \2", working)

        # 4. Rapikan spasi berlebih di tengah kalimat
        if re.search(r"\s{2,}", working):
            issues.append(
                PunctuationIssue(
                    original="(spasi ganda)",
                    replacement="(spasi tunggal)",
                    reason="Spasi berlebih di antara kata dirapikan menjadi satu spasi.",
                )
            )
            working = re.sub(r"\s{2,}", " ", working)

        # 5. Evaluasi tiap kalimat untuk tanda penutup akhir ('.' vs '?')
        working = self._fix_sentence_endings(working, issues)

        return working, issues

    def _fix_sentence_endings(
        self, text: str, issues: List[PunctuationIssue]
    ) -> str:
        """Memeriksa setiap kalimat apakah merupakan Ayat Tanya ('?') atau Ayat Penyata ('.')."""
        # Pisahkan berdasarkan penutup kalimat (. ? !) sambil menyimpan tanda penutupnya
        parts = re.split(r"([.?!])", text)
        rebuilt: List[str] = []

        idx = 0
        while idx < len(parts):
            sentence_body = parts[idx]
            ending = parts[idx + 1] if (idx + 1) < len(parts) else ""
            idx += 2

            if not sentence_body.strip():
                if ending:
                    rebuilt.append(ending)
                continue

            is_question, q_trigger = self._is_interrogative_sentence(sentence_body)

            if is_question:
                if ending == ".":
                    issues.append(
                        PunctuationIssue(
                            original=f"{sentence_body.strip()}.",
                            replacement=f"{sentence_body.strip()}?",
                            reason=(
                                f"Kalimat mengandung penanda tanya '{q_trigger}' (Ayat Tanya), "
                                "sehingga tanda titik ('.') di akhir kalimat diubah menjadi tanda tanya ('?')."
                            ),
                        )
                    )
                    ending = "?"
                elif ending == "":
                    issues.append(
                        PunctuationIssue(
                            original=sentence_body.strip(),
                            replacement=f"{sentence_body.strip()}?",
                            reason=(
                                f"Kalimat mengandung penanda tanya '{q_trigger}' (Ayat Tanya), "
                                "sehingga ditambahkan tanda tanya ('?') di akhir kalimat."
                            ),
                        )
                    )
                    ending = "?"
            else:
                if ending == "":
                    issues.append(
                        PunctuationIssue(
                            original=sentence_body.strip(),
                            replacement=f"{sentence_body.strip()}.",
                            reason="Kalimat penyata wajib diakhiri dengan tanda titik ('.').",
                        )
                    )
                    ending = "."

            rebuilt.append(sentence_body + ending)

        return "".join(rebuilt)

    def _is_interrogative_sentence(self, sentence: str) -> Tuple[bool, str]:
        """
        Mendeteksi apakah sebuah kalimat merupakan Ayat Tanya Bahasa Melayu.
        Mengembalikan (True, kata_pemicu) jika Ayat Tanya.
        """
        clean = sentence.strip().lower()
        words = re.findall(r"\b[a-z]+(?:-[a-z]+)*\b", clean)
        if not words:
            return False, ""

        # 1. Cek kata tanya mutlak di mana saja dalam kalimat (apakah, siapakah, bilakah, adakah, mengapa, bagaimana, dll.)
        for w in words:
            if w in self.STRONG_QUESTION_WORDS:
                return True, w
            # Kata berpartikel -kah (contoh: bolehkah, sudahkah, benarkah, perlukah, dapatkah)
            if w.endswith("kah") and len(w) >= 6 and w not in ("langkah", "sedekah", "nafkah", "tingkah", "rekah", "mekah", "nikah", "warkah", "berkah"):
                return True, w

        # 2. Cek frasa tanya 'di mana', 'ke mana', 'dari mana', 'di manakah'
        for phrase in ("di mana", "ke mana", "dari mana", "di manakah", "ke manakah", "dari manakah"):
            if re.search(rf"\b{re.escape(phrase)}\b", clean):
                return True, phrase

        # 3. Cek kata tanya kontekstual ('apa', 'siapa', 'bila', 'berapa') di awal kalimat atau tepat setelah koma
        clauses = [c.strip() for c in clean.split(",") if c.strip()]
        for clause in clauses:
            clause_words = re.findall(r"\b[a-z]+\b", clause)
            if clause_words and clause_words[0] in self.CONTEXTUAL_QUESTION_WORDS:
                # Pastikan bukan frasa pernyataan seperti 'bila-bila' atau 'apa-apa'
                if not clause.startswith(f"{clause_words[0]}-{clause_words[0]}"):
                    return True, clause_words[0]

        return False, ""
