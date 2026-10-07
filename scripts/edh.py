"""Завантаження відкритих даних EDH (Гейдельберг) і відбір за країнами та датою."""
import csv, io, re, tempfile, urllib.request, zipfile
from pathlib import Path

BASE = "https://edh.ub.uni-heidelberg.de/data/download/"
OUT = Path(__file__).resolve().parent.parent / "data" / "написи" / "edh"
КРАЇНИ = {"ua", "pl", "ro", "bg", "cz", "ru"}
csv.field_size_limit(10**9)


def get(name):
    return urllib.request.urlopen(urllib.request.Request(BASE + name, headers={"User-Agent": "ancient-texts-research"}), timeout=300).read()


def main():
    rows = csv.DictReader(io.StringIO(get("edh_data_text.csv").decode("utf-8")))
    вибір = [r for r in rows if r["land"].rstrip("?") in КРАЇНИ and (r["dat_jahr_e"] or "0").lstrip("-").isdigit() and int(r["dat_jahr_e"] or 0) <= 800]
    with open(OUT / "inscriptions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, вибір[0].keys())
        w.writeheader()
        w.writerows(вибір)
    ids = {r["hd_nr"] for r in вибір}
    print("записів", len(вибір))
    index = get("edhEpidocDump_HD000001-HD010000.zip")  # перевірка імен у архіві
    names = zipfile.ZipFile(io.BytesIO(index)).namelist()[:2]
    print("приклад імен", names)
    for i in range(9):
        lo = i * 10000 + 1
        hi = (i + 1) * 10000 if i < 8 else 82828
        z = zipfile.ZipFile(io.BytesIO(index if i == 0 else get(f"edhEpidocDump_HD{lo:06d}-HD{hi:06d}.zip")))
        for n in z.namelist():
            m = re.search(r"(HD\d{6})", n)
            if m and m.group(1) in ids:
                (OUT / "xml" / f"{m.group(1)}.xml").write_bytes(z.read(n))


if __name__ == "__main__":
    main()
