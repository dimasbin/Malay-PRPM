"""
Modul Pembangun Database SQLite Offline untuk Leksikon PRPM Malaysia & Bahasa Inggris.
Menyimpan:
1. prpm_words: Kata baku Bahasa Melayu berdasarkan PRPM / Kamus Dewan DBP Malaysia.
2. ms_standardization: Pemetaan kata tidak baku / bahasa pasar / ejaan salah -> Baku PRPM Malaysia
   (termasuk 15 Kata Majmuk Mantap DBP dan Kata Majmuk Terpisah PRPM).
3. english_words: Leksikon Bahasa Inggris offline (agar kata campuran Inggris dikenali dan tidak diganti).
4. proper_nouns & acronyms: Kata Nama Khas dan akronim resmi untuk pemeriksaan huruf kapital.
"""

from __future__ import annotations
import os
import sqlite3
from typing import Dict, List, Set, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prpm_offline.db")

# ============================================================================
# 1. PEMETAAN PEMBAKUAN KATA MELAYU -> BAKU PRPM MALAYSIA (DBP)
# ============================================================================
# Mencakup:
# - Bahasa pasar / slang / singkatan SMS Malaysia -> Baku PRPM
# - Ejaan salah kaprah kata majmuk (Kata Majmuk Terpisah vs 15 Kata Majmuk Mantap DBP)
# - Varian ejaan tidak baku / serapan Indonesia -> Ejaan Baku PRPM Malaysia
MS_STANDARDIZATION: Dict[str, Tuple[str, str]] = {
    # Slang & Singkatan Malaysia -> Baku PRPM
    "nak": ("hendak", "Kata tidak baku/slang 'nak' dibakukan menjadi 'hendak' mengikut PRPM."),
    "tak": ("tidak", "Kata singkat 'tak' dibakukan menjadi 'tidak' mengikut PRPM."),
    "takde": ("tiada", "Kata pasar 'takde' dibakukan menjadi 'tiada' mengikut PRPM."),
    "takda": ("tiada", "Kata pasar 'takda' dibakukan menjadi 'tiada' mengikut PRPM."),
    "xde": ("tiada", "Singkatan 'xde' dibakukan menjadi 'tiada' mengikut PRPM."),
    "xnak": ("tidak hendak", "Singkatan 'xnak' dibakukan menjadi 'tidak hendak' mengikut PRPM."),
    "xleh": ("tidak boleh", "Singkatan 'xleh' dibakukan menjadi 'tidak boleh' mengikut PRPM."),
    "takleh": ("tidak boleh", "Kata pasar 'takleh' dibakukan menjadi 'tidak boleh' mengikut PRPM."),
    "dah": ("sudah", "Kata singkat 'dah' dibakukan menjadi 'sudah' mengikut PRPM."),
    "udah": ("sudah", "Kata tidak baku 'udah' dibakukan menjadi 'sudah' mengikut PRPM."),
    "je": ("sahaja", "Kata pasar 'je' dibakukan menjadi 'sahaja' mengikut PRPM."),
    "jer": ("sahaja", "Kata pasar 'jer' dibakukan menjadi 'sahaja' mengikut PRPM."),
    "aje": ("sahaja", "Kata pasar 'aje' dibakukan menjadi 'sahaja' mengikut PRPM."),
    "saja": ("sahaja", "Ejaan baku penuh PRPM mengutamakan 'sahaja'."),
    "kat": ("di", "Kata sendi pasar 'kat' dibakukan menjadi 'di' mengikut PRPM."),
    "korang": ("kamu semua", "Kata ganti pasar 'korang' dibakukan menjadi 'kamu semua' mengikut PRPM."),
    "diorang": ("mereka", "Kata ganti pasar 'diorang' dibakukan menjadi 'mereka' mengikut PRPM."),
    "dorang": ("mereka", "Kata ganti pasar 'dorang' dibakukan menjadi 'mereka' mengikut PRPM."),
    "depa": ("mereka", "Kata dialek 'depa' dibakukan menjadi 'mereka' mengikut PRPM."),
    "kitorang": ("kami", "Kata ganti pasar 'kitorang' dibakukan menjadi 'kami' mengikut PRPM."),
    "kitorg": ("kami", "Singkatan 'kitorg' dibakukan menjadi 'kami' mengikut PRPM."),
    "camne": ("bagaimana", "Kata pasar 'camne' dibakukan menjadi 'bagaimana' mengikut PRPM."),
    "cane": ("bagaimana", "Kata pasar 'cane' dibakukan menjadi 'bagaimana' mengikut PRPM."),
    "gimana": ("bagaimana", "Kata tidak baku 'gimana' dibakukan menjadi 'bagaimana' mengikut PRPM."),
    "kenapa": ("mengapa", "Kata tanya 'kenapa' dibakukan menjadi 'mengapa' dalam laras baku PRPM."),
    "nape": ("mengapa", "Kata pasar 'nape' dibakukan menjadi 'mengapa' mengikut PRPM."),
    "kerna": ("kerana", "Ejaan tidak baku 'kerna' dibakukan menjadi 'kerana' mengikut PRPM."),
    "karena": ("kerana", "Ejaan 'karena' dibakukan menjadi 'kerana' mengikut PRPM Malaysia."),
    "karna": ("kerana", "Ejaan tidak baku 'karna' dibakukan menjadi 'kerana' mengikut PRPM Malaysia."),
    "krn": ("kerana", "Singkatan 'krn' dibakukan menjadi 'kerana' mengikut PRPM."),
    "sbb": ("sebab", "Singkatan 'sbb' dibakukan menjadi 'sebab' mengikut PRPM."),
    "tapi": ("tetapi", "Kata hubung singkat 'tapi' dibakukan menjadi 'tetapi' mengikut PRPM."),
    "tp": ("tetapi", "Singkatan 'tp' dibakukan menjadi 'tetapi' mengikut PRPM."),
    "yg": ("yang", "Singkatan 'yg' dibakukan menjadi 'yang' mengikut PRPM."),
    "dgn": ("dengan", "Singkatan 'dgn' dibakukan menjadi 'dengan' mengikut PRPM."),
    "utk": ("untuk", "Singkatan 'utk' dibakukan menjadi 'untuk' mengikut PRPM."),
    "dlm": ("dalam", "Singkatan 'dlm' dibakukan menjadi 'dalam' mengikut PRPM."),
    "pd": ("pada", "Singkatan 'pd' dibakukan menjadi 'pada' mengikut PRPM."),
    "kpd": ("kepada", "Singkatan 'kpd' dibakukan menjadi 'kepada' mengikut PRPM."),
    "drpd": ("daripada", "Singkatan 'drpd' dibakukan menjadi 'daripada' mengikut PRPM."),
    "dr": ("dari", "Singkatan 'dr' dibakukan menjadi 'dari' mengikut PRPM."),
    "skrg": ("sekarang", "Singkatan 'skrg' dibakukan menjadi 'sekarang' mengikut PRPM."),
    "skg": ("sekarang", "Singkatan 'skg' dibakukan menjadi 'sekarang' mengikut PRPM."),
    "blh": ("boleh", "Singkatan 'blh' dibakukan menjadi 'boleh' mengikut PRPM."),
    "bleh": ("boleh", "Kata pasar 'bleh' dibakukan menjadi 'boleh' mengikut PRPM."),
    "bawak": ("bawa", "Ejaan lisan 'bawak' dibakukan menjadi 'bawa' mengikut PRPM."),
    "ambik": ("ambil", "Ejaan lisan 'ambik' dibakukan menjadi 'ambil' mengikut PRPM."),
    "bagitahu": ("memberitahu", "Kata lisan 'bagitahu' dibakukan menjadi 'memberitahu' mengikut PRPM."),
    "bagitau": ("memberitahu", "Kata lisan 'bagitau' dibakukan menjadi 'memberitahu' mengikut PRPM."),
    "gitau": ("memberitahu", "Kata lisan 'gitau' dibakukan menjadi 'memberitahu' mengikut PRPM."),
    "pastu": ("selepas itu", "Kata pasar 'pastu' dibakukan menjadi 'selepas itu' mengikut PRPM."),
    "lepastu": ("selepas itu", "Kata pasar 'lepastu' dibakukan menjadi 'selepas itu' mengikut PRPM."),
    "besok": ("esok", "Dalam laras baku PRPM, 'esok' digunakan sebagai bentuk baku bagi 'besok'."),
    "dulu": ("dahulu", "Kata singkat 'dulu' dibakukan menjadi 'dahulu' mengikut PRPM."),
    "gitu": ("begitu", "Kata singkat 'gitu' dibakukan menjadi 'begitu' mengikut PRPM."),
    "gini": ("begini", "Kata singkat 'gini' dibakukan menjadi 'begini' mengikut PRPM."),
    "ni": ("ini", "Kata tunjuk singkat 'ni' dibakukan menjadi 'ini' mengikut PRPM."),
    "tu": ("itu", "Kata tunjuk singkat 'tu' dibakukan menjadi 'itu' mengikut PRPM."),
    "tau": ("tahu", "Ejaan lisan 'tau' dibakukan menjadi 'tahu' mengikut PRPM."),
    "mau": ("mahu", "Ejaan 'mau' dibakukan menjadi 'mahu' mengikut PRPM Malaysia."),
    "maw": ("mahu", "Ejaan lisan 'maw' dibakukan menjadi 'mahu' mengikut PRPM Malaysia."),
    "pengen": ("hendak", "Kata tidak baku 'pengen' dibakukan menjadi 'hendak' mengikut PRPM."),
    "pingin": ("hendak", "Kata tidak baku 'pingin' dibakukan menjadi 'hendak' mengikut PRPM."),
    "belom": ("belum", "Ejaan tidak baku 'belom' dibakukan menjadi 'belum' mengikut PRPM."),
    "blm": ("belum", "Singkatan 'blm' dibakukan menjadi 'belum' mengikut PRPM."),
    "sdh": ("sudah", "Singkatan 'sdh' dibakukan menjadi 'sudah' mengikut PRPM."),
    "gak": ("tidak", "Kata tidak baku 'gak' dibakukan menjadi 'tidak' mengikut PRPM."),
    "nggak": ("tidak", "Kata tidak baku 'nggak' dibakukan menjadi 'tidak' mengikut PRPM."),
    "enggak": ("tidak", "Kata tidak baku 'enggak' dibakukan menjadi 'tidak' mengikut PRPM."),

    # Ejaan Baku PRPM Malaysia vs Ejaan Tidak Baku / Varian Serumpun
    "paham": ("faham", "Ejaan baku PRPM Malaysia ialah 'faham' (bukan 'paham')."),
    "pikir": ("fikir", "Ejaan baku PRPM Malaysia ialah 'fikir' (bukan 'pikir')."),
    "berpikir": ("berfikir", "Ejaan baku PRPM Malaysia ialah 'berfikir' (bukan 'berpikir')."),
    "pikiran": ("fikiran", "Ejaan baku PRPM Malaysia ialah 'fikiran' (bukan 'pikiran')."),
    "coba": ("cuba", "Ejaan baku PRPM Malaysia ialah 'cuba' (bukan 'coba')."),
    "mencoba": ("mencuba", "Ejaan baku PRPM Malaysia ialah 'mencuba' (bukan 'mencoba')."),
    "dicoba": ("dicuba", "Ejaan baku PRPM Malaysia ialah 'dicuba' (bukan 'dicoba')."),
    "percobaan": ("percubaan", "Ejaan baku PRPM Malaysia ialah 'percubaan' (bukan 'percobaan')."),
    "jadwal": ("jadual", "Ejaan baku PRPM Malaysia ialah 'jadual' (bukan 'jadwal')."),
    "kantor": ("pejabat", "Padanan baku PRPM Malaysia bagi tempat kerja ialah 'pejabat'."),
    "uang": ("wang", "Ejaan baku PRPM Malaysia ialah 'wang' (bukan 'uang')."),
    "duit": ("wang", "Dalam laras baku PRPM, 'wang' lebih baku berbanding 'duit'."),
    "nomor": ("nombor", "Ejaan baku PRPM Malaysia ialah 'nombor' (bukan 'nomor')."),
    "nomer": ("nombor", "Ejaan baku PRPM Malaysia ialah 'nombor' (bukan 'nomer')."),
    "telepon": ("telefon", "Ejaan baku PRPM Malaysia ialah 'telefon' (bukan 'telepon')."),
    "stasiun": ("stesen", "Ejaan baku PRPM Malaysia ialah 'stesen' (bukan 'stasiun')."),
    "bis": ("bas", "Ejaan baku PRPM Malaysia ialah 'bas'."),
    "beda": ("beza", "Ejaan baku PRPM Malaysia ialah 'beza' (bukan 'beda')."),
    "berbeda": ("berbeza", "Ejaan baku PRPM Malaysia ialah 'berbeza' (bukan 'berbeda')."),
    "perbedaan": ("perbezaan", "Ejaan baku PRPM Malaysia ialah 'perbezaan' (bukan 'perbedaan')."),
    "resmi": ("rasmi", "Ejaan baku PRPM Malaysia ialah 'rasmi' (bukan 'resmi')."),
    "meresmikan": ("merasmikan", "Ejaan baku PRPM Malaysia ialah 'merasmikan' (bukan 'meresmikan')."),
    "peresmian": ("perasmian", "Ejaan baku PRPM Malaysia ialah 'perasmian' (bukan 'peresmian')."),
    "analisa": ("analisis", "Ejaan baku PRPM Malaysia ialah 'analisis' (bukan 'analisa')."),
    "sistim": ("sistem", "Ejaan baku PRPM Malaysia ialah 'sistem' (bukan 'sistim')."),
    "nasehat": ("nasihat", "Ejaan baku PRPM Malaysia ialah 'nasihat' (bukan 'nasehat')."),
    "resiko": ("risiko", "Ejaan baku PRPM Malaysia ialah 'risiko' (bukan 'resiko')."),
    "praktek": ("praktik", "Ejaan baku PRPM Malaysia ialah 'praktik' (bukan 'praktek')."),
    "kualitas": ("kualiti", "Ejaan baku PRPM Malaysia ialah 'kualiti'."),
    "kuantitas": ("kuantiti", "Ejaan baku PRPM Malaysia ialah 'kuantiti'."),
    "universitas": ("universiti", "Ejaan baku PRPM Malaysia ialah 'universiti'."),
    "aktivitas": ("aktiviti", "Ejaan baku PRPM Malaysia ialah 'aktiviti'."),
    "fasilitas": ("fasiliti", "Ejaan baku PRPM Malaysia ialah 'fasiliti'."),
    "prioritas": ("prioriti", "Ejaan baku PRPM Malaysia ialah 'prioriti'."),
    "komunitas": ("komuniti", "Ejaan baku PRPM Malaysia ialah 'komuniti'."),
    "identitas": ("identiti", "Ejaan baku PRPM Malaysia ialah 'identiti'."),
    "realitas": ("realiti", "Ejaan baku PRPM Malaysia ialah 'realiti'."),
    "mayoritas": ("majoriti", "Ejaan baku PRPM Malaysia ialah 'majoriti'."),
    "minoritas": ("minoriti", "Ejaan baku PRPM Malaysia ialah 'minoriti'."),
    "otoritas": ("autoriti", "Ejaan baku PRPM Malaysia ialah 'autoriti'."),
    "produktivitas": ("produktiviti", "Ejaan baku PRPM Malaysia ialah 'produktiviti'."),
    "kreativitas": ("kreativiti", "Ejaan baku PRPM Malaysia ialah 'kreativiti'."),
    "informasi": ("maklumat", "Padanan baku PRPM Malaysia ialah 'maklumat'."),
    "jawaban": ("jawapan", "Ejaan baku PRPM Malaysia ialah 'jawapan' (bukan 'jawaban')."),
    "kapan": ("bila", "Kata tanya masa baku PRPM Malaysia ialah 'bila' atau 'bilakah'."),
    "butuh": ("perlu", "Kata baku PRPM Malaysia ialah 'perlu'."),
    "membutuhkan": ("memerlukan", "Kata baku PRPM Malaysia ialah 'memerlukan'."),
    "kebutuhan": ("keperluan", "Kata baku PRPM Malaysia ialah 'keperluan'."),
    "gampang": ("mudah", "Kata baku PRPM Malaysia ialah 'mudah'."),
    "delapan": ("lapan", "Ejaan angka baku PRPM Malaysia ialah 'lapan'."),

    # Kaidah Kata Majmuk Terpisah PRPM (sering salah ditulis rapat)
    "terimakasih": ("terima kasih", "Mengikut PRPM DBP, kata majmuk 'terima kasih' wajib ditulis terpisah."),
    "kemaskini": ("kemas kini", "Mengikut PRPM DBP, kata majmuk 'kemas kini' wajib ditulis terpisah."),
    "muatturun": ("muat turun", "Mengikut PRPM DBP, kata majmuk 'muat turun' wajib ditulis terpisah."),
    "muatnaik": ("muat naik", "Mengikut PRPM DBP, kata majmuk 'muat naik' wajib ditulis terpisah."),
    "rekabentuk": ("reka bentuk", "Mengikut PRPM DBP, kata majmuk 'reka bentuk' wajib ditulis terpisah."),
    "ulangkaji": ("ulang kaji", "Mengikut PRPM DBP, kata majmuk 'ulang kaji' wajib ditulis terpisah."),
    "temuduga": ("temu duga", "Mengikut PRPM DBP, kata majmuk 'temu duga' wajib ditulis terpisah."),
    "tengahari": ("tengah hari", "Mengikut PRPM DBP, 'tengah hari' wajib ditulis terpisah."),
    "pilihanraya": ("pilihan raya", "Mengikut PRPM DBP, 'pilihan raya' wajib ditulis terpisah."),
    "bandaraya": ("bandar raya", "Mengikut PRPM DBP, 'bandar raya' wajib ditulis terpisah (kecuali nama khas)."),
    "jalanraya": ("jalan raya", "Mengikut PRPM DBP, 'jalan raya' wajib ditulis terpisah."),
    "pasaraya": ("pasar raya", "Mengikut PRPM DBP, 'pasar raya' wajib ditulis terpisah."),
    "keretapi": ("kereta api", "Mengikut PRPM DBP, 'kereta api' wajib ditulis terpisah."),
    "kapalterbang": ("kapal terbang", "Mengikut PRPM DBP, 'kapal terbang' wajib ditulis terpisah."),
    "gambarajah": ("gambar rajah", "Mengikut PRPM DBP, 'gambar rajah' wajib ditulis terpisah."),
    "aturcara": ("atur cara", "Mengikut PRPM DBP, 'atur cara' wajib ditulis terpisah."),
    "katalaluan": ("kata laluan", "Mengikut PRPM DBP, 'kata laluan' wajib ditulis terpisah."),
    "suratkhabar": ("surat khabar", "Mengikut PRPM DBP, 'surat khabar' wajib ditulis terpisah."),
    "campurtangan": ("campur tangan", "Mengikut PRPM DBP, 'campur tangan' wajib ditulis terpisah."),
    "ambilalih": ("ambil alih", "Mengikut PRPM DBP, 'ambil alih' wajib ditulis terpisah."),

    # Bahasa Basahan & Singkatan Tambahan -> Baku PRPM Malaysia (Terverifikasi PRPM DBP)
    "sikit": ("sedikit", "Kata basahan 'sikit' dibakukan menjadi 'sedikit' mengikut PRPM DBP."),
    "ngam": ("sesuai", "Kata basahan 'ngam' dibakukan menjadi 'sesuai' mengikut PRPM DBP."),
    "kompeni": ("syarikat", "Kata percakapan 'kompeni' dibakukan menjadi 'syarikat' dalam konteks perniagaan PRPM DBP."),
    "jap": ("sekejap", "Singkatan lisan 'jap' dibakukan menjadi 'sekejap' mengikut PRPM."),
    "camni": ("begini", "Kata pasar 'camni' dibakukan menjadi 'begini' mengikut PRPM."),
    "camtu": ("begitu", "Kata pasar 'camtu' dibakukan menjadi 'begitu' mengikut PRPM."),
    "macamni": ("begini", "Kata pasar 'macamni' dibakukan menjadi 'begini' mengikut PRPM."),
    "macamtu": ("begitu", "Kata pasar 'macamtu' dibakukan menjadi 'begitu' mengikut PRPM."),
    "sape": ("siapa", "Ejaan lisan 'sape' dibakukan menjadi 'siapa' mengikut PRPM."),
    "mmg": ("memang", "Singkatan 'mmg' dibakukan menjadi 'memang' mengikut PRPM."),
    "sgt": ("sangat", "Singkatan 'sgt' dibakukan menjadi 'sangat' mengikut PRPM."),
    "org": ("orang", "Singkatan 'org' dibakukan menjadi 'orang' mengikut PRPM."),
    "brg": ("barang", "Singkatan 'brg' dibakukan menjadi 'barang' mengikut PRPM."),
    "bkn": ("bukan", "Singkatan 'bkn' dibakukan menjadi 'bukan' mengikut PRPM."),
    "jgn": ("jangan", "Singkatan 'jgn' dibakukan menjadi 'jangan' mengikut PRPM."),
    "knp": ("mengapa", "Singkatan 'knp' dibakukan menjadi 'mengapa' mengikut PRPM."),
    "dtg": ("datang", "Singkatan 'dtg' dibakukan menjadi 'datang' mengikut PRPM."),
    "tgk": ("lihat", "Singkatan 'tgk' dibakukan menjadi 'lihat' mengikut PRPM."),
    "xtau": ("tidak tahu", "Singkatan 'xtau' dibakukan menjadi 'tidak tahu' mengikut PRPM."),
    "xtahu": ("tidak tahu", "Singkatan 'xtahu' dibakukan menjadi 'tidak tahu' mengikut PRPM."),
    "bole": ("boleh", "Ejaan singkat 'bole' dibakukan menjadi 'boleh' mengikut PRPM."),
    "mcam": ("seperti", "Ejaan tidak baku 'mcam' dibakukan menjadi 'seperti' mengikut PRPM."),
    "bg": ("beri", "Singkatan 'bg' dibakukan menjadi 'beri' mengikut PRPM."),

    # Kaidah Kata Sendi 'di' dan 'ke' (Wajib Terpisah untuk Tempat/Arah)
    "disini": ("di sini", "Kata sendi nama tempat 'di sini' wajib ditulis terpisah mengikut PRPM DBP."),
    "disana": ("di sana", "Kata sendi nama tempat 'di sana' wajib ditulis terpisah mengikut PRPM DBP."),
    "disitu": ("di situ", "Kata sendi nama tempat 'di situ' wajib ditulis terpisah mengikut PRPM DBP."),
    "diatas": ("di atas", "Kata sendi nama tempat 'di atas' wajib ditulis terpisah mengikut PRPM DBP."),
    "dibawah": ("di bawah", "Kata sendi nama tempat 'di bawah' wajib ditulis terpisah mengikut PRPM DBP."),
    "didalam": ("di dalam", "Kata sendi nama tempat 'di dalam' wajib ditulis terpisah mengikut PRPM DBP."),
    "diluar": ("di luar", "Kata sendi nama tempat 'di luar' wajib ditulis terpisah mengikut PRPM DBP."),
    "dimana": ("di mana", "Kata sendi 'di mana' wajib ditulis terpisah mengikut PRPM DBP."),
    "kemana": ("ke mana", "Kata sendi 'ke mana' wajib ditulis terpisah mengikut PRPM DBP."),
    "keatas": ("ke atas", "Kata sendi 'ke atas' wajib ditulis terpisah mengikut PRPM DBP."),
    "kebawah": ("ke bawah", "Kata sendi 'ke bawah' wajib ditulis terpisah mengikut PRPM DBP."),
    "kedalam": ("ke dalam", "Kata sendi 'ke dalam' wajib ditulis terpisah mengikut PRPM DBP."),

    # Pembakuan Imbuhan Lazim & Hukum Peluluhan KPST (Tatabahasa Dewan PRPM)
    "memperolehi": ("memperoleh", "Mengikut PRPM DBP, bentuk baku ialah 'memperoleh' (tanpa akhiran '-i')."),
    "diperolehi": ("diperoleh", "Mengikut PRPM DBP, bentuk pasif baku ialah 'diperoleh' (tanpa akhiran '-i')."),
    "mengemaskini": ("mengemas kini", "Mengikut PRPM DBP, kata majmuk berawalan sahaja wajib ditulis terpisah: 'mengemas kini'."),
    "dikemaskini": ("dikemas kini", "Mengikut PRPM DBP, kata majmuk berawalan sahaja wajib ditulis terpisah: 'dikemas kini'."),
    "memparkir": ("memarkir", "Mengikut hukum peluluhan KPST PRPM DBP, 'parkir' meluluh menjadi 'memarkir'."),
    "mensokong": ("menyokong", "Mengikut hukum peluluhan KPST PRPM DBP, 'sokong' meluluh menjadi 'menyokong'."),
    "mentulis": ("menulis", "Mengikut hukum peluluhan KPST PRPM DBP, 'tulis' meluluh menjadi 'menulis'."),
    "mempakai": ("memakai", "Mengikut hukum peluluhan KPST PRPM DBP, 'pakai' meluluh menjadi 'memakai'."),
    "mengkira": ("mengira", "Mengikut hukum peluluhan KPST PRPM DBP, 'kira' meluluh menjadi 'mengira'."),
    "mempamerkan": ("memamerkan", "Mengikut hukum peluluhan KPST PRPM DBP, 'pamer' meluluh menjadi 'memamerkan'."),
    "menselesaikan": ("menyelesaikan", "Mengikut hukum peluluhan KPST PRPM DBP, 'selesai' meluluh menjadi 'menyelesaikan'."),
    "mentolong": ("menolong", "Mengikut hukum peluluhan KPST PRPM DBP, 'tolong' meluluh menjadi 'menolong'."),
    "mentukar": ("menukar", "Mengikut hukum peluluhan KPST PRPM DBP, 'tukar' meluluh menjadi 'menukar'."),
}

# ============================================================================
# 2. 15 KATA MAJMUK MANTAP DBP (Wajib Ditulis Rapat jika Ditemukan Terpisah)
# ============================================================================
KATA_MAJMUK_MANTAP_DBP: Dict[str, str] = {
    "antara bangsa": "antarabangsa",
    "beri tahu": "beritahu",
    "bumi putera": "bumiputera",
    "jawatan kuasa": "jawatankuasa",
    "kaki tangan": "kakitangan",
    "kerja sama": "kerjasama",
    "olah raga": "olahraga",
    "mata hari": "matahari",
    "setia usaha": "setiausaha",
    "suka rela": "sukarela",
    "suruhan jaya": "suruhanjaya",
    "tanda tangan": "tandatangan",
    "tanggung jawab": "tanggungjawab",
    "warga negara": "warganegara",
    "pesuruh jaya": "pesuruhjaya",
}

# ============================================================================
# 3. LEKSIKON KATA BAKU PRPM MALAYSIA (Kata Dasar & Kata Umum)
# ============================================================================
PRPM_WORDS: Set[str] = {
    # Kata Ganti Nama
    "saya", "aku", "kami", "kita", "anda", "kamu", "awak", "engkau", "beliau", "dia", "ia", "mereka",
    "baginda", "beta", "patik", "hamba", "sendiri", "masing-masing", "sesiapa", "siapa-siapa",
    # Kata Tanya & Penunjuk
    "apa", "apakah", "siapa", "siapakah", "bila", "bilakah", "mengapa", "mengapakah",
    "bagaimana", "bagaimanakah", "berapa", "berapakah", "mana", "manakah", "adakah",
    "ini", "itu", "sini", "situ", "sana", "begitu", "begini", "demikian",
    # Kata Tugas, Hubung, Sendi, Bantu
    "dan", "atau", "tetapi", "namun", "malah", "bahkan", "serta", "lalu", "kemudian", "sambil",
    "kerana", "sebab", "oleh", "untuk", "bagi", "demi", "tentang", "mengenai", "terhadap",
    "dengan", "tanpa", "sejak", "semenjak", "hingga", "sehingga", "sampai", "antara",
    "di", "ke", "dari", "daripada", "pada", "kepada", "dalam", "luar", "atas", "bawah",
    "depan", "hadapan", "belakang", "tepi", "sisi", "tengah", "sebelah", "sekitar", "sekeliling",
    "apabila", "ketika", "semasa", "sementara", "sewaktu", "sebelum", "selepas", "sesudah",
    "jika", "jikalau", "kalau", "sekiranya", "andainya", "walaupun", "sungguhpun", "meskipun", "biarpun",
    "agar", "supaya", "bahawa", "yang", "adalah", "ialah", "merupakan",
    "sudah", "telah", "belum", "sedang", "masih", "akan", "baru", "pernah", "acapkali", "sering",
    "hendak", "mahu", "ingin", "boleh", "dapat", "mesti", "perlu", "wajib", "harus", "patut", "enggan",
    "tidak", "bukan", "tiada", "jangan", "usah", "sahaja", "hanya", "jua", "juga", "pun", "lagi",
    "sangat", "amat", "sungguh", "sekali", "paling", "terlalu", "terlampau", "agak", "cukup", "kurang",
    "lebih", "makin", "semakin", "kian",
    # Kata Bilangan & Ukuran
    "sifar", "kosong", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "lapan", "sembilan",
    "sepuluh", "sebelas", "belas", "puluh", "seratus", "ratus", "seribu", "ribu", "juta", "bilion", "trilion",
    "pertama", "kedua", "ketiga", "keempat", "kelima", "perpuluhan", "setengah", "separuh", "sebahagian",
    "semua", "seluruh", "segala", "sekalian", "setiap", "tiap-tiap", "beberapa", "banyak", "ramai", "sedikit",
    "buah", "orang", "ekor", "batang", "helai", "keping", "biji", "pucuk", "bilah", "pasang", "unit",
    "ringgit", "sen", "meter", "kilometer", "gram", "kilogram", "liter", "jam", "minit", "saat",
    # 15 Kata Majmuk Mantap DBP
    "antarabangsa", "beritahu", "bumiputera", "jawatankuasa", "kakitangan", "kerjasama",
    "olahraga", "matahari", "setiausaha", "sukarela", "suruhanjaya", "tandatangan",
    "tanggungjawab", "warganegara", "pesuruhjaya",
    # Kata Kerja & Kata Dasar Umum PRPM
    "ada", "ajar", "ajak", "akhiri", "aku", "ambil", "anggap", "angkat", "antar", "arah", "atur",
    "baca", "bahagi", "bahas", "bantu", "bangun", "bawa", "bayar", "baiki", "bela", "beli", "bentuk",
    "beri", "berhenti", "berjalan", "berjaya", "berkata", "berlaku", "bermula", "bertemu", "bertanya",
    "beza", "bina", "bincang", "buat", "buka", "bunuh", "buru",
    "capai", "cari", "catat", "cetak", "cipta", "cuba", "cuci", "cukup",
    "daftar", "dapat", "datang", "dengar", "diri", "dorong", "duduk", "duga",
    "edar", "ejas", "elak", "faham", "fikir", "guna", "ganti", "ganggu", "gerak", "gubal", "gulung",
    "hadir", "hadap", "hantar", "hapus", "harap", "hasil", "henti", "hidup", "hilang", "hitung", "hormat", "hubung",
    "ikut", "imbas", "ingat", "isi", "izin", "jaga", "jadi", "jalan", "jamin", "janji", "jatuh", "jawab", "jelas", "jual", "jumpa",
    "kaji", "kawal", "kembali", "kemas", "kenal", "kembang", "kendali", "kerja", "ketahui", "kira", "kirim", "kongsi", "kumpul", "kurang",
    "laksana", "laku", "lalu", "langkah", "lapor", "larang", "latih", "lawat", "layan", "letak", "lihat", "lulus", "lupa",
    "main", "makan", "maklum", "maju", "masuk", "mati", "menang", "minum", "minta", "mohon", "muat", "mula", "muncul",
    "naik", "nampak", "nilai", "nyata", "ubah", "uji", "ukur", "ulang", "umum", "undi", "urus", "usaha", "usul",
    "pakai", "panggil", "pandang", "pandu", "pantau", "pasang", "pasti", "patuh", "pegang", "pelihara", "periksa", "perlu", "pilih", "pindah", "pinjam", "potong", "proses", "pukul", "pulang", "putus",
    "ancang", "rancang", "rasmi", "rawat", "reka", "rujuk", "runding", "rosak",
    "sedia", "sebut", "sedar", "selamat", "selesai", "selidik", "semak", "sembah", "simpan", "sokong", "soal", "suruh", "susun", "syor",
    "tahu", "tahan", "tambah", "tampil", "tanam", "tangguh", "tanggung", "tangkap", "tanya", "tarik", "tawar", "tekan", "temu", "tentu", "terbang", "terbit", "terima", "terjemah", "terus", "tetap", "tidur", "tinggal", "tingkat", "tolak", "tolong", "tonton", "tulis", "tumbuh", "tunjuk", "turun", "turut", "tutup",
    "wujud", "ziarah",
    # Kata Nama & Kata Adjektif Umum PRPM
    "abang", "adik", "agama", "ahli", "air", "akal", "akhir", "akta", "aktiviti", "alam", "alamat", "alat", "aliran", "aman", "amanah", "anak", "anggota", "angin", "angka", "anggaran", "anugerah", "api", "arah", "aras", "artikel", "asas", "asing", "aspek", "aturan", "awal", "awam", "ayah", "ayat",
    "badan", "bahagian", "bahan", "baharu", "baru", "bahasa", "bahaya", "baik", "baju", "baka", "bakat", "baki", "balai", "bandar", "bangsa", "bangunan", "bank", "bantuan", "bapa", "barang", "barat", "baris", "bas", "batal", "batas", "batu", "bawah", "bayaran", "beban", "bebas", "beg", "bekal", "bekas", "belanja", "belanjawan", "belia", "benar", "bencana", "benda", "bendahari", "bentuk", "beras", "berat", "berita", "berkas", "bersih", "besar", "besi", "betul", "biasa", "biaya", "bidang", "bijak", "bil", "bilik", "bimbingan", "bimbang", "bintang", "biru", "bisnes", "borang", "bandar", "budaya", "budi", "buka", "bukti", "buku", "bulan", "bulat", "bumi", "bunga", "bunyi", "buruk", "burung", "butir",
    "cabang", "cabaran", "cadangan", "cahaya", "cair", "calon", "campur", "canggih", "cantik", "cara", "catatan", "cawangan", "cekap", "cepat", "cerah", "ceramah", "cerdik", "cerita", "cermat", "cinta", "ciri", "contoh", "corak", "cuaca", "cukai", "cuti",
    "dada", "daerah", "daftar", "daging", "dahulu", "dakwaan", "dalam", "damai", "dana", "dapur", "darah", "darat", "darjah", "dasar", "data", "datuk", "daun", "dawai", "daya", "dekat", "dewan", "dewasa", "dinding", "dingin", "diri", "disiplin", "doktor", "dokumen", "doa", "dosa", "dunia", "dusun",
    "ekonomi", "elaun", "elok", "emas", "emosi", "empati", "enjin", "era", "erti", "esok", "etika",
    "faedah", "faktor", "fakta", "fakulti", "famili", "farmasi", "fasa", "fasiliti", "fenomena", "filem", "fizikal", "fokus", "format", "formula", "forum", "foto", "fungsi",
    "gabungan", "gaji", "galakan", "gambar", "gandingan", "gangguan", "garam", "garis", "gaya", "gejala", "gelap", "gelaran", "gelombang", "gempa", "gembira", "generasi", "gerak", "gerakan", "geran", "gigi", "giliran", "global", "golongan", "graf", "gudang", "gula", "gunung", "guru",
    "habis", "had", "hadiah", "hadir", "hadirin", "haiwan", "hajat", "hak", "hakikat", "hakim", "hal", "halaman", "halangan", "halus", "hampir", "hangat", "harapan", "harga", "hari", "harian", "harta", "hasil", "hati", "hayat", "hebat", "helah", "hemat", "hidangan", "hidung", "hijau", "hikmah", "hilang", "himpunan", "hitam", "hospital", "hotel", "hubungan", "hujan", "hukuman", "hulu", "huruf", "hutan", "hutang",
    "ibadah", "ibarat", "ibu", "idea", "identiti", "iklan", "iklim", "ikrar", "iktiraf", "ilmu", "imej", "impak", "impian", "indah", "indeks", "individu", "industri", "inflasi", "infrastruktur", "ingat", "ingatan", "inisiatif", "inovasi", "insan", "insiden", "institusi", "institut", "insurans", "integriti", "intelek", "intipati", "ipoh", "iringan", "isi", "isnin", "istana", "isteri", "istilah", "istimewa", "isu", "izin",
    "jabatan", "jadual", "jaguh", "jahat", "jalan", "jalur", "jam", "jambatan", "jaminan", "jamuan", "jangka", "jangkitan", "janji", "jantung", "jarak", "jarang", "jari", "jaringan", "jarum", "jasa", "jasmani", "jauh", "jawapan", "jawatan", "jaya", "jejaka", "jelas", "jemputan", "jenama", "jenayah", "jendela", "jenis", "jentera", "jernih", "jiran", "jiwa", "jodoh", "juara", "jumaat", "jumlah", "jurang", "jurnal", "juru", "jurulatih", "jurutera", "jurus", "juta",
    "kaca", "kadar", "kaedah", "kain", "kajian", "kakak", "kaki", "kalah", "kali", "kalimat", "kalangan", "kalsium", "kamus", "kanak", "kanak-kanak", "kanan", "kandungan", "kampung", "kapal", "kapasiti", "kapten", "karangan", "karbon", "karya", "kasar", "kasih", "kasut", "kata", "kategori", "katil", "kaum", "kawal", "kawalan", "kawan", "kawasan", "kaya", "kayu", "keadaan", "keadilan", "keamanan", "kebaikan", "kebajikan", "kebanyakan", "kebebasan", "kebenaran", "kebersihan", "kebiasaannya", "kebudayaan", "kebun", "kecemasan", "kecekapan", "kecil", "kecuali", "kedai", "kediaman", "kedudukan", "kehadiran", "kehidupan", "kehendak", "kehilangan", "keindahan", "keinginan", "kejadian", "kejayaan", "kejohanan", "kejutan", "kekal", "kekayaan", "kekuatan", "kekurangan", "kelab", "kelabu", "kelahiran", "kelakuan", "kelam", "kelantan", "kelas", "kelayakan", "kelebihan", "kelemahan", "kelengkapan", "keliling", "kelmarin", "kelompok", "keluar", "keluarga", "kelulusan", "kemahiran", "kemajuan", "kemalangan", "kemanusiaan", "kemampuan", "kemas", "kematian", "kembali", "kembara", "kemenangan", "kementerian", "kemiskinan", "kemudahan", "kemungkinan", "kenaikan", "kenangan", "kenderaan", "kenyataan", "kepala", "kepentingan", "kepercayaan", "keperluan", "kepimpinan", "keputusan", "keraian", "kerajaan", "kerana", "kerani", "kerap", "keras", "keratan", "kereta", "kerjaya", "kertas", "kerugian", "kerusi", "kes", "kesalahan", "kesan", "kesedaran", "kesejahteraan", "keselamatan", "keseluruhan", "kesempatan", "kesenian", "kesihatan", "kesimpulan", "kesulitan", "ketara", "ketat", "ketiga", "ketinggian", "ketua", "keturunan", "keupayaan", "keutamaan", "kewangan", "kewajipan", "khabar", "khamis", "khas", "khidmat", "khusus", "kilang", "kini", "kira", "kiri", "kisah", "kitab", "kitar", "klasik", "klinik", "kod", "kolej", "komisen", "komited", "komitmen", "kompleks", "komponen", "komputer", "komunikasi", "komuniti", "konsep", "kontrak", "kontraktor", "konvensyen", "koperasi", "kopi", "korban", "korporat", "kos", "kosong", "kota", "kotak", "kotor", "kreatif", "kreativiti", "kredit", "kriteria", "kritikal", "krisis", "kuasa", "kualiti", "kuantiti", "kuat", "kubu", "kucing", "kuda", "kuih", "kukuh", "kuliah", "kulit", "kumpulan", "kunci", "kuning", "kunjungan", "kuota", "kurang", "kursi", "kursus", "kutipan",
    "laba", "ladang", "lagu", "lahir", "lain", "laki", "lelaki", "laku", "laluan", "lama", "laman", "lambang", "lambat", "lampu", "lancar", "landasan", "langit", "langkah", "langsung", "lanjut", "lantai", "lantik", "lapan", "lapang", "lapangan", "lapisan", "laporan", "larangan", "laras", "lari", "latihan", "laut", "lautan", "lawan", "lawatan", "layak", "layanan", "layar", "lazim", "lebar", "lebih", "leher", "lekas", "lemah", "lemak", "lembaga", "lembut", "lengkap", "lengan", "lepas", "lesen", "letih", "lewat", "liar", "lidah", "lihat", "lima", "limpah", "lindung", "lingkungan", "lintas", "liputan", "lisan", "liter", "logik", "lokasi", "lombong", "lompat", "longgar", "lorong", "luas", "luar", "lubang", "luka", "lukisan", "lulus", "lumba", "lumpur", "lurus", "lutut",
    "maaf", "macam", "madu", "mahal", "mahasiswa", "mahir", "mahkamah", "mahu", "majikan", "majlis", "majmuk", "maju", "makanan", "makmal", "maklumat", "makmur", "makna", "maksimum", "maksud", "malam", "malang", "malas", "malaysia", "malu", "mampu", "mana", "manakala", "manfaat", "mangsa", "manis", "manusia", "marah", "maruah", "masa", "masakan", "masalah", "masih", "masin", "masing", "masjid", "masuk", "masyarakat", "mata", "matang", "matematik", "matlamat", "maya", "majoriti", "medan", "media", "meja", "mekanisme", "melayu", "melalui", "memang", "menang", "menara", "menarik", "mendapat", "menerima", "mengikut", "mentah", "menteri", "merah", "merdeka", "mereka", "meriah", "mesin", "mesra", "mesti", "mesyuarat", "meter", "mewah", "milik", "mimpi", "minat", "minggu", "minimum", "minuman", "minyak", "miskin", "misi", "modal", "moden", "modul", "molek", "moral", "motivasi", "motor", "muda", "mudah", "muka", "muktamad", "mula", "mulia", "mulut", "muncul", "mungkin", "murah", "murid", "murni", "musim", "musnah", "musuh", "mutu", "muzium",
    "nada", "nafas", "nafkah", "naib", "naik", "nama", "nampak", "namun", "nanti", "nasi", "nasihat", "nasib", "naskhah", "nasional", "negara", "negeri", "nenek", "neraca", "niaga", "niat", "nikmat", "nilai", "nipis", "nisbah", "nombor", "norma", "nota", "notis", "nyata", "nyawa",
    "objektif", "ubat", "operasi", "operator", "optimis", "orang", "organisasi", "otak", "otot",
    "padang", "padat", "padi", "padu", "pagar", "pagi", "paha", "pahit", "pahlawan", "pakaian", "pakar", "pakej", "paksa", "paku", "palsu", "pameran", "panas", "pandai", "pandangan", "panduan", "panel", "panggilan", "pangkat", "pangkal", "pangkalan", "panjang", "pantai", "pantas", "pantau", "papan", "para", "paras", "parlimen", "parti", "pasang", "pasangan", "pasar", "pasaran", "pasir", "pasukan", "patah", "patuh", "patut", "payah", "payung", "pecah", "pedas", "peduli", "pegawai", "peguam", "pejabat", "pejuang", "peka", "pekan", "pekerja", "pekerjaan", "pelabur", "pelaburan", "pelajar", "pelajaran", "pelaksana", "pelaksanaan", "pelakon", "pelan", "pelanggan", "pelancong", "pelancongan", "peluang", "pelbagai", "pelepasan", "pemandu", "pemandangan", "pemantauan", "pemasaran", "pembaca", "pembangunan", "pembayaran", "pembelajaran", "pembeli", "pembelian", "pembentukan", "pemberian", "pembersihan", "pembinaan", "pembuat", "pembukaan", "pemegang", "pemerhatian", "pemeriksaan", "pemerintah", "pemikiran", "pemilik", "pemilihan", "pemimpin", "pemindahan", "pemohon", "pemuda", "pemulihan", "pena", "penahanan", "penambahbaikan", "penambahan", "penampilan", "penanaman", "penanda", "penangguhan", "penangkapan", "penasihat", "pencapaian", "pencarian", "pencegahan", "pencemaran", "pencen", "pencipta", "pendaftaran", "pendakwaan", "pendalaman", "pendapatan", "pendekatan", "pendengar", "penderitaan", "pendeta", "pendidikan", "pendirian", "penduduk", "penemuan", "penempatan", "penentuan", "penerbangan", "penerbit", "penerbitan", "penerima", "penerimaan", "penerokaan", "penetapan", "pengadil", "pengajaran", "pengajian", "pengakuan", "pengalaman", "pengambilan", "penganjur", "pengangkutan", "pengarah", "pengaruh", "pengasas", "pengawal", "pengawasan", "pengecualian", "pengedar", "pengeluaran", "pengenalan", "pengendali", "pengendalian", "pengerusi", "pengetahuan", "pengetua", "pengguna", "penggunaan", "penghantaran", "penghargaan", "penghasilan", "pengiktirafan", "pengiklanan", "pengiraan", "pengiriman", "penglibatan", "penguasaan", "penguatkuasaan", "pengujian", "pengumuman", "pengundi", "pengunjung", "pengurangan", "pengurus", "pengurusan", "penilaian", "peningkatan", "penipuan", "penjaga", "penjagaan", "penjara", "penjelasan", "penjual", "penjualan", "penolong", "penonton", "pensyarah", "pentadbir", "pentadbiran", "pentas", "penting", "penubuhan", "penuh", "penulis", "penulisan", "penumpang", "penurunan", "penutup", "penutupan", "penyakit", "penyanyi", "penyebaran", "penyedia", "penyediaan", "penyelaras", "penyelarasan", "penyelenggaraan", "penyelesaian", "penyelidik", "penyelidikan", "penyerahan", "penyertaan", "penyiasatan", "penyimpanan", "penyokong", "penyusunan", "perabot", "perahu", "perakaunan", "peralatan", "peralihan", "peranan", "perancangan", "perang", "perangai", "perangkap", "perasaan", "perasmian", "peraturan", "perayaan", "perbadanan", "perbahasan", "perbandingan", "perbelanjaan", "perbezaan", "perbincangan", "perbuatan", "perbualan", "percakapan", "percayakan", "percubaan", "percuma", "perdagangan", "perdana", "perdamaian", "perempuan", "perenggan", "pergerakan", "pergi", "perguruan", "perhatian", "perhimpunan", "perhubungan", "peribadi", "perigi", "periksa", "peringatan", "peringkat", "perintah", "peristiwa", "perjalanan", "perjanjian", "perjawatan", "perjuangan", "perkara", "perkahwinan", "perkembangan", "perkhidmatan", "perkongsian", "perladangan", "perlahan", "perakuan", "pelaksanaan", "perlembagaan", "perlindungan", "perlu", "perlumbaan", "permainan", "permata", "permintaan", "permohonan", "permulaan", "permukaan", "perniagaan", "pernyataan", "perpaduan", "perpindahan", "perpuluhan", "perpustakaan", "persatuan", "persefahaman", "persekutuan", "persekitaran", "persediaan", "persidangan", "persijilan", "persoalan", "pertama", "pertambahan", "pertandingan", "pertanian", "pertanyaan", "pertahanan", "pertemuan", "pertengahan", "pertimbangan", "pertubuhan", "pertukaran", "pertumbuhan", "pertunjukan", "perubahan", "perubatan", "perumpamaan", "perundangan", "perundingan", "peruntukan", "perusahaan", "perut", "perutusan", "perwakilan", "pesakit", "pesan", "pesanan", "pesawat", "peserta", "pesisir", "pesta", "peta", "petang", "petani", "peti", "petugas", "petunjuk", "piagam", "piala", "piawai", "piawaian", "pihak", "fikiran", "pilihan", "pimpinan", "pinjaman", "pintu", "pipi", "piring", "pisau", "plan", "plastik", "platform", "pokok", "pola", "polis", "polisi", "politik", "pondok", "popular", "populasi", "port", "posisi", "positif", "pos", "potensi", "potongan", "praktik", "praktikal", "prasangka", "prasarana", "prestasi", "presiden", "prinsip", "prioriti", "produk", "produksi", "produktiviti", "profesional", "profesor", "profil", "program", "projek", "promosi", "prosedur", "proses", "protokol", "provinsi", "puas", "puasa", "puan", "publik", "pujian", "pukul", "pula", "pulang", "pulau", "pulih", "puluh", "punca", "puncak", "pungutan", "pusingan", "pusat", "pustaka", "putera", "puteri", "putih", "putus", "putusan",
    "rabu", "racun", "radio", "ragam", "ragu", "rahsia", "raja", "rajin", "rakan", "rakyat", "ramai", "ramalan", "rambut", "ramai", "rancangan", "rangka", "rangkaian", "rantau", "rantai", "rapat", "rapi", "rasa", "rasmi", "rasuah", "rata", "ratus", "rawatan", "raya", "rayuan", "reaksi", "realiti", "rebah", "rehat", "rekod", "rela", "relevan", "remaja", "rendah", "rentas", "resit", "respon", "respons", "restoran", "rezeki", "riang", "ribu", "ringan", "ringgit", "ringkas", "ringkasan", "risalah", "risiko", "rondaan", "rosak", "roti", "ruang", "ruangan", "rugi", "rujukan", "rukun", "rumah", "rumit", "rumput", "rumusan", "rundingan", "rupa", "rusuhan",
    "saat", "sabar", "sabah", "sabtu", "sabun", "sah", "sahabat", "sahaja", "saham", "sains", "saiz", "sajak", "sakit", "saksi", "saku", "salah", "salam", "saluran", "sama", "saman", "sambungan", "sambutan", "sampah", "sampai", "sampel", "samping", "sampul", "sana", "sandaran", "sangat", "sanggup", "sangka", "saranan", "sarapan", "sarawak", "sari", "sarjana", "sasaran", "sastera", "satu", "saudara", "saudari", "sawit", "sayang", "sayap", "sayur", "sebab", "sebagai", "sebahagian", "sebaliknya", "sebarang", "sebegini", "sebegitu", "sebelah", "sebelas", "sebelum", "sebenar", "sebenarnya", "sebentar", "seberang", "sebutan", "secara", "secukupnya", "sedang", "sedangkan", "sedap", "sedar", "sederhana", "sedia", "sedikit", "sedih", "segala", "segar", "segera", "segi", "sehari", "sehingga", "seimbang", "sejak", "sejarah", "sejati", "sejuk", "sekali", "sekaligus", "sekarang", "sekeliling", "sekitar", "sekolah", "seksyen", "sektor", "sekumpulan", "sekurang-kurangnya", "selagi", "selain", "selalu", "selama", "selamat", "selangor", "selasa", "selatan", "selepas", "selesai", "selidik", "selimut", "seluruh", "semak", "semakan", "semakin", "semalam", "semangat", "semasa", "semata-mata", "sembahyang", "sembilan", "semenanjung", "sementara", "semoga", "sempadan", "sempat", "sempurna", "semua", "semula", "sen", "senang", "senarai", "sendi", "sendiri", "sengaja", "seni", "senjata", "senja", "sentiasa", "sentuh", "senyum", "seorang", "sepakat", "sepanjang", "sepasang", "sepatutnya", "sepenuhnya", "seperti", "sepuluh", "seragam", "serah", "serahan", "serangan", "seratus", "serbu", "serentak", "seribu", "sering", "serius", "serta", "serta-merta", "seru", "sesak", "sesama", "sesat", "sesebuah", "seseorang", "sesi", "sesiapa", "sesuatu", "sesudah", "sesuai", "setakat", "seterusnya", "setia", "setiap", "setiausaha", "setuju", "sewa", "sewaktu", "siang", "siap", "siapa", "siaran", "siasatan", "sibuk", "sidang", "sifat", "sifar", "sihat", "sijil", "sikap", "sila", "silap", "simbol", "simpan", "simpanan", "simpang", "simpati", "sinar", "sindiket", "singgah", "singkat", "singkatan", "sini", "siri", "sisa", "sisi", "sistem", "situ", "situasi", "skala", "skim", "skrin", "skrip", "skuad", "soal", "soalan", "sokongan", "sopan", "sorok", "sosial", "spesifikasi", "spesifik", "stabil", "stadium", "staf", "standard", "status", "statistik", "stesen", "stok", "strategi", "strategik", "struktur", "studio", "suami", "suara", "suasana", "suatu", "subjek", "subsidi", "subuh", "suci", "sudah", "sudut", "suhu", "suka", "sukar", "sukan", "sukarela", "sukarelawan", "suku", "sultan", "sumbangan", "sumber", "sumpah", "sungai", "sungguh", "sunyi", "supaya", "surat", "surau", "suri", "suruhanjaya", "susah", "susu", "susulan", "susunan", "swasta", "syarat", "syarikat", "syiling", "syor", "syukur",
    "taat", "tabiat", "tabung", "tabungan", "tadi", "tahap", "tahan", "tahanan", "tahu", "tahun", "tahunan", "tajam", "tajaan", "tajuk", "takut", "taklimat", "takrif", "takwim", "tali", "talian", "taman", "tamat", "tambah", "tambahan", "tambang", "tampak", "tampan", "tampil", "tamu", "tanah", "tanaman", "tanda", "tandatangan", "tanding", "tangan", "tangga", "tanggal", "tangguh", "tanggung", "tanggungjawab", "tangkap", "tangkapan", "tani", "tanpa", "tanya", "tapak", "taraf", "tarikh", "tarik", "tarikan", "tarian", "tarif", "tasik", "tatabahasa", "tatacara", "tindakan", "tawaran", "tawan", "tawar", "tayangan", "tebal", "tebing", "tebu", "teduh", "tegah", "tegak", "tegas", "teguh", "teguran", "teh", "teknik", "teknikal", "teknologi", "tekanan", "teksi", "tekun", "teladan", "telah", "telapak", "telefon", "televisyen", "telinga", "teliti", "teluk", "telur", "tema", "teman", "tembaga", "tembak", "tembok", "tempias", "tempat", "tempatan", "tempoh", "tempur", "temu", "tenaga", "tenang", "tendang", "tengah", "tenggelam", "tengok", "tentang", "tentangan", "tentera", "tenteram", "tentu", "tenun", "teori", "tepat", "tepi", "tepung", "terang", "terap", "teras", "terbang", "terbit", "terbitan", "terhadap", "terima", "terjemahan", "terjun", "terkenal", "terlalu", "termasuk", "terminal", "ternakan", "teroka", "terowong", "tertentu", "tertib", "teruk", "terus", "terutama", "tesis", "tetamu", "tetap", "tetapi", "tiada", "tiang", "tiap", "tiba", "tidak", "tidur", "tiga", "tikar", "tiket", "tikus", "tilam", "timbalan", "timbang", "timbangan", "timbul", "timur", "tin", "tindak", "tindakan", "tinggal", "tinggi", "tingkap", "tingkat", "tingkatan", "tinjauan", "tipis", "tipu", "tirai", "tiru", "titik", "tiup", "tokoh", "tolak", "tolakan", "tolong", "tombak", "tong", "tonggak", "tongkat", "tonton", "tontonan", "topi", "topik", "tradisi", "tradisional", "tragedi", "transaksi", "transformasi", "transit", "trilion", "tuala", "tuan", "tuang", "tuah", "tubuh", "tuduh", "tuduhan", "tugas", "tugasan", "tuhan", "tuju", "tujuan", "tujuh", "tukang", "tukar", "tulang", "tulen", "tulis", "tulisan", "tulus", "tumbuh", "tumbuhan", "tumpah", "tumpuan", "tunai", "tunas", "tunda", "tunduk", "tunggal", "tunggu", "tunggakan", "tunjuk", "tuntutan", "turun", "turut", "turutan", "tutup", "tutur",
    "ubah", "ubat", "ubi", "ucap", "ucapan", "udara", "ugutan", "ujian", "ukiran", "ukur", "ukuran", "ulama", "ulang", "ulangan", "ular", "ulasan", "ulat", "ulit", "umat", "umbi", "umpama", "umum", "umur", "undang", "undang-undang", "undi", "undian", "undur", "unggas", "unggul", "ungkapan", "ungu", "unik", "unit", "universiti", "unsur", "untuk", "untung", "upacara", "upah", "upaya", "uraian", "urat", "urus", "urusan", "urusetia", "usah", "usaha", "usahawan", "usang", "usia", "usik", "usul", "utama", "utara", "utusan",
    "vaksin", "variasi", "versi", "veterinar", "video", "virus", "visi", "vitamin", "vokal",
    "wabak", "wacana", "wad", "wadah", "wafat", "wahyu", "wajah", "wajar", "wajib", "wakil", "waktu", "walau", "walaupun", "wali", "wanita", "wang", "wangi", "waras", "warga", "warganegara", "waris", "warisan", "warna", "warta", "wartawan", "wasiat", "waspada", "watak", "watikah", "wau", "wawancara", "wawasan", "wayang", "wilayah", "wira", "wirawati", "wisata", "wisma", "wujud",
    "yakin", "yakni", "yang", "yatim", "yayasan", "yuran",
    "zaman", "zat", "ziarah", "zikir", "zon", "zoo",
    # Hari & Bulan (Baku Malaysia)
    "isnin", "selasa", "rabu", "khamis", "jumaat", "sabtu", "ahad",
    "januari", "februari", "mac", "april", "mei", "jun", "julai", "ogos", "september", "oktober", "november", "disember",
    # Kosakata Harian & Gelaran Umum PRPM Tambahan
    "balik", "lapar", "penat", "haus", "cakap", "kejap", "sekejap", "tumpang", "seronok", "pusing",
    "parkir", "risau", "bosan", "kecewa", "gelak", "ketawa", "tangis", "mandi", "masak", "pening",
    "demam", "batuk", "selesema", "cabut", "ketuk", "buang", "campak", "peluk", "kejut", "hairan",
    "celsius", "peratus", "bajet", "diskaun", "bin", "binti", "encik", "haji", "hajah", "tun",
    "bila-bila", "apa-apa", "mana-mana", "mengenai",
}

# ============================================================================
# 4. LEKSIKON BAHASA INGGRIS OFFLINE (Untuk Mengenali & Mempertahankan Kata Inggris)
# ============================================================================
ENGLISH_WORDS: Set[str] = {
    # Kata Kerja, Benda, Sifat, dan Istilah Harian/Kantor/Teknologi Bahasa Inggris
    "a", "able", "about", "above", "accept", "access", "account", "accurate", "achieve", "across", "act", "action", "active", "activity", "actual", "actually", "add", "addition", "additional", "address", "admin", "advance", "advanced", "advantage", "advice", "advise", "affect", "after", "afternoon", "again", "against", "age", "agency", "agenda", "agent", "ago", "agree", "agreement", "ahead", "ai", "aid", "aim", "air", "airport", "alarm", "album", "alert", "align", "alignment", "all", "allow", "almost", "alone", "along", "already", "also", "alter", "alternative", "although", "always", "amazing", "amount", "analysis", "analyze", "and", "angle", "angry", "animal", "announce", "announcement", "annual", "another", "answer", "any", "anybody", "anyone", "anything", "anyway", "anywhere", "apart", "apartment", "apologize", "app", "appear", "apple", "application", "apply", "appoint", "appointment", "appreciate", "approach", "appropriate", "approval", "approve", "april", "area", "argue", "argument", "arise", "arm", "around", "arrange", "arrangement", "arrival", "arrive", "art", "article", "artist", "as", "aside", "ask", "asleep", "aspect", "assess", "assessment", "asset", "assign", "assignment", "assist", "assistance", "assistant", "associate", "assume", "assumption", "assure", "at", "attach", "attachment", "attack", "attempt", "attend", "attendance", "attention", "attitude", "attract", "attractive", "audience", "audit", "august", "author", "authority", "auto", "automatic", "automatically", "available", "average", "avoid", "award", "aware", "awareness", "away", "awesome",
    "baby", "back", "background", "backup", "bad", "bag", "balance", "ball", "ban", "band", "bank", "banking", "bar", "base", "based", "basic", "basically", "basis", "basket", "batch", "bath", "battery", "battle", "be", "beach", "bear", "beat", "beautiful", "beauty", "because", "become", "bed", "bedroom", "beer", "before", "begin", "beginning", "behavior", "behaviour", "behind", "being", "belief", "believe", "bell", "belong", "below", "belt", "bench", "benchmark", "bend", "beneath", "benefit", "beside", "besides", "best", "bet", "better", "between", "beyond", "big", "bike", "bill", "water", "billing", "billion", "bind", "bird", "birth", "birthday", "bit", "bite", "black", "blade", "blame", "blank", "blind", "block", "blog", "blood", "blow", "blue", "board", "boarding", "boat", "body", "boil", "bold", "bomb", "bond", "bone", "bonus", "book", "booking", "boom", "boost", "boot", "border", "bored", "boring", "born", "borrow", "boss", "both", "bother", "bottle", "bottom", "bounce", "bound", "boundary", "bowl", "box", "boy", "boyfriend", "brain", "branch", "brand", "branding", "brave", "bread", "break", "breakfast", "breast", "breath", "breathe", "brick", "bridge", "brief", "briefing", "briefly", "bright", "brilliant", "bring", "broad", "broadcast", "broken", "broker", "brother", "brown", "browse", "browser", "brush", "bubble", "buck", "bucket", "buddy", "budget", "buffer", "bug", "build", "builder", "building", "bulk", "bullet", "bunch", "bundle", "burden", "burn", "bury", "bus", "business", "busy", "but", "butter", "button", "buy", "buyer", "by", "bypass",
    "cab", "cabin", "cabinet", "cable", "cache", "cafe", "cake", "calculate", "calculation", "calendar", "call", "calm", "camera", "camp", "campaign", "campus", "can", "cancel", "cancellation", "cancer", "candidate", "candle", "candy", "cap", "capability", "capable", "capacity", "capital", "captain", "capture", "car", "carbon", "card", "care", "career", "careful", "carefully", "cargo", "carpet", "carrier", "carry", "cart", "case", "cash", "cast", "castle", "casual", "cat", "catalog", "catalogue", "catch", "category", "cater", "catering", "cause", "ceiling", "celebrate", "celebration", "cell", "center", "central", "centre", "century", "ceo", "ceremony", "certain", "certainly", "certificate", "chain", "chair", "chairman", "challenge", "chamber", "champion", "championship", "chance", "change", "channel", "chapter", "character", "characteristic", "charge", "charger", "charity", "charm", "chart", "chase", "chat", "cheap", "cheat", "check", "checker", "checklist", "checkout", "cheek", "cheer", "cheese", "chef", "chemical", "chest", "chicken", "chief", "child", "childhood", "chill", "chip", "chocolate", "choice", "choose", "chop", "church", "cigarette", "cinema", "circle", "circuit", "circumstance", "cite", "citizen", "city", "civil", "claim", "clarify", "clarity", "class", "classic", "classroom", "clause", "clean", "cleaner", "clear", "clearly", "clerk", "clever", "click", "client", "climate", "climb", "clinic", "clinical", "clip", "clock", "clone", "close", "closed", "closely", "closer", "closet", "cloth", "clothes", "clothing", "cloud", "club", "clue", "cluster", "coach", "coaching", "coal", "coast", "coat", "code", "coding", "coffee", "coin", "cold", "collaborate", "collaboration", "collapse", "collar", "colleague", "collect", "collection", "college", "color", "colour", "column", "combination", "combine", "come", "comedy", "comfort", "comfortable", "command", "comment", "commercial", "commission", "commit", "commitment", "committee", "common", "commonly", "communicate", "communication", "community", "company", "compare", "comparison", "compete", "competition", "competitive", "competitor", "complain", "complaint", "complete", "completely", "complex", "complexity", "compliance", "complicated", "comply", "component", "compose", "composition", "comprehensive", "computer", "concentrate", "concentration", "concept", "concern", "concerned", "concert", "conclude", "conclusion", "concrete", "condition", "conduct", "conference", "confidence", "confident", "config", "configuration", "configure", "confirm", "confirmation", "conflict", "confuse", "confused", "confusion", "connect", "connected", "connection", "conscious", "consensus", "consent", "consequence", "conservative", "consider", "considerable", "consideration", "consist", "consistent", "constant", "constantly", "constitute", "constraint", "construct", "construction", "consult", "consultant", "consultation", "consume", "consumer", "consumption", "contact", "contain", "container", "contemporary", "content", "contest", "context", "continue", "continuous", "contract", "contractor", "contrast", "contribute", "contribution", "control", "controller", "controversial", "convenience", "convenient", "convention", "conventional", "conversation", "conversion", "convert", "converter", "convince", "cook", "cookie", "cooking", "cool", "cooperate", "cooperation", "coordinate", "coordinator", "cop", "cope", "copy", "core", "corn", "corner", "corporate", "corporation", "correct", "correction", "correctly", "correlation", "correspond", "corridor", "cost", "costly", "costume", "cottage", "cotton", "couch", "could", "council", "counsel", "count", "counter", "country", "county", "couple", "courage", "course", "court", "cousin", "cover", "coverage", "cow", "crack", "craft", "crash", "crazy", "cream", "create", "creation", "creative", "creativity", "creator", "creature", "credit", "crew", "crime", "criminal", "crisis", "criteria", "critic", "critical", "criticism", "criticize", "crop", "cross", "crowd", "crowded", "crucial", "cruel", "cruise", "crush", "cry", "crystal", "cue", "cultural", "culture", "cup", "cupboard", "cure", "curious", "currency", "current", "currently", "curriculum", "curtain", "curve", "custom", "customer", "customize", "cut", "cute", "cycle",
    "dad", "daily", "damage", "dance", "dancer", "danger", "dangerous", "dare", "dark", "darkness", "dashboard", "data", "database", "date", "daughter", "dawn", "day", "dead", "deadline", "deal", "dealer", "dear", "death", "debate", "debt", "debug", "decade", "december", "decide", "decision", "deck", "declare", "decline", "decorate", "decrease", "dedicate", "deep", "deeply", "deer", "default", "defeat", "defence", "defend", "defendant", "defense", "deficit", "define", "definitely", "definition", "degree", "delay", "delegate", "delete", "deliberate", "delicate", "delicious", "delight", "deliver", "delivery", "demand", "democracy", "democratic", "demo", "demonstrate", "demonstration", "department", "departure", "depend", "dependent", "depending", "deploy", "deployment", "deposit", "depression", "depth", "deputy", "derive", "describe", "description", "desert", "deserve", "design", "designer", "desire", "desk", "desktop", "desperate", "despite", "dessert", "destination", "destroy", "destruction", "detail", "detailed", "detect", "detection", "detective", "determine", "develop", "developer", "development", "device", "devil", "devote", "diagram", "dialog", "dialogue", "diamond", "diary", "dictionary", "die", "diet", "differ", "difference", "different", "differently", "difficult", "difficulty", "dig", "digital", "dimension", "dining", "dinner", "direct", "direction", "directly", "director", "directory", "dirt", "dirty", "disability", "disable", "disabled", "disagree", "disappear", "disappointed", "disappointment", "disaster", "disc", "discipline", "disclose", "disclosure", "discount", "discover", "discovery", "discrimination", "discuss", "discussion", "disease", "dish", "disk", "dislike", "dismiss", "disorder", "display", "dispute", "distance", "distant", "distinct", "distinction", "distinguish", "distribute", "distribution", "district", "disturb", "diverse", "diversity", "divide", "division", "divorce", "do", "doctor", "document", "documentation", "dog", "dollar", "domain", "domestic", "dominant", "dominate", "donate", "donation", "done", "door", "dose", "dot", "double", "doubt", "down", "download", "downtown", "dozen", "draft", "drag", "drama", "dramatic", "dramatically", "draw", "drawer", "drawing", "dream", "dress", "drink", "drive", "driver", "drop", "drug", "drum", "drunk", "dry", "dual", "due", "dull", "dump", "during", "dust", "duty", "dynamic",
    "each", "eager", "ear", "early", "earn", "earnings", "earth", "earthquake", "ease", "easily", "east", "eastern", "easy", "eat", "economic", "economics", "economist", "economy", "edge", "edit", "edition", "editor", "educate", "education", "educational", "educator", "effect", "effective", "effectively", "efficiency", "efficient", "effort", "egg", "eight", "eighteen", "eighty", "either", "elderly", "elect", "election", "electric", "electrical", "electricity", "electronic", "element", "elementary", "elevator", "eleven", "eligible", "eliminate", "elite", "else", "elsewhere", "email", "embarrassed", "embrace", "emerge", "emergency", "emission", "emotion", "emotional", "emphasis", "emphasize", "empire", "employ", "employee", "employer", "employment", "empty", "enable", "encounter", "encourage", "encouragement", "end", "ending", "enemy", "energy", "enforce", "enforcement", "engage", "engaged", "engagement", "engine", "engineer", "engineering", "enhance", "enjoy", "enormous", "enough", "enquiry", "ensure", "enter", "enterprise", "entertain", "entertainment", "enthusiasm", "entire", "entirely", "entitle", "entity", "entrance", "entrepreneur", "entry", "envelope", "environment", "environmental", "episode", "equal", "equally", "equation", "equip", "equipment", "equivalent", "era", "error", "escape", "especially", "essay", "essential", "essentially", "establish", "establishment", "estate", "estimate", "etc", "ethical", "ethics", "ethnic", "evaluate", "evaluation", "even", "evening", "event", "eventually", "ever", "every", "everybody", "everyday", "everyone", "everything", "everywhere", "evidence", "evident", "evil", "evolution", "evolve", "exact", "exactly", "exam", "examination", "examine", "example", "exceed", "excellent", "except", "exception", "exchange", "excited", "excitement", "exciting", "exclude", "exclusive", "excuse", "execute", "execution", "executive", "exercise", "exhibit", "exhibition", "exist", "existence", "existing", "exit", "expand", "expansion", "expect", "expectation", "expected", "expense", "expensive", "experience", "experienced", "experiment", "experimental", "expert", "expertise", "explain", "explanation", "explicit", "explode", "exploit", "exploration", "explore", "explosion", "export", "expose", "exposure", "express", "expression", "extend", "extension", "extensive", "extent", "external", "extra", "extraordinary", "extreme", "extremely", "eye",
    "fabric", "face", "facility", "fact", "factor", "factory", "faculty", "fade", "fail", "failure", "fair", "fairly", "faith", "fake", "fall", "false", "fame", "familiar", "family", "famous", "fan", "fancy", "fantastic", "far", "fare", "farm", "farmer", "fashion", "fast", "fat", "fate", "father", "fault", "favor", "favorable", "favorite", "favour", "favourite", "fear", "feature", "february", "federal", "fee", "feed", "feedback", "feel", "feeling", "fellow", "female", "fence", "festival", "fetch", "fever", "few", "fiber", "fiction", "field", "fifteen", "fifth", "fifty", "fight", "fighter", "fighting", "figure", "file", "fill", "film", "filter", "final", "finally", "finance", "financial", "find", "finding", "fine", "finger", "finish", "fire", "firm", "first", "fiscal", "fish", "fishing", "fit", "fitness", "five", "fix", "fixed", "flag", "flame", "flash", "flat", "flavor", "flavour", "flee", "flesh", "flexible", "flight", "flip", "float", "flood", "floor", "flour", "flow", "flower", "fluid", "fly", "flying", "focus", "fold", "folder", "folk", "follow", "following", "food", "fool", "foot", "football", "for", "forbid", "force", "forecast", "foreign", "forest", "forever", "forget", "forgive", "fork", "form", "formal", "format", "formation", "former", "formula", "forth", "fortune", "forty", "forum", "forward", "found", "foundation", "founder", "four", "fourteen", "fourth", "frame", "framework", "free", "freedom", "freeze", "french", "frequency", "frequent", "frequently", "fresh", "friday", "fridge", "friend", "friendly", "friendship", "from", "front", "fruit", "frustrated", "fuel", "full", "fully", "fun", "function", "functional", "fund", "fundamental", "funding", "funeral", "funny", "furniture", "further", "furthermore", "future",
    "gain", "galaxy", "gallery", "game", "gaming", "gang", "gap", "garage", "garbage", "garden", "garlic", "gas", "gate", "gather", "gathering", "gay", "gaze", "gear", "gender", "gene", "general", "generally", "generate", "generation", "generous", "genetic", "genius", "genre", "gentle", "gentleman", "gently", "genuine", "get", "ghost", "giant", "gift", "gifted", "girl", "girlfriend", "give", "given", "glad", "glance", "glass", "global", "glove", "go", "goal", "god", "gold", "golden", "golf", "good", "goodbye", "goods", "govern", "government", "governor", "grab", "grace", "grade", "gradually", "graduate", "grain", "grand", "grandfather", "grandmother", "grant", "grape", "graph", "graphic", "grasp", "grass", "grateful", "grave", "gravity", "gray", "great", "greatest", "greatly", "green", "greet", "grey", "grid", "grief", "grin", "grip", "grocery", "ground", "group", "grow", "growing", "growth", "guarantee", "guard", "guess", "guest", "guide", "guideline", "guilty", "guitar", "gun", "guy", "gym",
    "habit", "habitat", "hair", "half", "hall", "halt", "hand", "handful", "handle", "handling", "handsome", "hang", "happen", "happily", "happiness", "happy", "hard", "hardly", "hardware", "harm", "harmony", "harsh", "harvest", "hat", "hate", "have", "hazard", "he", "head", "headache", "headline", "headquarters", "heal", "health", "healthy", "hear", "hearing", "heart", "heat", "heaven", "heavily", "heavy", "heel", "height", "helicopter", "hell", "hello", "helmet", "help", "helpful", "hence", "her", "herb", "here", "heritage", "hero", "hers", "herself", "hesitate", "hey", "hi", "hidden", "hide", "high", "highlight", "highly", "highway", "hill", "him", "himself", "hint", "hip", "hire", "his", "historian", "historic", "historical", "history", "hit", "hobby", "hockey", "hold", "holder", "holding", "hole", "holiday", "holy", "home", "homeless", "homework", "honest", "honestly", "honey", "honor", "honour", "hook", "hope", "hopefully", "horizon", "hormone", "horn", "horrible", "horror", "horse", "hospital", "host", "hostage", "hostile", "hot", "hotel", "hour", "house", "household", "housing", "how", "however", "huge", "human", "humor", "humour", "hundred", "hungry", "hunt", "hunter", "hunting", "hurt", "husband", "hypothesis",
    "i", "ice", "icon", "idea", "ideal", "identical", "identification", "identify", "identity", "ideology", "if", "ignore", "ill", "illegal", "illness", "illustrate", "image", "imagination", "imagine", "immediate", "immediately", "immigrant", "immigration", "impact", "implement", "implementation", "implication", "imply", "import", "importance", "important", "impose", "impossible", "impress", "impression", "impressive", "improve", "improvement", "in", "incentive", "inch", "incident", "include", "including", "income", "incorporate", "increase", "increased", "increasing", "increasingly", "incredible", "incredibly", "indeed", "independence", "independent", "index", "indicate", "indication", "indicator", "individual", "industrial", "industry", "inevitable", "infant", "infection", "inflation", "influence", "inform", "informal", "information", "infrastructure", "ingredient", "initial", "initially", "initiative", "injury", "inner", "innocent", "innovation", "innovative", "input", "inquiry", "insect", "inside", "insight", "insist", "inspect", "inspection", "inspector", "inspiration", "inspire", "install", "installation", "instance", "instant", "instantly", "instead", "instinct", "institute", "institution", "institutional", "instruct", "instruction", "instructor", "instrument", "insurance", "intellectual", "intelligence", "intelligent", "intend", "intended", "intense", "intensity", "intent", "intention", "interact", "interaction", "interactive", "interest", "interested", "interesting", "interface", "interior", "intermediate", "internal", "international", "internet", "interpret", "interpretation", "interrupt", "interval", "intervention", "interview", "into", "introduce", "introduction", "invade", "invasion", "invent", "invention", "inventory", "invest", "investigate", "investigation", "investigator", "investment", "investor", "invisible", "invitation", "invite", "invoice", "involve", "involved", "involvement", "iron", "island", "isolate", "isolated", "isolation", "issue", "it", "item", "its", "itself",
    "jacket", "jail", "jam", "january", "jazz", "jealous", "jeans", "jet", "jewelry", "job", "join", "joint", "joke", "journal", "journalism", "journalist", "journey", "joy", "judge", "judgment", "juice", "july", "jump", "june", "junior", "jury", "just", "justice", "justify",
    "keep", "key", "keyboard", "kick", "kid", "kill", "killer", "killing", "kilometer", "kind", "king", "kingdom", "kiss", "kit", "kitchen", "knee", "knife", "knock", "know", "knowledge", "known",
    "lab", "label", "labor", "laboratory", "labour", "lack", "lady", "lake", "lamp", "land", "landing", "landscape", "lane", "language", "lap", "laptop", "large", "largely", "laser", "last", "late", "later", "latest", "latter", "laugh", "laughter", "launch", "laundry", "law", "lawn", "lawsuit", "lawyer", "lay", "layer", "layout", "lazy", "lead", "leader", "leadership", "leading", "leaf", "league", "lean", "learn", "learning", "least", "leather", "leave", "lecture", "left", "leg", "legacy", "legal", "legend", "legislation", "legitimate", "lemon", "lend", "length", "lens", "less", "lesson", "let", "letter", "level", "liability", "liberal", "library", "license", "lid", "lie", "life", "lifestyle", "lifetime", "lift", "light", "lighting", "like", "likely", "limit", "limitation", "limited", "line", "link", "lion", "lip", "liquid", "list", "listen", "listener", "literally", "literary", "literature", "little", "live", "living", "load", "loading", "loan", "lobby", "local", "locate", "location", "lock", "log", "logic", "logical", "login", "logo", "lonely", "long", "look", "loop", "loose", "lord", "lose", "loss", "lost", "lot", "lots", "loud", "lounge", "love", "lovely", "lover", "low", "lower", "loyal", "luck", "lucky", "luggage", "lunch", "lung", "luxury",
    "machine", "machinery", "mad", "magazine", "magic", "mail", "main", "mainly", "maintain", "maintenance", "major", "majority", "make", "maker", "makeup", "male", "mall", "man", "manage", "management", "manager", "managing", "mandate", "mandatory", "manipulate", "manner", "manual", "manufacture", "manufacturer", "manufacturing", "many", "map", "mapping", "march", "margin", "marine", "mark", "market", "marketing", "marketplace", "marriage", "married", "marry", "mask", "mass", "massive", "master", "match", "mate", "material", "math", "mathematics", "matrix", "matter", "maximum", "may", "maybe", "mayor", "me", "meal", "mean", "meaning", "meanwhile", "measure", "measurement", "meat", "mechanic", "mechanical", "mechanism", "medal", "media", "medical", "medication", "medicine", "medium", "meet", "meeting", "melt", "member", "membership", "memory", "mental", "mention", "mentor", "menu", "merchant", "mere", "merely", "merge", "merger", "merit", "mess", "message", "messaging", "metal", "meter", "method", "methodology", "metro", "middle", "midnight", "might", "migration", "mild", "military", "milk", "mill", "million", "mind", "mine", "mineral", "minimal", "minimize", "minimum", "minister", "ministry", "minor", "minority", "minute", "miracle", "mirror", "miss", "missile", "missing", "mission", "mistake", "mix", "mixed", "mixture", "mobile", "mode", "model", "moderate", "modern", "modest", "modify", "module", "mom", "moment", "monday", "money", "monitor", "monitoring", "monkey", "month", "monthly", "mood", "moon", "moral", "more", "moreover", "morning", "mortgage", "most", "mostly", "mother", "motion", "motivate", "motivation", "motor", "mount", "mountain", "mouse", "mouth", "move", "movement", "movie", "much", "mud", "multiple", "multiply", "mum", "murder", "muscle", "museum", "music", "musical", "musician", "must", "mutual", "my", "myself", "mystery", "myth",
    "nail", "naked", "name", "narrative", "narrow", "nation", "national", "native", "natural", "naturally", "nature", "navy", "near", "nearby", "nearly", "neat", "necessarily", "necessary", "neck", "need", "needle", "negative", "negotiate", "negotiation", "neighbor", "neighborhood", "neighbour", "neither", "nerve", "nervous", "net", "network", "networking", "neutral", "never", "nevertheless", "new", "newly", "news", "newspaper", "next", "nice", "nicely", "night", "nine", "nineteen", "ninety", "no", "nobody", "nod", "noise", "nominal", "nominate", "none", "nonetheless", "noon", "nor", "normal", "normally", "north", "northern", "nose", "not", "note", "notebook", "nothing", "notice", "notification", "notify", "notion", "novel", "november", "now", "nowadays", "nowhere", "nuclear", "number", "numerous", "nurse", "nut",
    "object", "objective", "obligation", "observation", "observe", "observer", "obstacle", "obtain", "obvious", "obviously", "occasion", "occasional", "occasionally", "occupation", "occupy", "occur", "ocean", "october", "odd", "odds", "of", "off", "offence", "offend", "offense", "offensive", "offer", "offering", "office", "officer", "official", "officially", "offline", "offset", "often", "oh", "oil", "ok", "okay", "old", "on", "once", "one", "ongoing", "onion", "online", "only", "onto", "open", "opening", "openly", "opera", "operate", "operating", "operation", "operational", "operator", "opinion", "opponent", "opportunity", "oppose", "opposite", "opposition", "opt", "optical", "optimistic", "optimize", "option", "optional", "or", "oral", "orange", "orbit", "order", "ordinary", "organ", "organic", "organization", "organizational", "organize", "orientation", "origin", "original", "originally", "other", "otherwise", "ought", "our", "ours", "ourselves", "out", "outcome", "outdoor", "outer", "outfit", "outlet", "outline", "output", "outside", "outsider", "outstanding", "oven", "over", "overall", "overcome", "overlook", "overnight", "overseas", "oversee", "overtime", "overview", "owe", "own", "owner", "ownership", "oxygen",
    "pace", "pack", "package", "packaging", "packet", "pad", "page", "pain", "painful", "paint", "painter", "painting", "pair", "palace", "pale", "palm", "pan", "panel", "panic", "pants", "paper", "parade", "paragraph", "parallel", "parameter", "parent", "park", "parking", "parliament", "part", "participant", "participate", "participation", "particular", "particularly", "partly", "partner", "partnership", "party", "pass", "passage", "passenger", "passion", "passive", "passport", "password", "past", "paste", "pat", "patch", "patent", "path", "patience", "patient", "pattern", "pause", "pay", "payment", "payroll", "pc", "peace", "peaceful", "peak", "peer", "pen", "penalty", "pencil", "pending", "pension", "people", "pepper", "per", "perceive", "percent", "percentage", "perception", "perfect", "perfectly", "perform", "performance", "performer", "perhaps", "period", "permanent", "permission", "permit", "person", "personal", "personality", "personally", "personnel", "perspective", "persuade", "pet", "phase", "phenomenon", "philosophy", "phone", "photo", "photograph", "photographer", "photography", "phrase", "physical", "physically", "physician", "physics", "piano", "pick", "pickup", "picture", "pie", "piece", "pig", "pile", "pill", "pilot", "pin", "pink", "pioneer", "pipe", "pipeline", "pitch", "pity", "place", "placement", "plain", "plan", "plane", "planet", "planning", "plant", "plastic", "plate", "platform", "play", "player", "pleasant", "please", "pleased", "pleasure", "plenty", "plot", "plug", "plugin", "plus", "pm", "pocket", "poem", "poet", "poetry", "point", "pointer", "poison", "pole", "police", "policy", "polish", "polite", "political", "politician", "politics", "poll", "pollution", "pond", "pool", "poor", "pop", "popular", "popularity", "population", "porch", "pork", "port", "portfolio", "portion", "portrait", "portray", "pose", "position", "positive", "possess", "possession", "possibility", "possible", "possibly", "post", "poster", "pot", "potato", "potential", "potentially", "pound", "pour", "poverty", "powder", "power", "powerful", "practical", "practice", "practitioner", "praise", "pray", "prayer", "precise", "precisely", "predict", "prediction", "prefer", "preference", "pregnancy", "pregnant", "preliminary", "premise", "premium", "preparation", "prepare", "prepared", "prescription", "presence", "present", "presentation", "preserve", "president", "presidential", "press", "pressure", "pretend", "pretty", "prevail", "prevent", "prevention", "preview", "previous", "previously", "price", "pricing", "pride", "priest", "primarily", "primary", "prime", "principal", "principle", "print", "printer", "printing", "prior", "priority", "prison", "prisoner", "privacy", "private", "privilege", "prize", "pro", "probably", "problem", "procedure", "proceed", "process", "processing", "processor", "proclaim", "produce", "producer", "product", "production", "productive", "productivity", "profession", "professional", "professor", "profile", "profit", "profitable", "profound", "program", "programme", "programmer", "programming", "progress", "progressive", "prohibit", "project", "projection", "prominent", "promise", "promote", "promotion", "prompt", "proof", "proper", "properly", "property", "proportion", "proposal", "propose", "proposed", "prosecutor", "prospect", "protect", "protection", "protein", "protest", "protocol", "proud", "prove", "provide", "provider", "province", "provision", "psychological", "psychology", "public", "publication", "publicity", "publicly", "publish", "publisher", "publishing", "pull", "pulse", "pump", "punch", "punish", "punishment", "purchase", "pure", "purple", "purpose", "pursue", "pursuit", "push", "put", "puzzle",
    "qualify", "quality", "quantity", "quarter", "queen", "query", "quest", "question", "queue", "quick", "quickly", "quiet", "quietly", "quit", "quite", "quiz", "quota", "quote",
    "race", "racial", "rack", "radar", "radiation", "radical", "radio", "rage", "rail", "railway", "rain", "raise", "rally", "random", "range", "rank", "ranking", "rapid", "rapidly", "rare", "rarely", "rate", "rather", "rating", "ratio", "raw", "ray", "reach", "react", "reaction", "read", "reader", "readily", "reading", "ready", "real", "realistic", "reality", "realize", "really", "realm", "rear", "reason", "reasonable", "rebel", "rebuild", "recall", "receipt", "receive", "receiver", "recent", "recently", "reception", "recipe", "recipient", "recognition", "recognize", "recommend", "recommendation", "record", "recording", "recover", "recovery", "recruit", "recruitment", "red", "reduce", "reduction", "refer", "reference", "reflect", "reflection", "reform", "refrigerator", "refugee", "refund", "refusal", "refuse", "regard", "regarding", "regardless", "regime", "region", "regional", "register", "registration", "regret", "regular", "regularly", "regulate", "regulation", "regulator", "regulatory", "reinforce", "reject", "rejection", "relate", "related", "relation", "relationship", "relative", "relatively", "relax", "release", "relevant", "reliability", "reliable", "relief", "relieve", "religion", "religious", "reluctant", "rely", "remain", "remaining", "remark", "remarkable", "remedy", "remember", "remind", "reminder", "remote", "removal", "remove", "render", "renew", "rent", "rental", "repair", "repeat", "repeatedly", "replace", "replacement", "reply", "report", "reporter", "reporting", "represent", "representation", "representative", "reproduce", "republic", "reputation", "request", "require", "requirement", "rescue", "research", "researcher", "resemble", "reservation", "reserve", "residence", "resident", "residential", "resign", "resignation", "resist", "resistance", "resolution", "resolve", "resort", "resource", "respect", "respective", "respectively", "respond", "respondent", "response", "responsibility", "responsible", "rest", "restaurant", "restore", "restrict", "restriction", "result", "resume", "retail", "retailer", "retain", "retire", "retirement", "retreat", "retrieve", "return", "reveal", "revenue", "reverse", "review", "reviewer", "revise", "revision", "revolution", "reward", "rhythm", "rice", "rich", "rid", "ride", "rider", "ridge", "ridiculous", "rifle", "right", "ring", "riot", "rip", "rise", "risk", "risky", "ritual", "rival", "river", "road", "rob", "robot", "rock", "rocket", "rod", "role", "roll", "romantic", "roof", "room", "root", "rope", "rose", "rough", "roughly", "round", "route", "routine", "row", "royal", "rub", "rubber", "rude", "ruin", "rule", "ruler", "rumor", "run", "runner", "running", "rural", "rush",
    "sack", "sacred", "sacrifice", "sad", "safe", "safety", "sail", "sake", "salad", "salary", "sale", "sales", "salt", "same", "sample", "sanction", "sand", "sandwich", "satellite", "satisfaction", "satisfy", "saturday", "sauce", "save", "saving", "say", "scale", "scan", "scandal", "scanner", "scared", "scary", "scatter", "scenario", "scene", "schedule", "scheme", "scholar", "scholarship", "school", "science", "scientific", "scientist", "scope", "score", "scratch", "scream", "screen", "screening", "script", "scroll", "sea", "seal", "search", "season", "seat", "second", "secondary", "secret", "secretary", "section", "sector", "secure", "security", "see", "seed", "seek", "seem", "segment", "seize", "select", "selection", "self", "sell", "seller", "seminar", "senate", "senator", "send", "sender", "senior", "sense", "sensitive", "sentence", "separate", "separately", "september", "sequence", "series", "serious", "seriously", "servant", "serve", "server", "service", "session", "set", "setting", "settle", "settlement", "seven", "seventeen", "seventy", "several", "severe", "sex", "sexual", "shade", "shadow", "shake", "shall", "shallow", "shame", "shape", "share", "shareholder", "sharp", "she", "sheep", "sheet", "shelf", "shell", "shelter", "shift", "shine", "ship", "shipping", "shirt", "shock", "shoe", "shoot", "shooting", "shop", "shopping", "shore", "short", "shortage", "shortly", "shot", "should", "shoulder", "shout", "show", "shower", "shut", "shy", "sick", "side", "sigh", "sight", "sign", "signal", "signature", "significance", "significant", "significantly", "silence", "silent", "silk", "silly", "silver", "similar", "similarly", "simple", "simply", "simulate", "simulation", "simultaneously", "sin", "since", "sing", "singer", "single", "sink", "sir", "sister", "sit", "site", "situation", "six", "sixteen", "sixty", "size", "ski", "skill", "skilled", "skin", "skip", "skirt", "sky", "slave", "sleep", "slice", "slide", "slight", "slightly", "slip", "slope", "slot", "slow", "slowly", "small", "smart", "smartphone", "smash", "smell", "smile", "smoke", "smoking", "smooth", "snack", "snake", "snap", "snow", "so", "soap", "soccer", "social", "society", "sock", "soft", "software", "soil", "solar", "soldier", "sole", "solely", "solid", "solution", "solve", "some", "somebody", "somehow", "someone", "something", "sometimes", "somewhat", "somewhere", "son", "song", "soon", "sophisticated", "sorry", "sort", "soul", "sound", "soup", "source", "south", "southern", "space", "spam", "span", "spare", "spark", "speak", "speaker", "special", "specialist", "specialize", "species", "specific", "specifically", "specification", "specify", "specimen", "spectacular", "spectrum", "speculate", "speech", "speed", "spell", "spelling", "spend", "spending", "sphere", "spice", "spicy", "spider", "spill", "spin", "spirit", "spiritual", "split", "spoil", "spokesman", "sponsor", "spoon", "sport", "spot", "spouse", "spread", "spreadsheet", "spring", "spy", "squad", "square", "squeeze", "stability", "stable", "stadium", "staff", "stage", "stair", "stake", "stakeholder", "stall", "stamp", "stand", "standard", "standing", "star", "stare", "start", "starter", "startup", "state", "statement", "station", "statistical", "statistics", "statue", "status", "stay", "steady", "steak", "steal", "steam", "steel", "steep", "steer", "stem", "step", "stick", "sticky", "stiff", "still", "stimulate", "stir", "stock", "stomach", "stone", "stop", "storage", "store", "storm", "story", "stove", "straight", "strain", "strange", "stranger", "strategic", "strategy", "straw", "stream", "street", "strength", "strengthen", "stress", "stretch", "strict", "strictly", "strike", "string", "strip", "stroke", "strong", "strongly", "structural", "structure", "struggle", "student", "studio", "study", "stuff", "stumble", "stupid", "style", "subject", "submit", "subsequent", "subsidy", "substance", "substantial", "substitute", "subtle", "suburb", "succeed", "success", "successful", "successfully", "such", "suck", "sudden", "suddenly", "sue", "suffer", "sufficient", "sugar", "suggest", "suggestion", "suicide", "suit", "suitable", "suite", "sum", "summarize", "summary", "summer", "summit", "sun", "sunday", "super", "superior", "supermarket", "supervisor", "supplement", "supplier", "supply", "support", "supporter", "suppose", "supposed", "supreme", "sure", "surely", "surface", "surgery", "surprise", "surprised", "surprising", "surround", "surrounding", "survey", "survival", "survive", "survivor", "suspect", "suspend", "suspicion", "suspicious", "sustain", "sustainable", "swallow", "swear", "sweat", "sweep", "sweet", "swim", "swimming", "swing", "switch", "sword", "symbol", "sympathy", "symptom", "sync", "syndrome", "system",
    "table", "tablet", "tackle", "tactic", "tag", "tail", "take", "tale", "talent", "talented", "talk", "tall", "tank", "tap", "tape", "target", "task", "taste", "tax", "taxpayer", "tea", "teach", "teacher", "teaching", "team", "tear", "tech", "technical", "technician", "technique", "technology", "teen", "teenager", "telephone", "television", "tell", "temperature", "template", "temple", "temporary", "ten", "tenant", "tend", "tendency", "tender", "tennis", "tension", "tent", "term", "terminal", "terminate", "terms", "terrible", "territory", "terror", "terrorism", "terrorist", "test", "testify", "testimony", "testing", "text", "textbook", "texture", "than", "thank", "thanks", "that", "the", "theater", "theatre", "their", "theirs", "them", "theme", "themselves", "then", "theory", "therapy", "there", "therefore", "these", "they", "thick", "thigh", "thin", "thing", "think", "thinking", "third", "thirsty", "thirteen", "thirty", "this", "those", "though", "thought", "thousand", "thread", "threat", "threaten", "three", "threshold", "throat", "through", "throughout", "throw", "thumb", "thursday", "thus", "ticket", "tide", "tie", "tight", "tile", "till", "time", "timeline", "timer", "timing", "tin", "tiny", "tip", "tire", "tired", "tissue", "title", "to", "toast", "tobacco", "today", "toe", "together", "toilet", "token", "tomato", "tomorrow", "tone", "tongue", "tonight", "too", "tool", "tooth", "top", "topic", "toss", "total", "totally", "touch", "tough", "tour", "tourism", "tourist", "tournament", "toward", "towards", "towel", "tower", "town", "toy", "trace", "track", "tracking", "trade", "trading", "tradition", "traditional", "traffic", "tragedy", "trail", "trailer", "train", "trainer", "training", "trait", "transaction", "transfer", "transform", "transformation", "transition", "translate", "translation", "transmission", "transmit", "transport", "transportation", "trap", "trash", "trauma", "travel", "traveler", "tray", "treasure", "treat", "treatment", "treaty", "tree", "tremendous", "trend", "trial", "tribe", "trick", "trigger", "trim", "trip", "troop", "tropical", "trouble", "truck", "true", "truly", "trust", "truth", "try", "tube", "tuesday", "tuition", "tune", "tunnel", "turn", "turnover", "tv", "twelve", "twenty", "twice", "twin", "twist", "two", "type", "typical", "typically",
    "ugly", "ultimate", "ultimately", "unable", "uncle", "under", "undergo", "understand", "understanding", "undertake", "unemployment", "unexpected", "unfair", "unfold", "unfortunately", "unhappy", "uniform", "union", "unique", "unit", "unite", "united", "universal", "universe", "university", "unknown", "unless", "unlike", "unlikely", "unlimited", "unlock", "until", "unusual", "up", "update", "upgrade", "upload", "upon", "upper", "upset", "upstairs", "urban", "urge", "urgent", "us", "usage", "use", "used", "useful", "user", "usual", "usually", "utility", "utilize",
    "vacation", "vaccine", "valid", "validate", "validation", "valley", "valuable", "value", "van", "variable", "variation", "variety", "various", "vary", "vast", "vegetable", "vehicle", "vendor", "venture", "venue", "verbal", "verdict", "verify", "version", "versus", "vertical", "very", "vessel", "veteran", "via", "victim", "victory", "video", "view", "viewer", "village", "violate", "violation", "violence", "violent", "virtual", "virtually", "virtue", "virus", "visa", "visible", "vision", "visit", "visitor", "visual", "vital", "vitamin", "voice", "volume", "volunteer", "vote", "voter", "voucher", "vulnerable",
    "wage", "wait", "waiter", "wake", "walk", "wall", "wallet", "wander", "want", "war", "warm", "warn", "warning", "warranty", "wash", "waste", "watch", "water", "wave", "way", "we", "weak", "weakness", "wealth", "wealthy", "weapon", "wear", "weather", "web", "website", "wedding", "wednesday", "week", "weekend", "weekly", "weigh", "weight", "weird", "welcome", "welfare", "well", "west", "western", "wet", "what", "whatever", "wheat", "wheel", "when", "whenever", "where", "whereas", "wherever", "whether", "which", "while", "whisper", "white", "who", "whole", "whom", "whose", "why", "wide", "widely", "widespread", "wife", "wifi", "wild", "will", "willing", "win", "wind", "window", "wine", "wing", "winner", "winter", "wipe", "wire", "wireless", "wisdom", "wise", "wish", "with", "withdraw", "withdrawal", "within", "without", "witness", "woman", "wonder", "wonderful", "wood", "wooden", "wool", "word", "work", "worker", "workflow", "working", "workout", "workplace", "workshop", "world", "worldwide", "worm", "worried", "worry", "worse", "worship", "worst", "worth", "would", "wound", "wrap", "wrist", "write", "writer", "writing", "wrong",
    "yard", "yeah", "year", "yearly", "yell", "yellow", "yes", "yesterday", "yet", "yield", "you", "young", "your", "yours", "yourself", "youth",
    "zero", "zone", "zoom",
}

# ============================================================================
# 5. KATA NAMA KHAS (PROPER NOUNS) & AKRONIM RESMI (Untuk Huruf Kapital)
# ============================================================================
PROPER_NOUNS: Dict[str, str] = {
    # Hari dalam Bahasa Melayu (Wajib Huruf Besar di PRPM/DBP)
    "isnin": "Isnin",
    "selasa": "Selasa",
    "rabu": "Rabu",
    "khamis": "Khamis",
    "jumaat": "Jumaat",
    "sabtu": "Sabtu",
    "ahad": "Ahad",
    # Bulan dalam Bahasa Melayu
    "januari": "Januari",
    "februari": "Februari",
    "mac": "Mac",
    "april": "April",
    "mei": "Mei",
    "jun": "Jun",
    "julai": "Julai",
    "ogos": "Ogos",
    "september": "September",
    "oktober": "Oktober",
    "november": "November",
    "disember": "Disember",
    # Negara, Negeri & Bandar Utama Malaysia
    "malaysia": "Malaysia",
    "indonesia": "Indonesia",
    "singapura": "Singapura",
    "brunei": "Brunei",
    "thailand": "Thailand",
    "johor": "Johor",
    "kedah": "Kedah",
    "kelantan": "Kelantan",
    "melaka": "Melaka",
    "pahang": "Pahang",
    "perak": "Perak",
    "perlis": "Perlis",
    "pulau pinang": "Pulau Pinang",
    "sabah": "Sabah",
    "sarawak": "Sarawak",
    "selangor": "Selangor",
    "terengganu": "Terengganu",
    "kuala lumpur": "Kuala Lumpur",
    "putrajaya": "Putrajaya",
    "labuan": "Labuan",
    "shah alam": "Shah Alam",
    "petaling jaya": "Petaling Jaya",
    "subang jaya": "Subang Jaya",
    "cyberjaya": "Cyberjaya",
    "ipoh": "Ipoh",
    "kuching": "Kuching",
    "kota kinabalu": "Kota Kinabalu",
    "kuantan": "Kuantan",
    "seremban": "Seremban",
    "alor setar": "Alor Setar",
    "kota bharu": "Kota Bharu",
    "langkawi": "Langkawi",
    "klang": "Klang",
    "ampang": "Ampang",
    "cheras": "Cheras",
    "bangi": "Bangi",
    "kajang": "Kajang",
    "puchong": "Puchong",
    "damansara": "Damansara",
    "miri": "Miri",
    "sibu": "Sibu",
    "tawau": "Tawau",
    "sandakan": "Sandakan",
    "muar": "Muar",
    "batu pahat": "Batu Pahat",
    "port dickson": "Port Dickson",
    "george town": "George Town",
    "kuala terengganu": "Kuala Terengganu",
    "sungai petani": "Sungai Petani",
    # Bahasa, Bangsa, Agama & Perayaan (Wajib Huruf Kapital)
    "melayu": "Melayu",
    "inggris": "Inggeris",
    "inggeris": "Inggeris",
    "bahasa melayu": "Bahasa Melayu",
    "bahasa inggeris": "Bahasa Inggeris",
    "islam": "Islam",
    "allah": "Allah",
    "ramadan": "Ramadan",
    "syawal": "Syawal",
    "aidilfitri": "Aidilfitri",
    "aidiladha": "Aidiladha",
    "merdeka": "Merdeka",
    # Jenama Teknologi, Bank & Nama Orang Lazim
    "google": "Google",
    "google chrome": "Google Chrome",
    "google meet": "Google Meet",
    "whatsapp": "WhatsApp",
    "microsoft": "Microsoft",
    "microsoft word": "Microsoft Word",
    "microsoft excel": "Microsoft Excel",
    "microsoft teams": "Microsoft Teams",
    "powerpoint": "PowerPoint",
    "youtube": "YouTube",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "telegram": "Telegram",
    "shopee": "Shopee",
    "lazada": "Lazada",
    "iphone": "iPhone",
    "ipad": "iPad",
    "ios": "iOS",
    "android": "Android",
    "maybank": "Maybank",
    "cimb": "CIMB",
    "ahmad": "Ahmad",
    "ali": "Ali",
    "abu": "Abu",
    "siti": "Siti",
    "aminah": "Aminah",
    "farah": "Farah",
    "hafiz": "Hafiz",
    "aisyah": "Aisyah",
}

ACRONYMS: Set[str] = {
    "PRPM", "DBP", "KL", "RM", "MYR", "USD", "SGD", "IDR",
    "JPN", "KPM", "KKM", "KDN", "JPJ", "PDRM", "SPRM", "KWSP", "PERKESO", "LHDN",
    "TM", "TNB", "MARA", "FELDA", "PETRONAS", "PROTON", "PERODUA", "CIMB",
    "UM", "UKM", "UPM", "USM", "UTM", "UiTM", "UIAM", "UUM", "UNIMAS", "UMS",
    "SPM", "STPM", "PT3", "UPSR", "MUET", "IPTA", "IPTS",
    "CEO", "CTO", "CFO", "COO", "HR", "IT", "AI", "API", "SQL", "CLI", "GUI", "PDF", "CSV", "JSON", "HTML", "CSS", "URL", "USB", "RAM", "CPU", "GPU", "SOP", "KPI", "FAQ", "VIP", "CCTV", "ATM", "SIM", "PIN", "OTP", "WIFI",
}


def _ensure_source_columns(conn: sqlite3.Connection) -> None:
    """Migrasi otomatis kolom 'source' pada database versi sebelumnya tanpa menghapus data pengguna."""
    tables = (
        "prpm_words",
        "ms_standardization",
        "compound_rules",
        "english_words",
        "proper_nouns",
        "acronyms",
    )
    cur = conn.cursor()
    for table in tables:
        cols = {row[1] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()}
        if "source" not in cols:
            cur.execute(
                f"ALTER TABLE {table} ADD COLUMN source TEXT NOT NULL DEFAULT 'seed'"
            )
    conn.commit()


def _seed_all_tables(conn: sqlite3.Connection) -> None:
    """Mengisi seluruh entri bawaan ('seed') dengan mempertahankan entri 'user' dan 'sync'."""
    cur = conn.cursor()

    # Hapus entri bawaan ('seed') lama agar aturan yang dihapus/diperbarui ikut bersih
    for table in (
        "prpm_words",
        "ms_standardization",
        "compound_rules",
        "english_words",
        "proper_nouns",
        "acronyms",
    ):
        cur.execute(f"DELETE FROM {table} WHERE source = 'seed'")

    # Pastikan kata yang kini dibakukan di MS_STANDARDIZATION tidak tertinggal sebagai kata baku
    non_std_keys = set(k.lower() for k in MS_STANDARDIZATION.keys()) | {"pasal"}
    for k in non_std_keys:
        cur.execute("DELETE FROM prpm_words WHERE word = ? AND source != 'user'", (k,))

    all_prpm_words = set(w.lower() for w in PRPM_WORDS)
    for _, (std_w, _) in MS_STANDARDIZATION.items():
        for token in std_w.lower().split():
            all_prpm_words.add(token)
    for lower_proper in PROPER_NOUNS.keys():
        for token in lower_proper.lower().split():
            all_prpm_words.add(token)

    cur.executemany(
        "INSERT OR IGNORE INTO prpm_words (word, source) VALUES (?, 'seed')",
        [(w,) for w in sorted(all_prpm_words)],
    )

    cur.executemany(
        "INSERT OR IGNORE INTO ms_standardization (non_standard, standard_word, reason, source) VALUES (?, ?, ?, 'seed')",
        [(k.lower(), v[0], v[1]) for k, v in MS_STANDARDIZATION.items()],
    )

    compound_rows = []
    for wrong_p, right_p in KATA_MAJMUK_MANTAP_DBP.items():
        compound_rows.append(
            (
                wrong_p.lower(),
                right_p,
                f"Mengikut Tatabahasa Dewan (PRPM DBP), '{right_p}' ialah kata majmuk mantap yang wajib ditulis rapat.",
            )
        )
    cur.executemany(
        "INSERT OR IGNORE INTO compound_rules (wrong_phrase, correct_phrase, reason, source) VALUES (?, ?, ?, 'seed')",
        compound_rows,
    )

    cur.executemany(
        "INSERT OR IGNORE INTO english_words (word, source) VALUES (?, 'seed')",
        [(w.lower(),) for w in sorted(ENGLISH_WORDS)],
    )

    cur.executemany(
        "INSERT OR IGNORE INTO proper_nouns (lower_form, proper_form, source) VALUES (?, ?, 'seed')",
        [(k.lower(), v) for k, v in PROPER_NOUNS.items()],
    )

    cur.executemany(
        "INSERT OR IGNORE INTO acronyms (acronym, source) VALUES (?, 'seed')",
        [(a,) for a in sorted(ACRONYMS)],
    )
    conn.commit()


def init_database(db_path: str = DB_PATH, force_rebuild: bool = False) -> str:
    """Inisialisasi atau bangun ulang database SQLite offline PRPM."""
    if os.path.exists(db_path) and not force_rebuild:
        conn = sqlite3.connect(db_path)
        _ensure_source_columns(conn)
        conn.close()
        return db_path

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        DROP TABLE IF EXISTS prpm_words;
        DROP TABLE IF EXISTS ms_standardization;
        DROP TABLE IF EXISTS compound_rules;
        DROP TABLE IF EXISTS english_words;
        DROP TABLE IF EXISTS proper_nouns;
        DROP TABLE IF EXISTS acronyms;

        CREATE TABLE prpm_words (
            word TEXT PRIMARY KEY,
            source TEXT NOT NULL DEFAULT 'seed'
        );

        CREATE TABLE ms_standardization (
            non_standard TEXT PRIMARY KEY,
            standard_word TEXT NOT NULL,
            reason TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'seed'
        );

        CREATE TABLE compound_rules (
            wrong_phrase TEXT PRIMARY KEY,
            correct_phrase TEXT NOT NULL,
            reason TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'seed'
        );

        CREATE TABLE english_words (
            word TEXT PRIMARY KEY,
            source TEXT NOT NULL DEFAULT 'seed'
        );

        CREATE TABLE proper_nouns (
            lower_form TEXT PRIMARY KEY,
            proper_form TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'seed'
        );

        CREATE TABLE acronyms (
            acronym TEXT PRIMARY KEY,
            source TEXT NOT NULL DEFAULT 'seed'
        );
        """
    )

    _seed_all_tables(conn)
    conn.close()
    return db_path


def upgrade_seed_database(db_path: str = DB_PATH) -> str:
    """Memperbarui kamus bawaan ('seed') tanpa menghapus kata tambahan pengguna ('user') dan hasil sinkronisasi ('sync')."""
    if not os.path.exists(db_path):
        return init_database(db_path, force_rebuild=True)
    conn = sqlite3.connect(db_path)
    _ensure_source_columns(conn)
    _seed_all_tables(conn)
    conn.close()
    return db_path


def get_database_stats(db_path: str = DB_PATH) -> Dict[str, int]:
    """Mengembalikan jumlah entri pada tiap tabel di database SQLite offline."""
    init_database(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    stats: Dict[str, int] = {}
    for table in (
        "prpm_words",
        "ms_standardization",
        "compound_rules",
        "english_words",
        "proper_nouns",
        "acronyms",
    ):
        stats[table] = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return stats


if __name__ == "__main__":
    path = init_database(force_rebuild=True)
    print(f"Database PRPM Offline berhasil dibangun di: {path}")
