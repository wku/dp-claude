"""Індекс надписів IOSPE з файлів EpiDoc XML, які покладено вручну в data/iospe/xml.
Файли потрібно отримати від авторів проєкту або завантажити вручну в браузері.
Скрипт сам нічого з сайту не завантажує (robots.txt сайту забороняє автоматичний обхід)."""
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "iospe"
NS = "{http://www.tei-c.org/ns/1.0}"
LANG = "{http://www.w3.org/XML/1.1/namespace}lang"


def txt(e):
    return " ".join("".join(e.itertext()).split()) if e is not None else ""


def row(path):
    r = ET.parse(path).getroot()
    def en(tag):
        return next((e for e in r.iter(NS + tag) if e.get("{http://www.w3.org/XML/1998/namespace}lang", "en") == "en"), None)
    d = next(r.iter(NS + "origDate"), None)
    nb = (d.get("notBefore-custom") or d.get("notBefore") or "") if d is not None else ""
    na = (d.get("notAfter-custom") or d.get("notAfter") or "") if d is not None else ""
    try:
        ok = "так" if int(na or nb) <= 800 else "ні"
    except ValueError:
        ok = ""
    return {"id": path.stem, "назва": txt(en("title")), "походження": txt(next(r.iter(NS + "origPlace"), None)),
            "дата_від": nb, "дата_до": na, "до_800": ok, "об_єкт": txt(en("objectType")),
            "матеріал": txt(en("material")), "опис": txt(en("seg"))}


if __name__ == "__main__":
    рядки = [row(p) for p in sorted((OUT / "xml").glob("*.xml"))]
    with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, рядки[0].keys())
        w.writeheader()
        w.writerows(рядки)
    print("файлів", len(рядки), "до 800 року", sum(r["до_800"] == "так" for r in рядки))
