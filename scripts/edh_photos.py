"""Завантаження фото написів EDH через IIIF (heidicon.ub.uni-heidelberg.de), пауза 1 с."""
import csv, io, time, urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data" / "написи" / "edh"
КРАЇНИ = {"ua": "Україна", "ro": "Румунія", "bg": "Болгарія", "cz": "Чехія", "pl": "Польща"}
csv.field_size_limit(10**9)
UA = {"User-Agent": "ancient-texts-research (+https://github.com/wku/dp-claude)"}


def get(url):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except Exception:
            time.sleep(15 * (i + 1))


ins = {r["hd_nr"]: r for r in csv.DictReader(open(D / "inscriptions.csv", encoding="utf-8"))}
foto = csv.DictReader(io.StringIO(get("https://edh.ub.uni-heidelberg.de/data/download/edh_data_foto.csv").decode("utf-8")))
лічильник = {}
for f in foto:
    hd = f["hd_nr"]
    if hd not in ins or not f["heidicon_iiif"]:
        continue
    лічильник[hd] = лічильник.get(hd, 0) + 1
    out = D / "документи" / КРАЇНИ[ins[hd]["land"].rstrip("?")]
    out.mkdir(parents=True, exist_ok=True)
    файл = out / (f"{hd}.jpg" if лічильник[hd] == 1 else f"{hd}_{лічильник[hd]}.jpg")
    if not файл.exists():
        img = get(f["heidicon_iiif"] + "/full/full/0/default.jpg")
        if img:
            файл.write_bytes(img)
        time.sleep(1)
