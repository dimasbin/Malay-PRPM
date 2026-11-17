"""
Pengujian End-to-End untuk Antarmuka CLI (prpm_cli.py):
- Eksekusi kalimat tunggal (-q dan --json)
- Opsi --eight lapan vs --eight delapan
- Mode batch --file dan --output
- Penanganan file tidak ditemukan (exit code 1)
- Penambahan kosakata ke database SQLite sementara (tanpa mengubah DB produksi)
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from app.data.lexicon_sync import import_proper_nouns_from_file, import_wordlist_file
from app.data.seed_lexicon import init_database, upgrade_seed_database
from app.engine.pipeline import PRPMPipeline

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_SCRIPT = os.path.join(PROJECT_ROOT, "prpm_cli.py")


class TestPRPMCLI(unittest.TestCase):
    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, CLI_SCRIPT, *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_cli_single_sentence_quiet(self) -> None:
        proc = self._run_cli(
            [
                "saya nak join meeting itu pada pukul 8 pagi , apakah jadual sudah ready.",
                "-q",
            ]
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            proc.stdout.strip(),
            "Saya hendak join meeting itu pada pukul lapan pagi, apakah jadual sudah ready?",
        )

    def test_cli_eight_delapan_flag(self) -> None:
        proc = self._run_cli(
            [
                "--eight",
                "delapan",
                "ada 800 unit dan 1000 buah buku",
                "-q",
            ]
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            proc.stdout.strip(),
            "Ada delapan ratus unit dan seribu buah buku.",
        )

    def test_cli_json_output(self) -> None:
        proc = self._run_cli(
            [
                "harga barang itu 1000 ringgit dan ada 800 unit",
                "--json",
            ]
        )
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(
            data["corrected_text"],
            "Harga barang itu seribu ringgit dan ada lapan ratus unit.",
        )
        self.assertFalse(data["is_valid_without_changes"])
        self.assertGreaterEqual(len(data["corrections"]), 3)

    def test_cli_batch_file_to_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "input.txt")
            out_path = os.path.join(tmpdir, "output.txt")
            with open(in_path, "w", encoding="utf-8") as f:
                f.write("saya nak check email sekarang\n")
                f.write("apakah jumlahnya 800 unit.\n")

            proc = self._run_cli(["--file", in_path, "--output", out_path])
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(os.path.exists(out_path))

            with open(out_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]

            self.assertEqual(
                lines,
                [
                    "Saya hendak check email sekarang.",
                    "Apakah jumlahnya lapan ratus unit?",
                ],
            )

    def test_cli_missing_file_returns_nonzero(self) -> None:
        proc = self._run_cli(["--file", "tidak_wujud_12345.txt"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("tidak ditemukan", proc.stderr)

    def test_isolated_db_custom_word_additions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = os.path.join(tmpdir, "test_prpm.db")
            init_database(temp_db, force_rebuild=True)
            pipeline = PRPMPipeline(db_path=temp_db, eight_word="lapan")

            # Tambah aturan pembakuan kustom, kata baku PRPM baru, dan kata Inggris baru
            pipeline.lexicon_checker.add_prpm_word("belanjawan")
            pipeline.lexicon_checker.add_standardization_rule(
                "bajet",
                "belanjawan",
                "Pembakuan kustom: 'bajet' -> 'belanjawan'.",
            )
            pipeline.lexicon_checker.add_english_word("kubernetes")

            res = pipeline.process("saya nak semak bajet server kubernetes untuk 1000 pengguna")
            self.assertEqual(
                res.corrected_text,
                "Saya hendak semak belanjawan server kubernetes untuk seribu pengguna.",
            )
            self.assertIn("kubernetes", res.english_words_preserved)

    def test_cli_stats_flag(self) -> None:
        proc = self._run_cli(["--stats"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("prpm_words", proc.stdout)

    def test_isolated_dic_import_and_upgrade_preserves_user_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = os.path.join(tmpdir, "sync_test.db")
            dic_path = os.path.join(tmpdir, "sample_ms.dic")
            init_database(temp_db, force_rebuild=True)

            pipeline = PRPMPipeline(db_path=temp_db)
            pipeline.lexicon_checker.add_prpm_word("userkustom")

            with open(dic_path, "w", encoding="utf-8") as f:
                f.write("#4\n")
                f.write("rumah/Dk\n")
                f.write("in\n")
                f.write("sikit\n")
                f.write("Zulfaqar/A\n")

            _, _ = import_wordlist_file(temp_db, dic_path, target="prpm", source="sync")
            _, _ = import_proper_nouns_from_file(temp_db, dic_path, source="sync")
            upgrade_seed_database(temp_db)

            reloaded = PRPMPipeline(db_path=temp_db)
            self.assertIn("userkustom", reloaded.lexicon_checker.prpm_words)
            self.assertNotIn("sikit", reloaded.lexicon_checker.prpm_words)
            self.assertNotIn("in", reloaded.lexicon_checker.prpm_words)
            self.assertIn("zulfaqar", reloaded.lexicon_checker.proper_nouns)


if __name__ == "__main__":
    unittest.main()
