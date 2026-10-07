"""Статті у відкритому доступі (Zenodo, ліцензії CC) про давні написи Причорномор'я. Скачує PDF та записує описи."""
import csv, json, re, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "статті"
UA = {"User-Agent": "ancient-texts-research (+https://github.com/wku/dp-claude)"}
ЗАПИТИ = ["Судебное магическое заклятие Ольвия", "Ольвия надпись", "Ольвія напис", "Херсонес надпись", "Херсонес напис", "Боспор надпись", "Березань свинцовое письмо",
          "Olbia Greek inscription", "Chersonesos inscription", "Bosporan inscription", "Tyras inscription", "Pontic Greek lead letter", "Scythia Greek graffiti"]
СЛОВА = re.compile(r"надпис|напис|inscript|эпигра|epigra|заклят|curse|defix|свинц|lead letter|граффит|graffit|ольвиополит|decree|декрет")
СЛОВА0 = re.compile(r"ольв|olbia|херсонес|chersones|боспор|bospor|тира\b|tyras|березан|berezan|пантикап|panticap|скиф|scyth|причерном|black sea|pontic", re.I)
ВИКЛ = re.compile(r"biodiver|plant|species|bird|fish|geolog|climate", re.I)


def get(url):
    time.sleep(2)
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    csvp = OUT / "описи.csv"
    вже = {r["id"] for r in csv.DictReader(open(csvp, encoding="utf-8"))} if csvp.exists() else set()
    f = open(csvp, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, ["id", "файл", "назва", "автори", "дата", "ліцензія", "опис", "сторінка"])
    if not вже:
        w.writeheader()
    for q in ЗАПИТИ:
        for h in json.loads(get("https://zenodo.org/api/records?" + urllib.parse.urlencode({"q": q, "size": 8, "type": "publication"})))["hits"]["hits"]:
            m = h["metadata"]
            назва = m.get("title", "")
            if str(h["id"]) in вже or not СЛОВА.search(назва.lower()) or not СЛОВА0.search(назва + " " + m.get("description", "")[:300]) or ВИКЛ.search(назва):
                continue
            lic = m.get("license", {}).get("id", "")
            if not lic.startswith(("cc-by", "cc0", "cc-zero")):
                continue
            for fl in h.get("files", []):
                if fl["key"].lower().endswith(".pdf") and fl["size"] < 60_000_000:
                    ім = re.sub(r"[^\w.\-]+", "_", f"{m.get('publication_date', '')[:4]}_{назва[:70]}") + ".pdf"
                    (OUT / ім).write_bytes(get(fl["links"]["self"]))
                    w.writerow({"id": h["id"], "файл": ім, "назва": назва, "автори": "; ".join(c["name"] for c in m.get("creators", [])),
                                "дата": m.get("publication_date", ""), "ліцензія": lic, "опис": re.sub(r"<[^>]+>", "", m.get("description", ""))[:700],
                                "сторінка": f"https://zenodo.org/records/{h['id']}"})
                    f.flush()
                    вже.add(str(h["id"]))
                    print(ім)
                    break


if __name__ == "__main__":
    main()
