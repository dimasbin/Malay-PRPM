"""
Modul Analisis Morfologi Bahasa Melayu (PRPM DBP) & Infleksi Bahasa Inggris.
Digunakan untuk:
1. Memvalidasi kata berimbuhan Bahasa Melayu (awalan, akhiran, apitan, partikel, kata ganda)
   berdasarkan Hukum Peluluhan KPST Tatabahasa Dewan / PRPM.
2. Mendeteksi & mengoreksi kesalahan peluluhan KPST (mis. memparkir -> memarkir, mensokong -> menyokong).
3. Mengenali kata Bahasa Inggris berimbuhan (-s, -es, -ed, -ing, -ly, un-, re-, dll.)
   agar kata campuran Bahasa Inggris tetap dipertahankan dan tidak dianggap salah eja.
"""

from __future__ import annotations
from typing import Optional, Set, Tuple


class MorphologyAnalyzer:
    """Penganalisis morfologi Bahasa Melayu PRPM dan Bahasa Inggris."""

    # Pengecualian rasmi PRPM/DBP bagi kata dasar berawalan k, p, s, t yang tidak luluh
    _K_NON_DROP_STEMS = {"kaji"}
    _P_NON_DROP_STEMS = {"punyai", "pelawa", "pelbagai", "pelajar"}
    _T_NON_DROP_STEMS = {"tadbir", "tafsir", "terjemah", "takrif", "takluk", "taksir", "tertawa"}

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
                if suf == "kan" and base.endswith("i") and len(base) > 3:
                    stem_candidates.add(base[:-1])

        for cand in stem_candidates:
            if cand in self.prpm_roots:
                return True
            if self._strip_malay_prefixes(cand):
                return True

        return False

    def _can_keep_k(self, rest: str) -> bool:
        return (
            rest in self._K_NON_DROP_STEMS
            or rest.startswith(("kh", "kr", "kl", "ks", "kt", "kw"))
        )

    def _can_keep_s(self, rest: str) -> bool:
        return rest.startswith(("sy", "st", "sk", "sp", "sl", "sm", "sn", "sr", "sw"))

    def _can_keep_p(self, rest: str) -> bool:
        return (
            rest in self._P_NON_DROP_STEMS
            or rest.startswith(("pr", "pl", "ps", "pt"))
        )

    def _can_keep_t(self, rest: str) -> bool:
        return (
            rest in self._T_NON_DROP_STEMS
            or rest.startswith(("tr", "ts", "tw"))
        )

    def _strip_malay_prefixes(self, word: str) -> bool:
        """Mengupas awalan Bahasa Melayu mengikut hukum peluluhan KPST Tatabahasa Dewan."""
        # Awalan tanpa peluluhan
        simple_prefixes = (
            "memper", "diper", "ber", "be", "ter", "te", "per", "pe",
            "di", "ke", "se", "ku", "kau", "pra", "pasca", "sub", "anti", "pro", "dwi", "eka",
        )
        for pref in simple_prefixes:
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots:
                    return True
                for sub_pref in ("ber", "ter", "per", "pe"):
                    if rest.startswith(sub_pref) and rest[len(sub_pref):] in self.prpm_roots:
                        return True

        # 1. menge- / penge- (kata dasar 1 suku kata: cat -> mengecat, sah -> mengesahkan, pos -> mengepos)
        for pref in ("menge", "penge"):
            if word.startswith(pref) and len(word) > len(pref) + 1:
                rest = word[len(pref):]
                if rest in self.prpm_roots:
                    return True

        # 2. meng- / peng- (vokal, g, h, atau peluluhan 'k'; 'k' kekal hanya pada gugus konsonan/pengecualian)
        for pref in ("meng", "peng"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if ("k" + rest) in self.prpm_roots:
                    return True
                if rest in self.prpm_roots:
                    if not rest.startswith("k") or self._can_keep_k(rest):
                        return True

        # 3. meny- / peny- (peluluhan 's')
        for pref in ("meny", "peny"):
            if word.startswith(pref) and len(word) > len(pref) + 1:
                rest = word[len(pref):]
                if ("s" + rest) in self.prpm_roots:
                    return True
                if rest in self.prpm_roots and not rest.startswith("s"):
                    return True

        # 4. mem- / pem- (b, f, v, atau peluluhan 'p'; 'p' kekal hanya pada gugus konsonan/pengecualian)
        for pref in ("mem", "pem"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if ("p" + rest) in self.prpm_roots or ("f" + rest) in self.prpm_roots:
                    return True
                if rest in self.prpm_roots:
                    if not rest.startswith("p") or self._can_keep_p(rest):
                        return True

        # 5. men- / pen- (c, d, j, sy, z, atau peluluhan 't'; 's'/'t' kekal hanya pada gugus konsonan/pengecualian)
        for pref in ("men", "pen"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if ("t" + rest) in self.prpm_roots:
                    return True
                if rest in self.prpm_roots:
                    if rest.startswith("s") and not self._can_keep_s(rest):
                        return False
                    if rest.startswith("t") and not self._can_keep_t(rest):
                        return False
                    return True

        # 6. me- / pe- (l, m, n, ng, ny, r, w, y)
        for pref in ("me", "pe"):
            if word.startswith(pref) and len(word) > len(pref) + 2:
                rest = word[len(pref):]
                if rest in self.prpm_roots:
                    return True

        return False

    def suggest_kpst_correction(self, word: str) -> Optional[Tuple[str, str]]:
        """
        Mendeteksi kesalahan peluluhan KPST (seperti mempakai -> memakai, mensokong -> menyokong,
        mentulis -> menulis, mengkira -> mengira) dan mengembalikan bentuk bakunya jika kata dasar sah.
        """
        w = word.lower().strip()
        if not w or len(w) < 6:
            return None

        # Kupas partikel (-lah, -kah, -tah, -nya, -ku, -mu) dan akhiran (-kan, -i, -an) untuk mencari stem
        rules = [
            ("mengk", "meng", "k", self._can_keep_k),
            ("pengk", "peng", "k", self._can_keep_k),
            ("memp", "mem", "p", self._can_keep_p),
            ("pemp", "pem", "p", self._can_keep_p),
            ("mens", "meny", "s", self._can_keep_s),
            ("pens", "peny", "s", self._can_keep_s),
            ("ment", "men", "t", self._can_keep_t),
            ("pent", "pen", "t", self._can_keep_t),
        ]

        for bad_pref, good_pref, kpst_char, keep_fn in rules:
            if w.startswith(bad_pref):
                rest_after_bad = w[len(bad_pref):]
                if len(rest_after_bad) < 2:
                    continue
                full_stem = kpst_char + rest_after_bad
                if keep_fn(full_stem):
                    continue
                if self._has_valid_root_with_suffixes(full_stem):
                    fixed = good_pref + rest_after_bad
                    reason = (
                        f"Mengikut hukum peluluhan KPST PRPM DBP, huruf '{kpst_char}' pada kata dasar "
                        f"wajib luluh apabila menerima imbuhan ('{w}' -> '{fixed}')."
                    )
                    return fixed, reason

        return None

    def _has_valid_root_with_suffixes(self, stem: str) -> bool:
        """Memeriksa apakah stem (termasuk kemungkinan akhiran -kan/-i/-an/-nya) berakar pada prpm_roots."""
        candidates = {stem}
        for clitic in ("lah", "kah", "tah", "nya", "ku", "mu"):
            if stem.endswith(clitic) and len(stem) > len(clitic) + 3:
                candidates.add(stem[: -len(clitic)])

        for cand in list(candidates):
            for suf in ("kan", "an", "i"):
                if cand.endswith(suf) and len(cand) > len(suf) + 2:
                    candidates.add(cand[: -len(suf)])

        return any(c in self.prpm_roots for c in candidates)

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
