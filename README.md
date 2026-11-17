# Aplikasi CLI Pemeriksa & Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) — Full Offline

Aplikasi berbasis **CLI (Command Line Interface)** yang berjalan **100% Full Offline** untuk memeriksa dan membakukan kalimat berbahasa Malaysia yang bercampur dengan Bahasa Inggris (*code-switching*), berdasarkan kaidah **PRPM (Pusat Rujukan Persuratan Melayu - DBP Malaysia)**.

## Fitur Utama
1. **Dua Mode Pembakuan (`--mode annotation` [Default] & `--mode baku`)**:
   - **Mode `annotation` (Default, Peraturan PM Customer Service Audio)**:
     - **Group 1 (*Write as spoken*)**: Kata lisan umum (`tak`, `je`, `nak`, `kat`, `jap`, `pastu`, `kot`, `ni`, `tu`, `dah`, `sorang`, `lah`, `kan`, `okey`, `tapi`, `dulu`) ditulis apa adanya.
     - **Group 2 (*Accent differences*)**: Variasi sebutan loghat (`ade` $\rightarrow$ `ada`, `saye` $\rightarrow$ `saya`, `ape` $\rightarrow$ `apa`, `kite` $\rightarrow$ `kita`, `ambik` $\rightarrow$ `ambil`, `balek` $\rightarrow$ `balik`) dibakukan ke ejaan rasmi.
     - **Tag `[OVERLAP/]...[/OVERLAP]`**: Spasi di dalam tag dibuang (`[OVERLAP/] school [/OVERLAP]` $\rightarrow$ `[OVERLAP/]school[/OVERLAP]`) dan tanda baca penutup dimasukkan ke dalam tag (`[OVERLAP/]today[/OVERLAP].` $\rightarrow$ `[OVERLAP/]today.[/OVERLAP]`).
   - **Mode `baku` (`--mode baku`)**: Pembakuan penuh PRPM DBP Malaysia termasuk menukar kata lisan (`nak` $\rightarrow$ `hendak`, `tak` $\rightarrow$ `tidak`, `paham` $\rightarrow$ `faham`), **15 Kata Majmuk Mantap DBP**, **Kata Majmuk Terpisah PRPM**, serta peluluhan KPST.
2. **Bypass Kata Campuran Bahasa Inggris (Tidak Diganti)**:
   - Dilengkapi kamus Bahasa Inggris offline beserta penganalisis infleksi (`-s`, `-es`, `-ed`, `-ing`, `-ly`) sehingga kata Bahasa Inggris di dalam kalimat tetap dipertahankan dan tidak dianggap salah eja.
3. **Konversi Angka ke Kalimat Terbilang**:
   - Mengubah angka menjadi teks terbilang secara otomatis (`1000` $\rightarrow$ `seribu`, `800` $\rightarrow$ `lapan ratus` [default PRPM] atau `delapan ratus` dengan flag `--eight delapan`, `ke-2` $\rightarrow$ `kedua`, `3.5` $\rightarrow$ `tiga perpuluhan lima`).
4. **Pemeriksaan Titik (`.`), Koma (`,`), dan Tanda Tanya (`?`)**:
   - Menghapus spasi sebelum tanda baca, menambahkan spasi setelah tanda baca, menormalkan tanda baca ganda (`..`, `??`), mendeteksi **Ayat Tanya** untuk diakhiri `?`, dan menutup **Ayat Penyata** dengan `.`.
5. **Pemeriksaan Huruf Kapital & Non-Kapital**:
   - Mengapitalisasi awal kalimat, Kata Nama Khas (`Isnin`–`Ahad`, `Januari`–`Disember`, `Kuala Lumpur`, `Malaysia`), serta akronim (`PRPM`, `DBP`), dan menurunkan huruf kapital yang salah di tengah kalimat.

---

## Cara Penggunaan (CLI)

### 1. Mode Interaktif (REPL)
Klik dua kali berkas `run_cli.bat` atau jalankan perintah berikut di terminal:
```powershell
python prpm_cli.py
```

### 2. Mode Satu Kalimat Langsung
```powershell
# Default (Mode Annotation - Peraturan PM)
python prpm_cli.py "saya nak join meeting itu di office pada pukul 8 pagi , apakah jadual sudah ready."

# Mode Full Baku PRPM Malaysia
python prpm_cli.py --mode baku "saya nak join meeting itu di office pada pukul 8 pagi , apakah jadual sudah ready."
```
Jika ingin menggunakan ejaan `delapan` untuk angka `8`:
```powershell
python prpm_cli.py --eight delapan "harga barang itu 1000 ringgit dan ada 800 unit"
```

### 3. Mode Demo Otomatis
```powershell
python prpm_cli.py --demo
```

### 4. Mode Batch File (`.txt`)
```powershell
python prpm_cli.py --file input.txt --output hasil_baku.txt
```

### 5. Mengelola & Menyinkronkan Kamus Offline (`prpm_offline.db`)
```powershell
# Lihat statistik isi database kamus offline
python prpm_cli.py --stats

# Tambah kata baku PRPM baru
python prpm_cli.py --add-prpm "belanjawan"

# Tambah aturan pembakuan kata (tidak baku -> baku PRPM)
python prpm_cli.py --add-norm "ngam" "sesuai"

# Tambah kata Bahasa Inggris ke whitelist (agar tidak diganti)
python prpm_cli.py --add-en "spreadsheet"

# Impor berkas wordlist lokal (.dic Hunspell atau .txt)
python prpm_cli.py --import-dic path\ke\ms_MY.dic
python prpm_cli.py --import-en path\ke\en_GB.dic

# Sinkronkan kamus Melayu (hunspell-ms) & Inggris (LibreOffice en_GB) saat online
python prpm_cli.py --sync-lexicon

# Perbarui kamus bawaan tanpa menghapus entri tambahan pengguna
python prpm_cli.py --upgrade-db
```

### 6. Menjalankan Unit Test
```powershell
python -m unittest discover -s tests -v
```
