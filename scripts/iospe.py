"""Завантаження надписів IOSPE (EpiDoc XML) та побудова індексу."""
import csv, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://iospe.kcl.ac.uk"
OUT = Path(__file__).resolve().parent.parent / "data" / "iospe"
(OUT / "xml").mkdir(parents=True, exist_ok=True)


def get(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research; ancient-texts)"}), timeout=60).read()
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(url)


def list_ids():
    ids, start = [], 0
    while True:
        html = get(f"{BASE}/search/en/-500/1800/?start={start}").decode()
        found = re.findall(r'href="/(\d+\.\d+)\.html"', html)
        if not found:
            return ids
        ids += found
        start += 40


def fetch(i):
    p = OUT / "xml" / f"{i}.xml"
    if not p.exists():
        p.write_bytes(get(f"{BASE}/{i}.xml"))
    return i


def txt(e):
    return " ".join("".join(e.itertext()).split()) if e is not None else ""


def row(i):
    r = ET.parse(OUT / "xml" / f"{i}.xml").getroot()
    q = lambda p, lang="en": next((e for e in r.iterfind(p) if e.get("{http://www.w3.org/XML/1998/namespace}lang") in (lang, None)), None)
    ns = "{http://www.tei-c.org/ns/1.0}"
    date = next(r.iter(ns + "origDate"), None)
    nb = date.get("notBefore-custom") or date.get("notBefore") if date is not None else ""
    na = date.get("notAfter-custom") or date.get("notAfter") if date is not None else ""
    ok = ""
    try:
        ok = "так" if int(na or nb) <= 800 else "ні"
    except ValueError:
        pass
    return dict(
        id=i, назва=txt(q(f".//{ns}titleStmt/{ns}title")),
        походження=txt(next(r.iter(ns + "origPlace"), None)),
        дата_від=nb, дата_до=na, до_800=ok,
        об_єкт=txt(q(f".//{ns}objectType")), матеріал=txt(q(f".//{ns}material")),
        опис=txt(q(f".//{ns}summary/{ns}seg")),
        url=f"{BASE}/{i}.html",
    )


if __name__ == "__main__":
    ids = list_ids()
    print("надписів", len(ids))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(fetch, ids))
    rows = [row(i) for i in ids]
    with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print("до 800 року", sum(r["до_800"] == "так" for r in rows))
