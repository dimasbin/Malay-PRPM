#!/usr/bin/env python3
"""
Aplikasi CLI (Command Line Interface) Full Offline:
Pemeriksa & Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) + Campuran Bahasa Inggris.

Fitur:
1. Pemeriksaan & pembakuan kata berdasarkan PRPM Malaysia (Full Baku).
2. Kata campuran Bahasa Inggris dikenali dan TIDAK DIGANTI (tetap dipertahankan).
3. Konversi angka menjadi kalimat terbilang (1000 -> seribu, 800 -> lapan ratus / delapan ratus).
4. Pemeriksaan tanda baca titik ('.'), koma (','), dan tanda tanya ('?').
5. Pemeriksaan penggunaan huruf kapital dan non-kapital.
"""

from __future__ import annotations
import argparse
import ctypes
import json
import os
import sys
from typing import List

from app.data.seed_lexicon import DB_PATH, init_database
from app.engine.pipeline import PipelineResult, PRPMPipeline


def _enable_windows_ansi() -> None:
    """Mengaktifkan dukungan warna ANSI pada terminal Windows (CMD / PowerShell)."""
    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    except Exception:
        pass


# Kode Warna ANSI Terminal
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RED = "\033[91m"


CATEGORY_BADGES = {
    "PRPM_KATA": f"{Colors.YELLOW}[PRPM KATA BAKU]{Colors.RESET}",
    "PRPM_MAJMUK": f"{Colors.MAGENTA}[PRPM KATA MAJMUK]{Colors.RESET}",
    "PRPM_EJAAN": f"{Colors.RED}[PRPM EJAAN]{Colors.RESET}",
    "ANGKA": f"{Colors.CYAN}[ANGKA -> KALIMAT]{Colors.RESET}",
    "TANDA_BACA": f"{Colors.BLUE}[TITIK/KOMA/TANYA]{Colors.RESET}",
    "KAPITAL": f"{Colors.GREEN}[HURUF KAPITAL]{Colors.RESET}",
}


def print_result(res: PipelineResult, use_color: bool = True) -> None:
    """Menampilkan hasil pemeriksaan kalimat ke layar terminal secara terstruktur."""
    if not use_color:
        print(f"Input Asli     : {res.original_text}")
        print(f"Hasil Baku PRPM: {res.corrected_text}")
        if res.english_words_preserved:
            print(f"Kata Inggris   : {', '.join(res.english_words_preserved)} (Dipertahankan)")
        if res.corrections:
            print("Rincian Koreksi:")
            for idx, c in enumerate(res.corrections, 1):
                print(f"  {idx}. [{c.category}] '{c.original}' -> '{c.replacement}' | {c.reason}")
        else:
            print("Status         : Sudah baku (Tidak ada kesalahan ditemukan).")
        print("-" * 76)
        return

    print(f"\n{Colors.DIM}{'─' * 76}{Colors.RESET}")
    print(f"{Colors.BOLD}Kalimat Input   :{Colors.RESET} {res.original_text}")
    print(
        f"{Colors.BOLD}Hasil Baku PRPM :{Colors.RESET} {Colors.GREEN}{Colors.BOLD}{res.corrected_text}{Colors.RESET}"
    )

    if res.english_words_preserved:
        en_list = ", ".join(res.english_words_preserved)
        print(
            f"{Colors.BOLD}Bahasa Inggris  :{Colors.RESET} {Colors.CYAN}{en_list}{Colors.RESET} "
            f"{Colors.DIM}(Dikenali & dipertahankan tanpa diganti){Colors.RESET}"
        )

    if res.corrections:
        print(
            f"\n{Colors.BOLD}Rincian Pembakuan & Koreksi ({len(res.corrections)} perubahan | {res.processing_time_ms} ms):{Colors.RESET}"
        )
        for idx, c in enumerate(res.corrections, 1):
            badge = CATEGORY_BADGES.get(c.category, f"[{c.category}]")
            print(
                f"  {idx}. {badge} {Colors.RED}'{c.original}'{Colors.RESET} -> "
                f"{Colors.GREEN}'{c.replacement}'{Colors.RESET}"
            )
            print(f"     {Colors.DIM}└─ {c.reason}{Colors.RESET}")
    else:
        print(
            f"\n{Colors.GREEN}✓ Kalimat sudah mematuhi kaidah baku PRPM Malaysia ({res.processing_time_ms} ms).{Colors.RESET}"
        )
    print(f"{Colors.DIM}{'─' * 76}{Colors.RESET}")


DEMO_SENTENCES: List[str] = [
    "saya nak join meeting itu di office pada pukul 8 pagi , apakah jadual sudah ready.",
    "harga laptop itu 1000 ringgit dan ada 800 unit yang sudah sold out",
    "pada hari isnin , mereka Pergi ke kuala lumpur untuk beri tahu jawatan kuasa tentang kerja sama ini",
    "kenapa korang masih tak paham document yang saya upload semalam..",
    "kami memerlukan 25 orang sukarelawan untuk program kemaskini data di universitas malaysia",
]


def run_interactive_repl(pipeline: PRPMPipeline) -> None:
    """Menjalankan mode interaktif (REPL) di terminal."""
    print(f"{Colors.CYAN}{Colors.BOLD}============================================================================{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}   APLIKASI CLI PEMERIKSA & PEMBAKU KALIMAT BAHASA MELAYU (PRPM MALAYSIA)   {Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}                  MODE FULL OFFLINE (CAMPURAN MELAYU-INGGRIS)               {Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}============================================================================{Colors.RESET}")
    print("Panduan Perintah:")
    print(f"  • Ketik kalimat langsung lalu tekan {Colors.BOLD}Enter{Colors.RESET} untuk memeriksa.")
    print(f"  • {Colors.YELLOW}:demo{Colors.RESET}                        -> Jalankan 5 contoh kalimat uji coba.")
    print(f"  • {Colors.YELLOW}:eight lapan|delapan{Colors.RESET}         -> Ubah ejaan angka 8 (aktif: '{pipeline.number_converter.eight_word}').")
    print(f"  • {Colors.YELLOW}:add-prpm <kata>{Colors.RESET}             -> Tambah kata baku PRPM ke kamus lokal.")
    print(f"  • {Colors.YELLOW}:add-baku <tak_baku> <baku>{Colors.RESET}  -> Tambah aturan pembakuan kata ke kamus lokal.")
    print(f"  • {Colors.YELLOW}:add-en <word>{Colors.RESET}               -> Tambah kata Bahasa Inggris ke whitelist.")
    print(f"  • {Colors.YELLOW}:keluar{Colors.RESET} atau {Colors.YELLOW}q{Colors.RESET}               -> Keluar dari aplikasi.\n")

    while True:
        try:
            user_input = input(f"{Colors.BOLD}PRPM>{Colors.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTerima kasih. Aplikasi ditutup.")
            break

        if not user_input:
            continue

        if user_input.lower() in (":keluar", ":exit", ":quit", "q", "exit", "quit"):
            print("Terima kasih. Aplikasi ditutup.")
            break

        if user_input.lower() == ":demo":
            print(f"\n{Colors.CYAN}Menjalankan {len(DEMO_SENTENCES)} kalimat demo...{Colors.RESET}")
            for s in DEMO_SENTENCES:
                res = pipeline.process(s)
                print_result(res)
            continue

        if user_input.lower().startswith(":eight "):
            mode = user_input.split(maxsplit=1)[1].strip().lower()
            if mode in ("lapan", "delapan"):
                pipeline = PRPMPipeline(db_path=DB_PATH, eight_word=mode)
                print(f"{Colors.GREEN}✓ Ejaan angka 8 diatur ke: '{mode}'.{Colors.RESET}")
            else:
                print(f"{Colors.RED}Pilih ':eight lapan' atau ':eight delapan'.{Colors.RESET}")
            continue

        if user_input.lower().startswith(":add-prpm "):
            word = user_input.split(maxsplit=1)[1].strip()
            pipeline.lexicon_checker.add_prpm_word(word)
            print(f"{Colors.GREEN}✓ Kata baku PRPM '{word}' berhasil ditambahkan ke database offline.{Colors.RESET}")
            continue

        if user_input.lower().startswith(":add-baku "):
            parts = user_input.split()
            if len(parts) >= 3:
                non_std = parts[1]
                std_w = " ".join(parts[2:])
                pipeline.lexicon_checker.add_standardization_rule(
                    non_std,
                    std_w,
                    f"Aturan pembakuan pengguna: '{non_std}' -> '{std_w}' mengikut PRPM.",
                )
                print(f"{Colors.GREEN}✓ Aturan pembakuan '{non_std}' -> '{std_w}' berhasil disimpan.{Colors.RESET}")
            else:
                print(f"{Colors.RED}Format: :add-baku <kata_tidak_baku> <kata_baku_prpm>{Colors.RESET}")
            continue

        if user_input.lower().startswith(":add-en "):
            word = user_input.split(maxsplit=1)[1].strip()
            pipeline.lexicon_checker.add_english_word(word)
            print(f"{Colors.GREEN}✓ Kata Bahasa Inggris '{word}' berhasil ditambahkan ke whitelist offline.{Colors.RESET}")
            continue

        res = pipeline.process(user_input)
        print_result(res)


def main() -> int:
    _enable_windows_ansi()

    parser = argparse.ArgumentParser(
        description="Aplikasi CLI Full Offline Pemeriksa & Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) + Campuran Inggris."
    )
    parser.add_argument(
        "sentence",
        nargs="?",
        help="Kalimat yang ingin diperiksa secara langsung. Kosongkan untuk masuk ke mode interaktif.",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Path berkas teks (.txt) berisi daftar kalimat (1 kalimat per baris) untuk diproses secara batch.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path berkas keluaran untuk menyimpan hasil pemrosesan batch.",
    )
    parser.add_argument(
        "--eight",
        choices=["lapan", "delapan"],
        default="lapan",
        help="Pilihan ejaan angka 8: 'lapan' (default Baku PRPM Malaysia) atau 'delapan'.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Jalankan contoh kalimat demo dan tampilkan hasilnya.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Keluarkan hasil dalam format JSON.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Hanya tampilkan kalimat hasil akhir tanpa tabel rincian.",
    )
    parser.add_argument(
        "--add-prpm",
        metavar="KATA",
        help="Tambahkan kata baku PRPM baru ke database offline.",
    )
    parser.add_argument(
        "--add-norm",
        nargs=2,
        metavar=("TIDAK_BAKU", "BAKU_PRPM"),
        help="Tambahkan pasangan kata tidak baku dan kata baku PRPM ke database offline.",
    )
    parser.add_argument(
        "--add-en",
        metavar="ENGLISH_WORD",
        help="Tambahkan kata Bahasa Inggris ke whitelist database offline.",
    )
    parser.add_argument(
        "--rebuild-db",
        action="store_true",
        help="Bangun ulang database kamus SQLite offline ke kondisi awal.",
    )

    args = parser.parse_args()

    if args.rebuild_db:
        path = init_database(DB_PATH, force_rebuild=True)
        print(f"Database kamus PRPM offline berhasil dibangun ulang di: {path}")
        return 0

    pipeline = PRPMPipeline(db_path=DB_PATH, eight_word=args.eight)

    if args.add_prpm:
        pipeline.lexicon_checker.add_prpm_word(args.add_prpm)
        print(f"Kata baku PRPM '{args.add_prpm}' berhasil disimpan ke database offline.")
        return 0

    if args.add_norm:
        non_std, std_w = args.add_norm
        pipeline.lexicon_checker.add_standardization_rule(
            non_std,
            std_w,
            f"Aturan pembakuan pengguna: '{non_std}' -> '{std_w}' mengikut PRPM.",
        )
        print(f"Aturan pembakuan '{non_std}' -> '{std_w}' berhasil disimpan ke database offline.")
        return 0

    if args.add_en:
        pipeline.lexicon_checker.add_english_word(args.add_en)
        print(f"Kata Bahasa Inggris '{args.add_en}' berhasil disimpan ke whitelist offline.")
        return 0

    if args.demo:
        for s in DEMO_SENTENCES:
            res = pipeline.process(s)
            if args.json:
                print(json.dumps(res.to_dict(), ensure_ascii=False))
            elif args.quiet:
                print(res.corrected_text)
            else:
                print_result(res)
        return 0

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: Berkas '{args.file}' tidak ditemukan.", file=sys.stderr)
            return 1
        with open(args.file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        results: List[PipelineResult] = [pipeline.process(line) for line in lines]

        if args.output:
            with open(args.output, "w", encoding="utf-8") as out_f:
                if args.json:
                    json.dump([r.to_dict() for r in results], out_f, ensure_ascii=False, indent=2)
                else:
                    for r in results:
                        out_f.write(r.corrected_text + "\n")
            print(f"✓ Berhasil memproses {len(results)} kalimat dan menyimpan ke '{args.output}'.")
        else:
            for r in results:
                if args.json:
                    print(json.dumps(r.to_dict(), ensure_ascii=False))
                elif args.quiet:
                    print(r.corrected_text)
                else:
                    print_result(r)
        return 0

    if args.sentence:
        res = pipeline.process(args.sentence)
        if args.json:
            print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        elif args.quiet:
            print(res.corrected_text)
        else:
            print_result(res)
        return 0

    run_interactive_repl(pipeline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
