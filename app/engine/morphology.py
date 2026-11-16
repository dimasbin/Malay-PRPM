"""
Modul Analisis Morfologi Bahasa Melayu (PRPM DBP) & Infleksi Bahasa Inggris.
Digunakan untuk:
1. Memvalidasi kata berimbuhan Bahasa Melayu (awalan, akhiran, apitan, partikel, kata ganda)
   terhadap leksikon kata dasar PRPM.
2. Mengenali kata Bahasa Inggris berimbuhan (-s, -es, -ed, -ing, -ly, un-, re-, dll.)
   agar kata campuran Bahasa Inggris tetap dipertahankan dan tidak dianggap salah eja.
"""

from __future__ import annotations
from typing import Optional, Set


class MorphologyAnalyzer:
    """Penganalisis morfologi Bahasa Melayu PRPM dan Bahasa Inggris."""

    def __init__(self, prpm_roots: Set[str], english_roots: Set[str]) -> None:
        self.prpm_roots = prpm_roots
        self.english_roots = english_roots

    # ========================================================================
    # 1. VALIDATOR MORFOLOGI BAHASA MELAYU (TATABAHASA DEWAN / PRPM)
    # ========================================================================
    def is_valid_malay_word(self, word: str) -> bool:
        """Memeriksa apakah kata merupakan kata dasar atau kata terbitan Bahasa Melayu yang sah."""
        w = word.lower().strip()
        if not w:
            return False

        # Cek langsung di leksikon PRPM
        if w in self.prpm_roots:
            return True

        # Cek kata ganda (contoh: kanak-kanak, buku-buku, berlari-lari, sayur-mayur)
        if "-" in w:
            parts = w.split("-")
            if len(parts) == 2 and parts[0] and parts[1]:
                if parts[0] == parts[1] and self.is_valid_malay_word(parts[0]):
                    return True
                if self.is_valid_malay_word(parts[0]) or self.is_valid_malay_word(parts[1]):
                    return True

        # Kupas partikel (-lah, -kah, -tah) dan kata ganti milik (-ku, -mu, -nya)
        candidates = {w}
        for clitic in ("lah", "kah", "tah"):
            if w.endswith(clitic) and len(w) > len(clitic) + 2:
                candidates.add(w[: -len(clitic)])

        for cand in list(candidates):
            for pron in ("nya", "ku", "mu"):
                if cand.endswith(pron) and len(cand) > len(pron) + 2:
                    candidates.add(cand[: -len(pron)])

        for cand in candidates:
            if cand in self.prpm_roots:
                return True
            if self._check_malay_affixes(cand):
                return True

        return False

    def _check_malay_affixes(self, word: str) -> bool:
        """Memeriksa kombinasi imbuhan awalan dan akhiran Bahasa Melayu."""
        # Kupas akhiran (-kan, -an, -i)
        stem_candidates = {word}
        for suf in ("kan", "an", "i"):
            if word.endswith(suf) and len(word) > len(suf) + 2:
                base = word[: -len(suf)]
                stem_candidates.add(base)
                # Jika double suffix seperti -kannya sudah dikupas sebelumnya, cek juga kombinasi -kan/-i
                if suf == "kan" and base.endswith("i") and len(base) > 3:
                    stem_candidates.add(base[:-1])

        for cand in stem_candidates:
            if cand in self.prpm_roots:
                return True
            if self._strip_malay_prefixes(cand):
                return True

        return False

    def _strip_malay_prefixes(self, word: str) -> bool:
        """Mengupas awalan Bahasa Melayu (termasuk peluluhan KPST) dan mengecek kata dasar."""
        # Awalan tanpa peluluhan
        simple_prefixes = (
            "memper", "diper", "ber", "be", "ter", "te", "per", "pe",
            "di", "ke", "se", "ku", "kau", "mahasis", "pra", "pasca", "sub", "anti", "pro", "dw", "eka"
        )
        for pref in simple_prefixes:
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots:
                    return True
                # Lapis kedua awalan (mis. keber- -> ke + ber, sepen- -> se + pen)
                for sub_pref in ("ber", "ter", "per", "pe"):
                    if rest.startswith(sub_pref) and rest[len(sub_pref):] in self.prpm_roots:
                        return True

        # Awalan sengau (meN- / peN-) beserta hukum peluluhan KPST
        # 1. menge- / penge- (untuk kata dasar 1 suku kata: cat -> mengecat, sah -> mengesahkan, pos -> mengepos)
        for pref in ("menge", "penge"):
            if word.startswith(pref) and len(word) > len(pref) + 1:
                rest = word[len(pref):]
                if rest in self.prpm_roots:
                    return True

        # 2. meng- / peng- (vokal, g, h, kh, atau peluluhan 'k')
        for pref in ("meng", "peng"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots or ("k" + rest) in self.prpm_roots:
                    return True

        # 3. meny- / peny- (peluluhan 's')
        for pref in ("meny", "peny"):
            if word.startswith(pref) and len(word) > len(pref) + 1:
                rest = word[len(pref):]
                if ("s" + rest) in self.prpm_roots or rest in self.prpm_roots:
                    return True

        # 4. mem- / pem- (b, f, v, atau peluluhan 'p')
        for pref in ("mem", "pem"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots or ("p" + rest) in self.prpm_roots or ("f" + rest) in self.prpm_roots:
                    return True

        # 5. men- / pen- (c, d, j, sy, z, atau peluluhan 't')
        for pref in ("men", "pen"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots or ("t" + rest) in self.prpm_roots:
                    return True

        # 6. me- / pe- (l, m, n, ng, ny, r, w, y)
        for pref in ("me", "pe"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots:
                    return True

        return False

    # ========================================================================
    # 2. VALIDATOR MORFOLOGI BAHASA INGGRIS (UNTUK BYPASS KATA INGGRIS)
    # ========================================================================
    def is_valid_english_word(self, word: str) -> bool:
        """
        Memeriksa apakah kata merupakan kata Bahasa Inggris (dasar maupun berinfleksi).
        Jika ya, kata ini akan dipertahankan (tidak diganti).
        """
        w = word.lower().strip()
        if not w:
            return False

        # Kontraksi umum Bahasa Inggris (don't, can't, I'm, we're, it's, dll.)
        if "'" in w:
            contractions = {
                "don't", "doesn't", "didn't", "can't", "cannot", "couldn't",
                "won't", "wouldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't",
                "haven't", "hasn't", "hadn't", "i'm", "you're", "we're", "they're",
                "it's", "that's", "there's", "what's", "let's", "i've", "i'll", "i'd",
            }
            if w in contractions:
                return True
            if w.endswith("'s") and self.is_valid_english_word(w[:-2]):
                return True

        if w in self.english_roots:
            return True

        # Kata berhubung strip Bahasa Inggris (contoh: follow-up, check-in, full-time, up-to-date)
        if "-" in w:
            parts = [p for p in w.split("-") if p]
            if len(parts) >= 2 and all(self.is_valid_english_word(p) for p in parts):
                return True

        # Cek infleksi akhiran Bahasa Inggris (-s, -es, -ies, -ed, -ied, -ing, -er, -est, -ly, -ness, -ment, -able)
        if self._check_english_inflections(w):
            return True

        # Cek awalan Bahasa Inggris (un-, re-, pre-, dis-, mis-, non-, over-, under-, out-, co-, sub-)
        for pref in ("un", "re", "pre", "dis", "mis", "non", "over", "under", "out", "sub", "inter", "super", "auto"):
            if w.startswith(pref) and len(w) > len(pref) + 2:
                rest = w[len(pref):]
                if rest in self.english_roots or self._check_english_inflections(rest):
                    return True

        return False

    def _check_english_inflections(self, w: str) -> bool:
        """Memeriksa apakah kata dengan akhiran infleksi Inggris berasal dari kata dasar Inggris."""
        # -ies -> -y (studies -> study, companies -> company)
        if w.endswith("ies") and len(w) > 4:
            if (w[:-3] + "y") in self.english_roots:
                return True

        # -ied -> -y (studied -> study, applied -> apply)
        if w.endswith("ied") and len(w) > 4:
            if (w[:-3] + "y") in self.english_roots:
                return True

        # -es (boxes -> box, watches -> watch, goes -> go, changes -> change)
        if w.endswith("es") and len(w) > 3:
            if w[:-2] in self.english_roots or w[:-1] in self.english_roots:
                return True

        # -s (meetings -> meeting, checks -> check, files -> file)
        if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            if w[:-1] in self.english_roots:
                return True
            if self._check_english_inflections(w[:-1]):
                return True

        # -ing (meeting -> meet, running -> run, making -> make, cancelling -> cancel)
        if w.endswith("ing") and len(w) > 4:
            stem = w[:-3]
            if stem in self.english_roots or (stem + "e") in self.english_roots:
                return True
            if len(stem) >= 2 and stem[-1] == stem[-2] and stem[:-1] in self.english_roots:
                return True

        # -ed (checked -> check, updated -> update, stopped -> stop, cancelled -> cancel)
        if w.endswith("ed") and len(w) > 3:
            stem = w[:-2]
            if stem in self.english_roots or (stem + "e") in self.english_roots or w[:-1] in self.english_roots:
                return True
            if len(stem) >= 2 and stem[-1] == stem[-2] and stem[:-1] in self.english_roots:
                return True

        # -ly, -er, -est, -ness, -ment, -able, -ful, -less
        for suf in ("ly", "er", "est", "ness", "ment", "able", "ful", "less"):
            if w.endswith(suf) and len(w) > len(suf) + 2:
                stem = w[: -len(suf)]
                if stem in self.english_roots or (stem + "e") in self.english_roots:
                    return True
                if stem.endswith("i") and (stem[:-1] + "y") in self.english_roots:
                    return True
                if len(stem) >= 2 and stem[-1] == stem[-2] and stem[:-1] in self.english_roots:
                    return True

        return False
