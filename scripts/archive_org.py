"""Завантаження метаданих і повного тексту (OCR) видань з Internet Archive."""
import json, time, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "archive_org"
ВИДАННЯ = {  # ідентифікатор Internet Archive -> зрозуміла назва папки
    "inscriptionesty00russgoog": "Латишев_1916_IOSPE_том1_Тіра_Ольвія_Херсонес_скан_Google",
    "sucho-id-_20220305_2137": "Латишев_1916_IOSPE_том1_Тіра_Ольвія_Херсонес_скан_бібліотеки",
    "inscriptionesan00petegoog": "Латишев_1890_IOSPE_том2_Боспорське_царство",
    "LatyshevInscriptionesAntiquaeOraeSeptentrionalisPontiEuxiniGraecaeEtLatinaeVol4IV": "Латишев_1901_IOSPE_том4",
    "pontika2": "Латишев_1909_Понтіка_збірник_статей",
    "izobrazheniiaraz00vaks": "1801_Зображення_пам_ятників_давнини_Чорного_моря",
    "cultsofolbia00hirs": "Хірст_1902_Культи_Ольвії",
    "derebusolbiopoli00lind": "1888_De_rebus_Olbiopolitarum",
    "bub_gb_XrojFJxkj5gC": "1822_Медалі_Ольвії",
    "b14691693": "1922_Грецька_археологічна_колекція_з_Ольвії",
    "antiquitsgrecqu00rochgoog": "Рауль_Рошетт_1822_Грецькі_старожитності_Боспору_Кіммерійського",
    "Kerchenskiedrevnosti26": "1845_Керченські_старожитності",
    "McGillLibrary-hssl_pamiatniki-khristianskago-khersonesa_foliobr133u383c5371905vyp-3-16271": "1905_Пам_ятники_християнського_Херсонеса",
}


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ancient-texts-research (contact via repo wku/dp-claude)"})
            return urllib.request.urlopen(req, timeout=300).read()
        except Exception as e:
            print("повтор", url, e)
            time.sleep(10 * (i + 1))
    return None


ФОРМАТИ = {"Text PDF", "Image Container PDF", "Additional Text PDF", "DjVu", "DjVuTXT"}
МАКС = 99 * 1024 * 1024  # ліміт GitHub на один файл


def save(url, path):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ancient-texts-research (contact via repo wku/dp-claude)"})
            with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            return True
        except Exception as e:
            print("повтор", path.name, e)
            time.sleep(10 * (i + 1))
    return False


def нова_назва(папка, імя):
    for кінець, нов in (("_djvu.txt", ".txt"), ("_text.pdf", "_шар_тексту.pdf"), (".pdf", ".pdf"), (".djvu", ".djvu")):
        if імя.endswith(кінець):
            return папка + нов
    return імя


for i, назва in ВИДАННЯ.items():
    d = OUT / назва
    d.mkdir(exist_ok=True)
    meta = get(f"https://archive.org/metadata/{i}")
    (d / "metadata.json").write_bytes(meta)
    for f in json.loads(meta)["files"]:
        ціль = d / нова_назва(назва, f["name"])
        if f["format"] in ФОРМАТИ and int(f.get("size", 0)) <= МАКС and not ціль.exists():
            print(назва, ціль.name, save(f"https://archive.org/download/{i}/{f['name']}", ціль))
            time.sleep(5)

import csv, re
рядки = []
for i, назва in ВИДАННЯ.items():
    m = json.load(open(OUT / назва / "metadata.json"))["metadata"]
    опис = re.sub(r"<[^>]+>", " ", str(m.get("description", "")))
    рядки.append({"папка": назва, "id": i, "назва": m.get("title", ""), "автор": m.get("creator", ""), "рік": m.get("date", m.get("year", "")),
                  "мова": m.get("language", ""), "опис": " ".join(опис.split()),
                  "файли": "; ".join(sorted(p.name for p in (OUT / назва).iterdir() if p.name != "metadata.json")),
                  "url": f"https://archive.org/details/{i}"})
with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, рядки[0].keys())
    w.writeheader()
    w.writerows(рядки)
