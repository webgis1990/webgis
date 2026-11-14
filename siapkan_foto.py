"""
Siapkan foto bidang untuk WebGIS ASTRA.
Fungsi: perkecil foto (lebar maks 1200 px, JPG, target 200-300 KB), beri nama ID08_1.jpg dst,
        hapus data EXIF (termasuk GPS) dari berkas hasil, dan buat data/foto.json.

Cara pakai (Python bawaan ArcGIS Pro sudah punya Pillow):
 1. Beri nama foto asli: ID08_1.jpg, ID08_2.jpg, ID10_1.jpg, dst (angka = ID bidang, urutan = nomor foto).
    Urutan yang disarankan: 1 = tampak keseluruhan, 2 = batas/papan aset, 3 = akses masuk.
 2. Ubah SUMBER dan REPO di bawah, lalu jalankan di Python window ArcGIS Pro atau dengan propy.bat.
"""
import os, re, json, datetime
from PIL import Image, ImageOps

SUMBER = r"E:\Joki\foto_asli"        # folder foto asli dari survei
REPO   = r"E:\Joki\paket"            # folder yang berisi index.html
LEBAR, KUALITAS_AWAL, MAKS_KB = 1200, 82, 300
KET = ["Tampak keseluruhan bidang", "Batas atau papan aset", "Akses jalan masuk"]

out_img = os.path.join(REPO, "img", "bidang"); os.makedirs(out_img, exist_ok=True)
os.makedirs(os.path.join(REPO, "data"), exist_ok=True)
pola = re.compile(r"^ID0*(\d+)_(\d+)\.(jpe?g|png|webp)$", re.I)

def tanggal(im, path):
    try:
        ex = im.getexif().get_ifd(0x8769)
        t = ex.get(36867) or im.getexif().get(306)
        if t: return datetime.datetime.strptime(str(t)[:19], "%Y:%m:%d %H:%M:%S").date().isoformat()
    except Exception: pass
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()

data, ada = {}, set()
for nama in sorted(os.listdir(SUMBER)):
    m = pola.match(nama)
    if not m:
        print("Dilewati (nama tidak sesuai pola IDxx_n.jpg):", nama); continue
    id_, no = int(m.group(1)), int(m.group(2)); sumber = os.path.join(SUMBER, nama)
    im = Image.open(sumber); tgl = tanggal(im, sumber)
    im = ImageOps.exif_transpose(im).convert("RGB")      # putar sesuai orientasi, lalu EXIF dibuang
    if im.width > LEBAR: im = im.resize((LEBAR, round(im.height * LEBAR / im.width)), Image.LANCZOS)
    tujuan = os.path.join(out_img, "ID%02d_%d.jpg" % (id_, no)); q = KUALITAS_AWAL
    while True:
        im.save(tujuan, "JPEG", quality=q, optimize=True, progressive=True)
        if os.path.getsize(tujuan) <= MAKS_KB * 1024 or q <= 60: break
        q -= 6
    e = data.setdefault(str(id_), {"tgl": tgl, "files": [], "ket": []})
    e["files"].append("img/bidang/" + os.path.basename(tujuan)); e["ket"].append(KET[no-1] if no <= len(KET) else "")
    e["tgl"] = min(e["tgl"], tgl); ada.add(id_)
    print("OK", nama, "->", os.path.basename(tujuan), round(os.path.getsize(tujuan)/1024), "KB, kualitas", q)

with open(os.path.join(REPO, "data", "foto.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
kosong = [i for i in range(1, 16) if i not in ada]
print("\nBidang dengan foto: %d dari 15" % len(ada))
print("Bidang TANPA foto:", kosong if kosong else "tidak ada")
