"""Фото написів з Wikimedia Commons (відкриті ліцензії) за категоріями, що стосуються України та Причорномор'я.
Обережний режим: пауза між запитами, повтор при 429 з очікуванням."""
import csv, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "написи" / "фото_Commons"
UA = {"User-Agent": "ancient-texts-research/1.0 (https://github.com/wku/dp-claude; research use)"}
ПАУЗА = 2
# категорії Commons, назва папки
ПОЧАТОК = {
    "Ольвія": ["Category:Inscriptions in Olbia", "Category:Steles from Olbia (Ukraine)", "Category:Latin inscriptions in Olbia"],
    "Херсонес": ["Category:Civic Oath of Chersonesos"],
}
ПОШУК = {  # запит -> папка, береться кожна знайдена категорія з потрібними словами
    "Херсонес": ["Chersonesos inscriptions", "Inscriptions in Chersonesos", "Chersonesus Taurica inscriptions"],
    "Тіра": ["Tyras inscriptions", "Tyras Ovidiopol inscription"],
    "Березань": ["Berezan inscriptions", "Berezan lead letter"],
    "Керч_Пантікапей": ["Panticapaeum inscriptions", "Kerch ancient inscriptions", "Bosporan inscriptions"],
    "Україна_загальне": ["Ancient Greek inscriptions in Ukraine", "Latin inscriptions in Ukraine", "Greek inscriptions in Crimea"],
}
ВИКЛЮЧИТИ = re.compile(r"petersburg|byzant|medieval|ottoman|soviet|modern|monument to|signs|cemeter|graffiti in", re.I)


def api(**p):
    p["format"] = "json"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)
    for i in range(8):
        time.sleep(ПАУЗА)
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            w = int(e.headers.get("Retry-After", 60)) if e.code == 429 else 20
            time.sleep(w * (i + 1))
        except Exception:
            time.sleep(20)
    raise RuntimeError(url)


def файли(кат, глибина=2, бачені=None):
    бачені = бачені if бачені is not None else set()
    if кат in бачені:
        return []
    бачені.add(кат)
    res, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle=кат, cmlimit=500, cmtype="file|subcat", **cont)
        for m in d["query"]["categorymembers"]:
            if m["ns"] == 6:
                res.append(m["title"])
            elif m["ns"] == 14 and глибина > 0 and not ВИКЛЮЧИТИ.search(m["title"]):
                res += файли(m["title"], глибина - 1, бачені)
        if "continue" not in d:
            return res
        cont = d["continue"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    кандидати = {k: list(v) for k, v in ПОЧАТОК.items()}
    for папка, запити in ПОШУК.items():
        for q in запити:
            for x in api(action="query", list="search", srsearch=q, srnamespace=14, srlimit=10)["query"]["search"]:
                if re.search(r"inscript|stele|lead|epigra|oath|tablet", x["title"], re.I) and not ВИКЛЮЧИТИ.search(x["title"]):
                    кандидати.setdefault(папка, []).append(x["title"])
    print({k: sorted(set(v)) for k, v in кандидати.items()}, flush=True)
    for папка, кати in кандидати.items():
        d = OUT / папка
        d.mkdir(exist_ok=True)
        csvp = d / "описи.csv"
        вже = {r["файл"] for r in csv.DictReader(open(csvp, encoding="utf-8"))} if csvp.exists() else set()
        новий = not csvp.exists()
        f = open(csvp, "a", newline="", encoding="utf-8")
        w = csv.DictWriter(f, ["файл", "назва", "опис", "автор", "ліцензія", "дата", "сторінка"])
        if новий:
            w.writeheader()
        титули = []
        for к in sorted(set(кати)):
            титули += файли(к)
        for t in sorted(set(титули)):
            ім = re.sub(r"[^\w.\-]+", "_", t.replace("File:", ""))
            if ім in вже or not re.search(r"\.(jpe?g|png|tiff?)$", ім, re.I):
                continue
            d_ = api(action="query", titles=t, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1600)
            p = list(d_["query"]["pages"].values())[0].get("imageinfo", [{}])[0]
            if not p.get("url"):
                continue
            em = p.get("extmetadata", {})
            g = lambda k: re.sub(r"<[^>]+>", "", em.get(k, {}).get("value", ""))
            try:
                time.sleep(ПАУЗА)
                (d / ім).write_bytes(urllib.request.urlopen(urllib.request.Request(p.get("thumburl") or p["url"], headers=UA), timeout=120).read())
            except Exception as e:
                print("збій", t, e, flush=True)
                continue
            w.writerow({"файл": ім, "назва": t, "опис": g("ImageDescription")[:600], "автор": g("Artist")[:200], "ліцензія": g("LicenseShortName"),
                        "дата": g("DateTimeOriginal")[:60], "сторінка": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_"))})
            f.flush()
            print(папка, ім, flush=True)
        f.close()


if __name__ == "__main__":
    main()
