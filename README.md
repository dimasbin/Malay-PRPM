# Aplikasi CLI Pemeriksa & Pembaku Kalimat Bahasa Melayu (PRPM Malaysia) — Full Offline

Aplikasi berbasis **CLI (Command Line Interface)** yang berjalan **100% Full Offline** untuk memeriksa dan membakukan kalimat berbahasa Malaysia yang bercampur dengan Bahasa Inggris (*code-switching*), berdasarkan kaidah **PRPM (Pusat Rujukan Persuratan Melayu - DBP Malaysia)**.

## Fitur Utama
1. **Validasi & Pembakuan Kata PRPM Malaysia (Full Baku)**:
   - Membakukan kata tidak baku, bahasa pasar/slang Malaysia, dan kata serapan tidak baku ke standar Kamus Dewan / PRPM (contoh: `nak` $\rightarrow$ `hendak`, `tak` $\rightarrow$ `tidak`, `paham` $\rightarrow$ `faham`, `pikir` $\rightarrow$ `fikir`, `jadwal` $\rightarrow$ `jadual`, `universitas` $\rightarrow$ `universiti`).
   - Mematuhi kaidah **15 Kata Majmuk Mantap DBP** (`kerja sama` $\rightarrow$ `kerjasama`, `jawatan kuasa` $\rightarrow$ `jawatankuasa`, `tanda tangan` $\rightarrow$ `tandatangan`) dan **Kata Majmuk Terpisah PRPM** (`kemaskini` $\rightarrow$ `kemas kini`, `temuduga` $\rightarrow$ `temu duga`).
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
python prpm_cli.py "saya nak join meeting itu di office pada pukul 8 pagi , apakah jadual sudah ready."
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

### 5. Menambah Kosakata ke Database Offline
```powershell
# Tambah kata baku PRPM baru
python prpm_cli.py --add-prpm "belanjawan"

# Tambah aturan pembakuan kata (tidak baku -> baku PRPM)
python prpm_cli.py --add-norm "bawak" "bawa"

# Tambah kata Bahasa Inggris ke whitelist (agar tidak diganti)
python prpm_cli.py --add-en "spreadsheet"
```

### 6. Menjalankan Unit Test
```powershell
python -m unittest discover -s tests -v
```
