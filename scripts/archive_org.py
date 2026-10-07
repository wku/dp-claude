"""Завантаження метаданих і повного тексту (OCR) видань з Internet Archive."""
import json, time, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "книги"
ВИДАННЯ = {  # ідентифікатор Internet Archive -> зрозуміла назва папки
    "inscriptionesty00russgoog": "Латишев_1916_IOSPE_том1_Тіра_Ольвія_Херсонес_скан_Google",
    "sucho-id-_20220305_2137": "Латишев_1916_IOSPE_том1_Тіра_Ольвія_Херсонес_скан_бібліотеки",
    "inscriptionesan00petegoog": "Латишев_1890_IOSPE_том2_Боспорське_царство",
    "LatyshevInscriptionesAntiquaeOraeSeptentrionalisPontiEuxiniGraecaeEtLatinaeVol4IV": "Латишев_1901_IOSPE_том4",
    "scythicaetcauca00latygoog": "Латишев_1893_Scythica_et_Caucasica_античні_автори_про_Скіфію",
    "gothichistoryofj00jord": "Йордан_VI_ст_Історія_готів_видання_1915_англійський_переклад",
    "bub_gb_VX2P_CtKJmQC": "Менандр_Протектор_і_Агафій_VI_ст_грецький_текст_видання_1871",
    "fragmentsdespoe00antgoog": "Скімн_Хіоський_і_Псевдо_Дікеарх_географічні_поеми_видання_1841",
    "herodotihistoria01herouoft": "Геродот_Історія_Худе_1908_том1_грецький_текст",
    "strabonisgeogra08stragoog": "Страбон_Географія_Дідо_1853_грецький_текст",
    "geographigraeci00unkngoog": "Малі_грецькі_географи_Мюллер_1855_том1",
    "dionischrysosto00diogoog": "Діон_Хрісостом_Твори_Емперіус_1844_грецький_текст",
    "claudiiptolemaei01ptol": "Птолемей_Географія_Ноббе_1843_том1",
    "claudiiptolemaei02ptol": "Птолемей_Географія_Ноббе_1843_том2",
    "povidinasonistr00owengoog": "Овідій_Скорботні_елегії_і_Листи_з_Понту_Оуен_1915_латинський_текст",
    "cuaiordanisroman00jord": "Йордан_Романа_і_Гетика_Моммзен_1882_латинський_текст",
    "pontika2": "Латишев_1909_Понтіка_збірник_статей",
    "antiquitsgrecqu00rochgoog": "Рауль_Рошетт_1822_Грецькі_старожитності_Боспору_Кіммерійського",
}


ОПИСИ = {  # ідентифікатор -> (назва, що це)
    "herodotihistoria01herouoft": ("Herodoti Historiae, том 1 (ред. К. Худе, Оксфорд)", "Грецький текст Історії Геродота, книги 1 до 4. Книга 4 описує Скіфію, Борисфен (Дніпро), Ольвію та народи сучасної України, V століття до н. е."),
    "strabonisgeogra08stragoog": ("Strabonis Geographica, грецький текст з латинським перекладом (Дідо, Париж)", "Повна Географія Страбона. Книга 7 описує північні береги Чорного моря, Крим і Борисфен, кінець I століття до н. е."),
    "geographigraeci00unkngoog": ("Geographi Graeci minores, том 1 (К. Мюллер)", "Грецькі малі географи. Містить Периплу Чорного моря Арріана, Скімна Хіоського й інші описи берегів Причорномор'я, з латинським перекладом."),
    "dionischrysosto00diogoog": ("Dionis Chrysostomi Opera graece (Емперіус)", "Грецькі твори Діона Хрісостома. Борисфенітська промова (36) розповідає про відвідини Ольвії, I століття."),
    "claudiiptolemaei01ptol": ("Claudii Ptolemaei Geographia, том 1 (К. Ноббе)", "Грецький текст Географії Птолемея, з описом Європейської Сарматії та узбережжя Чорного моря (II століття)."),
    "claudiiptolemaei02ptol": ("Claudii Ptolemaei Geographia, том 2 (К. Ноббе)", "Грецький текст Географії Птолемея, продовження, містить опис Азіатської Сарматії та Причорномор'я (II століття)."),
    "povidinasonistr00owengoog": ("P. Ovidi Nasonis Tristia, Ex Ponto, Halieutica (Оуен, Оксфорд)", "Латинський текст елегій Овідія з вигнання в Томи на узбережжі Чорного моря, I століття."),
    "cuaiordanisroman00jord": ("Iordanis Romana et Getica (Т. Моммзен, MGH)", "Латинський текст Йордана, VI століття. Гетика описує історію готів, їхнє перебування в Скіфії та на території сучасної України."),
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


ФОРМАТИ = {"Text PDF", "Image Container PDF"}  # лише скани у PDF
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

for i, (назва, опис) in ОПИСИ.items():
    d = OUT / ВИДАННЯ[i]
    if d.exists() and not (d / "ОПИС.md").exists():
        m = json.load(open(d / "metadata.json"))["metadata"]
        а = m.get("creator", "не вказано")
        а = ", ".join(а) if isinstance(а, list) else а
        файли = ", ".join(sorted(p.name for p in d.iterdir() if p.name not in ("metadata.json", "ОПИС.md")))
        (d / "ОПИС.md").write_text(f"# {назва}\n\nАвтор або упорядник. {а} (за даними Internet Archive)\n\nРік. {m.get('date', m.get('year', ''))}\n\nЩо це. {опис}\n\nФайли. {файли}\n\nДжерело. https://archive.org/details/{i}\n\nЛіцензія. Суспільне надбання.\n", encoding="utf-8")
