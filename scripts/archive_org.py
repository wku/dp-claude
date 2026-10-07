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
    "antiquitsgrecqu00rochgoog": "Рауль_Рошетт_1822_Грецькі_старожитності_Боспору_Кіммерійського",
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


def розділити_pdf(url, ціль, розмір):
    """PDF більший за ліміт GitHub завантажується і ділиться на частини за сторінками."""
    from pypdf import PdfReader, PdfWriter
    tmp = ціль.with_suffix(".tmp")
    if not save(url, tmp):
        return
    r = PdfReader(tmp)
    n = len(r.pages)
    частин = розмір // (80 * 1024 * 1024) + 1
    крок = -(-n // частин)
    for k in range(частин):
        w = PdfWriter()
        for pg in r.pages[k * крок:(k + 1) * крок]:
            w.add_page(pg)
        with open(ціль.with_name(f"{ціль.stem}_частина{k + 1}.pdf"), "wb") as f:
            w.write(f)
    tmp.unlink()
    print("розділено", ціль.name, n, "сторінок на", частин, "частини")


for i, назва in ВИДАННЯ.items():
    d = OUT / назва
    d.mkdir(exist_ok=True)
    meta = get(f"https://archive.org/metadata/{i}")
    (d / "metadata.json").write_bytes(meta)
    for f in json.loads(meta)["files"]:
        ціль = d / нова_назва(назва, f["name"])
        if f["format"] in ФОРМАТИ and int(f.get("size", 0)) > МАКС and ціль.suffix == ".pdf" and not list(d.glob(ціль.stem + "_частина*.pdf")):
            розділити_pdf(f"https://archive.org/download/{i}/{f['name']}", ціль, int(f["size"]))
        elif f["format"] in ФОРМАТИ and int(f.get("size", 0)) <= МАКС and not ціль.exists():
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
