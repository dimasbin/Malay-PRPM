"""
Pengujian Otomatis Komprehensif (Unit & Integration Tests) untuk Aplikasi Pengecek &
Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) Full Offline.
"""

import unittest
from app.engine.pipeline import PRPMPipeline


class TestNumberConverter(unittest.TestCase):
    """Pengujian konversi angka ke kalimat terbilang baku PRPM & mode delapan."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline_baku = PRPMPipeline(eight_word="lapan")
        cls.pipeline_delapan = PRPMPipeline(eight_word="delapan")

    def test_1000_and_800_baku_vs_delapan(self) -> None:
        inp = "harga laptop itu 1000 ringgit dan ada 800 unit yang sudah sold out"
        self.assertEqual(
            self.pipeline_baku.process(inp).corrected_text,
            "Harga laptop itu seribu ringgit dan ada lapan ratus unit yang sudah sold out.",
        )
        self.assertEqual(
            self.pipeline_delapan.process(inp).corrected_text,
            "Harga laptop itu seribu ringgit dan ada delapan ratus unit yang sudah sold out.",
        )

    def test_zero_units_teens_and_tens(self) -> None:
        self.assertEqual(
            self.pipeline_baku.process("baki wang hanya 0 ringgit").corrected_text,
            "Baki wang hanya sifar ringgit.",
        )
        self.assertEqual(
            self.pipeline_baku.process("ada 11 orang dan 19 buah kerusi").corrected_text,
            "Ada sebelas orang dan sembilan belas buah kerusi.",
        )

    def test_hundreds_thousands_millions_with_separators(self) -> None:
        self.assertEqual(
            self.pipeline_baku.process("jumlahnya 1,000 unit").corrected_text,
            "Jumlahnya seribu unit.",
        )
        self.assertEqual(
            self.pipeline_baku.process("peruntukan sebanyak 2,500,000 ringgit").corrected_text,
            "Peruntukan sebanyak dua juta lima ratus ribu ringgit.",
        )
        self.assertEqual(
            self.pipeline_baku.process("jumlah penduduk mencecah 1,000,000,000 orang").corrected_text,
            "Jumlah penduduk mencecah satu bilion orang.",
        )

    def test_sentence_starting_with_number(self) -> None:
        self.assertEqual(
            self.pipeline_baku.process("1000 orang hadir ke majlis itu").corrected_text,
            "Seribu orang hadir ke majlis itu.",
        )

    def test_ordinal_and_decimal_numbers(self) -> None:
        self.assertEqual(
            self.pipeline_baku.process("mesyuarat ke-1 dan ke-2 berlangsung selama 3.5 jam").corrected_text,
            "Mesyuarat pertama dan kedua berlangsung selama tiga perpuluhan lima jam.",
        )
        self.assertEqual(
            self.pipeline_baku.process("kadar inflasi meningkat kepada 12.05 peratus").corrected_text,
            "Kadar inflasi meningkat kepada dua belas perpuluhan sifar lima peratus.",
        )

    def test_rm_currency_negative_percent_and_combined_thousands_decimal(self) -> None:
        inp = "suhu hari ini -5 darjah celsius dan harganya RM1000 atau RM 1,250.50 atau RM500.00 dengan diskaun 20%"
        res = self.pipeline_baku.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Suhu hari ini negatif lima darjah celsius dan harganya RM seribu atau "
            "RM seribu dua ratus lima puluh perpuluhan lima sifar atau RM lima ratus "
            "dengan diskaun dua puluh peratus.",
        )


class TestPRPMStandardizationAndMorphology(unittest.TestCase):
    """Pengujian pembakuan kata PRPM Malaysia, kata majmuk, morfologi, dan pembetulan ejaan."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = PRPMPipeline(eight_word="lapan", mode="annotation")
        cls.pipeline_baku = PRPMPipeline(eight_word="lapan", mode="baku")

    def test_slang_and_sms_abbreviations_to_prpm_baku_mode(self) -> None:
        inp = "korang nak pergi kat pejabat skrg ke , sbb dgn jadual baru ni diorang takde masa."
        res = self.pipeline_baku.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Kamu semua hendak pergi di pejabat sekarang ke, sebab dengan jadual baru ini mereka tiada masa.",
        )

    def test_non_standard_variants_to_prpm_malaysia(self) -> None:
        inp = "saya paham mengapa mereka pikir analisa jadual di kantor itu berbeda"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya faham mengapa mereka fikir analisis jadual di pejabat itu berbeza.",
        )

    def test_clitics_attached_to_non_standard_stems(self) -> None:
        inp = "jawabannya sangat jelas dan perlu dicoba sekarang"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Jawapannya sangat jelas dan perlu dicuba sekarang.",
        )

    def test_kata_majmuk_mantap_dbp(self) -> None:
        inp = (
            "pada hari isnin , mereka Pergi ke kuala lumpur untuk beri tahu jawatan kuasa "
            "tentang kerja sama dan tanda tangan surat warga negara"
        )
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Pada hari Isnin, mereka pergi ke Kuala Lumpur untuk beritahu jawatankuasa "
            "tentang kerjasama dan tandatangan surat warganegara.",
        )

    def test_kata_majmuk_terpisah_prpm(self) -> None:
        inp = "terimakasih kerana membuat kemaskini katalaluan dan muatturun borang temuduga"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Terima kasih kerana membuat kemas kini kata laluan dan muat turun borang temu duga.",
        )

    def test_valid_malay_morphology_and_reduplication_preserved(self) -> None:
        inp = "Kanak-kanak itu sedang membaca buku dan menyemak keputusan peperiksaan."
        res = self.pipeline.process(inp)
        self.assertEqual(res.corrected_text, inp)
        self.assertTrue(res.is_valid_without_changes)

    def test_prpm_typo_correction_damerau_levenshtein(self) -> None:
        inp = "pegawai itu berada di pejabta untuk menyemak dokumn"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Pegawai itu berada di pejabat untuk menyemak dokumen.",
        )

    def test_daily_words_not_corrupted_by_typo_checker(self) -> None:
        inp = "saya hendak balik rumah kerana lapar dan penat serta dia cakap semua benda ok"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya hendak balik rumah kerana lapar dan penat serta dia cakap semua benda ok.",
        )

    def test_basahan_sikit_ngam_kompeni_and_di_ke_prepositions(self) -> None:
        inp = "sikit sahaja wang di kompeni itu yang ngam untuk kerja disini bukan disana"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Sedikit sahaja wang di syarikat itu yang sesuai untuk kerja di sini bukan di sana.",
        )

    def test_contextual_pasal_and_boleh_tak(self) -> None:
        self.assertEqual(
            self.pipeline.process("saya nak tanya pasal projek tu boleh tak").corrected_text,
            "Saya nak tanya tentang projek tu boleh tak?",
        )
        self.assertEqual(
            self.pipeline_baku.process("saya nak tanya pasal projek tu boleh tak").corrected_text,
            "Saya hendak tanya tentang projek itu boleh atau tidak?",
        )
        self.assertEqual(
            self.pipeline.process("pasal dia sakit, dia tidak hadir ke pejabat").corrected_text,
            "Kerana dia sakit, dia tidak hadir ke pejabat.",
        )

    def test_kpst_assimilation_corrections_and_exceptions(self) -> None:
        inp = "dia cuba memparkir dan mensokong serta mentulis dan mengkira kos untuk memproses data"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Dia cuba memarkir dan menyokong serta menulis dan mengira kos untuk memproses data.",
        )

    def test_unknown_word_reported_without_forced_change(self) -> None:
        inp = "dia ngamak di pejabat"
        res = self.pipeline.process(inp)
        self.assertEqual(res.corrected_text, "Dia ngamak di pejabat.")
        self.assertIn("ngamak", [u.word for u in res.unknown_words])


class TestEnglishPreservation(unittest.TestCase):
    """Pengujian pengenalan kata campuran Bahasa Inggris agar TIDAK diganti."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = PRPMPipeline(eight_word="lapan", mode="annotation")
        cls.pipeline_baku = PRPMPipeline(eight_word="lapan", mode="baku")

    def test_english_words_and_inflections_preserved(self) -> None:
        inp = "saya nak join meetings di office dan check updated attachments yang sudah uploaded semalam"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya nak join meetings di office dan check updated attachments yang sudah uploaded semalam.",
        )
        res_baku = self.pipeline_baku.process(inp)
        self.assertEqual(
            res_baku.corrected_text,
            "Saya hendak join meetings di office dan check updated attachments yang sudah uploaded semalam.",
        )
        for en_word in ("join", "meetings", "office", "check", "updated", "attachments", "uploaded"):
            self.assertIn(en_word, res.english_words_preserved)

    def test_english_hyphenated_and_contractions_preserved(self) -> None:
        inp = "kita buat follow-up esok kerana it's urgent dan we're ready untuk check-in"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Kita buat follow-up esok kerana it's urgent dan we're ready untuk check-in.",
        )

    def test_english_mid_sentence_capitalization_normalized_without_translation(self) -> None:
        inp = "Mereka Sedang Check Document Penting Di Pejabat."
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Mereka sedang check document penting di pejabat.",
        )
        self.assertIn("Check", res.english_words_preserved)
        self.assertIn("Document", res.english_words_preserved)


class TestPunctuationChecker(unittest.TestCase):
    """Pengujian tanda baca titik (.), koma (,), dan tanda tanya (?)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = PRPMPipeline(eight_word="lapan", mode="annotation")
        cls.pipeline_baku = PRPMPipeline(eight_word="lapan", mode="baku")

    def test_spacing_around_comma_and_period(self) -> None:
        inp = "saya beli buku ,pena ,dan kertas   di kedai"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya beli buku, pena, dan kertas di kedai.",
        )

    def test_double_punctuation_and_interrogative_detection(self) -> None:
        inp = "kenapa korang masih tak paham document yang saya upload semalam.."
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Mengapa kamu semua masih tak faham document yang saya upload semalam?",
        )
        res_baku = self.pipeline_baku.process(inp)
        self.assertEqual(
            res_baku.corrected_text,
            "Mengapa kamu semua masih tidak faham document yang saya upload semalam?",
        )

    def test_particle_kah_question_mark(self) -> None:
        self.assertEqual(
            self.pipeline.process("sudahkah anda menyemak jadual baru itu.").corrected_text,
            "Sudahkah anda menyemak jadual baru itu?",
        )
        self.assertEqual(
            self.pipeline.process("bolehkah kita mulakan meeting sekarang").corrected_text,
            "Bolehkah kita mulakan meeting sekarang?",
        )

    def test_indirect_question_word_stays_declarative_period(self) -> None:
        inp = "saya tidak tahu mengapa mereka lewat hari ini"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya tidak tahu mengapa mereka lewat hari ini.",
        )

    def test_multi_sentence_mixed_statement_and_question(self) -> None:
        inp = "saya sudah sampai di pejabat , tetapi bilik masih tutup. bilakah meeting akan bermula."
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya sudah sampai di pejabat, tetapi bilik masih tutup. Bilakah meeting akan bermula?",
        )

    def test_indirect_di_mana_stays_declarative_and_direct_becomes_question(self) -> None:
        self.assertEqual(
            self.pipeline.process("saya tidak tahu di mana pejabat baru itu").corrected_text,
            "Saya tidak tahu di mana pejabat baru itu.",
        )
        self.assertEqual(
            self.pipeline.process("di mana pejabat baru itu").corrected_text,
            "Di mana pejabat baru itu?",
        )

    def test_ellipsis_and_title_abbreviation_dot(self) -> None:
        inp = "saya hendak jumpa Dr. Ahmad nanti..."
        res = self.pipeline.process(inp)
        self.assertEqual(res.corrected_text, "Saya hendak jumpa Dr. Ahmad nanti...")


class TestCapitalizationChecker(unittest.TestCase):
    """Pengujian huruf kapital dan non-kapital."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = PRPMPipeline(eight_word="lapan", mode="annotation")
        cls.pipeline_baku = PRPMPipeline(eight_word="lapan", mode="baku")

    def test_proper_nouns_and_acronyms(self) -> None:
        inp = "kami memerlukan 25 orang sukarelawan untuk program kemaskini data prpm di universitas malaysia"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Kami memerlukan dua puluh lima orang sukarelawan untuk program kemas kini data PRPM di universiti Malaysia.",
        )

    def test_multi_word_proper_nouns_and_months_days(self) -> None:
        inp = "pada bulan januari nanti , kami bercuti ke pulau pinang dan kota kinabalu pada hari jumaat"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Pada bulan Januari nanti, kami bercuti ke Pulau Pinang dan Kota Kinabalu pada hari Jumaat.",
        )

    def test_acronym_vs_lowercase_english_word_it(self) -> None:
        inp = "jabatan IT dan DBP mengesahkan it works dengan bajet RM 500"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Jabatan IT dan DBP mengesahkan it works dengan bajet RM lima ratus.",
        )

    def test_english_pronoun_i_and_contraction_preserved(self) -> None:
        inp = "sebenarnya I'm happy kerana I sudah selesai review report"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Sebenarnya I'm happy kerana I sudah selesai review report.",
        )

    def test_brands_names_titles_and_lowercase_i_contraction(self) -> None:
        inp = "i'm going to meet Dr. Ahmad dan Encik Zulfaqar pakai Google Chrome dan WhatsApp di office"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "I'm going to meet Dr. Ahmad dan Encik Zulfaqar pakai Google Chrome dan WhatsApp di office.",
        )

    def test_bin_binti_and_common_encik_puan(self) -> None:
        inp = "Muhammad Bin Abdullah bekerja dengan puan itu di Cyberjaya"
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Muhammad bin Abdullah bekerja dengan puan itu di Cyberjaya.",
        )


class TestEndToEndScenarios(unittest.TestCase):
    """Pengujian skenario gabungan lengkap dan kondisi batas (edge cases)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = PRPMPipeline(eight_word="lapan", mode="annotation")
        cls.pipeline_baku = PRPMPipeline(eight_word="lapan", mode="baku")

    def test_full_complex_mixed_sentence(self) -> None:
        inp = (
            "saya nak join meeting itu di kuala lumpur pada pukul 8 pagi , "
            "apakah jadual dan 1000 unit laptop sudah ready."
        )
        res = self.pipeline.process(inp)
        self.assertEqual(
            res.corrected_text,
            "Saya nak join meeting itu di Kuala Lumpur pada pukul lapan pagi, "
            "apakah jadual dan seribu unit laptop sudah ready?",
        )
        res_baku = PRPMPipeline(eight_word="lapan", mode="baku").process(inp)
        self.assertEqual(
            res_baku.corrected_text,
            "Saya hendak join meeting itu di Kuala Lumpur pada pukul lapan pagi, "
            "apakah jadual dan seribu unit laptop sudah ready?",
        )

    def test_empty_and_whitespace_input(self) -> None:
        res_empty = self.pipeline.process("")
        self.assertEqual(res_empty.corrected_text, "")
        self.assertTrue(res_empty.is_valid_without_changes)

        res_ws = self.pipeline.process("   ")
        self.assertEqual(res_ws.corrected_text, "   ")
        self.assertTrue(res_ws.is_valid_without_changes)


class TestPMAnnotationRules(unittest.TestCase):
    """Pengujian peraturan rasmi PM dari dokumen Customer Service Long Audio Annotation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = PRPMPipeline(eight_word="lapan", mode="annotation")

    def test_group1_spoken_words_kept_as_spoken(self) -> None:
        cases = [
            ("saya tak tahu", "Saya tak tahu."),
            ("satu je", "Satu je."),
            ("saya nak tanya", "Saya nak tanya."),
            ("kat sini ada", "Kat sini ada."),
            ("tunggu jap", "Tunggu jap."),
            ("pastu saya call balik", "Pastu saya call balik."),
            ("boleh kot", "Boleh kot."),
            ("polisi ni okey. income tu penting", "Polisi ni okey. Income tu penting."),
            ("dah bayar", "Dah bayar."),
            ("duduk sorang", "Duduk sorang."),
            ("tak sure lah", "Tak sure lah."),
        ]
        for inp, expected in cases:
            res = self.pipeline.process(inp)
            self.assertEqual(res.corrected_text, expected)
            self.assertEqual(res.unknown_words, [], f"Unexpected unknown_words for: {inp}")

    def test_group2_accent_differences_standardized(self) -> None:
        cases = [
            ("ade , tapi tak banyak", "Ada, tapi tak banyak."),
            ("saye nak tanya", "Saya nak tanya."),
            ("ape yang boleh saye bantu.", "Apa yang boleh saya bantu?"),
            ("kite tengok dulu", "Kita tengok dulu."),
            ("kena ambik dulu", "Kena ambil dulu."),
            ("nanti saye balek", "Nanti saya balik."),
            ("he is flying a kite", "He is flying a kite."),
        ]
        for inp, expected in cases:
            self.assertEqual(self.pipeline.process(inp).corrected_text, expected)

    def test_overlap_tag_rules_spacing_and_punctuation(self) -> None:
        # 1. Valid tanpa tanda baca
        r1 = self.pipeline.process("I go to [OVERLAP/]school[/OVERLAP] today.")
        self.assertEqual(r1.corrected_text, "I go to [OVERLAP/]school[/OVERLAP] today.")
        self.assertTrue(r1.is_valid_without_changes)

        # 2. Valid dengan tanda baca di dalam tag
        r2 = self.pipeline.process("I go to school [OVERLAP/]today.[/OVERLAP]")
        self.assertEqual(r2.corrected_text, "I go to school [OVERLAP/]today.[/OVERLAP]")
        self.assertTrue(r2.is_valid_without_changes)

        # 3. Salah spasi di dalam tag -> dibersihkan
        r3 = self.pipeline.process("I go to [OVERLAP/] school [/OVERLAP] today.")
        self.assertEqual(r3.corrected_text, "I go to [OVERLAP/]school[/OVERLAP] today.")

        # 4. Salah tanda baca di luar tag -> dimasukkan ke dalam tag
        r4 = self.pipeline.process("I go to school [OVERLAP/]today[/OVERLAP].")
        self.assertEqual(r4.corrected_text, "I go to school [OVERLAP/]today.[/OVERLAP]")

        # 5. Contoh Melayu + penambahan titik otomatis ke dalam tag penutup
        r5 = self.pipeline.process("saya mahu menyemak baki [OVERLAP/]akaun saya[/OVERLAP]")
        self.assertEqual(
            r5.corrected_text,
            "Saya mahu menyemak baki [OVERLAP/]akaun saya.[/OVERLAP]",
        )

        # 6. Ayat tanya diakhiri tag overlap + kalimat sambungan selepas [/OVERLAP]
        r6 = self.pipeline.process("apakah [OVERLAP/]baki akaun saya[/OVERLAP]. terima kasih")
        self.assertEqual(
            r6.corrected_text,
            "Apakah [OVERLAP/]baki akaun saya?[/OVERLAP] Terima kasih.",
        )

        # 7. Kapitalisasi awal kalimat di dalam [OVERLAP/]
        r7 = self.pipeline.process("[OVERLAP/]saya[/OVERLAP] nak tanya")
        self.assertEqual(r7.corrected_text, "[OVERLAP/]Saya[/OVERLAP] nak tanya.")


if __name__ == "__main__":
    unittest.main()
