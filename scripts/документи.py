"""Перетворює сирі дані (XML, CSV) на читабельні документи Markdown, по одному на напис."""
import csv, re, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data" / "написи"
NS = "{http://www.tei-c.org/ns/1.0}"
XLANG = "{http://www.w3.org/XML/1998/namespace}lang"
csv.field_size_limit(10**9)


def render(e):
    t = e.tag.replace(NS, "")
    if t == "lb":
        return "\n" + (e.tail or "")
    inner = (e.text or "") + "".join(render(c) for c in e)
    inner = {"supplied": f"[{inner}]", "gap": "[...]", "ex": f"({inner})", "surplus": f"{{{inner}}}", "del": f"[[{inner}]]"}.get(t, inner)
    return inner + (e.tail or "")


def чисто(s):
    return "\n".join(" ".join(l.split()) for l in s.splitlines() if l.strip())


def за_мовою(root, path, мови=("en", "ru", None)):
    els = list(root.iterfind(path))
    for m in мови:
        for e in els:
            if e.get(XLANG) == m:
                return чисто("".join(e.itertext()))
    return чисто("".join(els[0].itertext())) if els else ""


# IOSPE
ТОМИ = {"1": "Тіра", "2": "Ольвія_і_Березань", "3": "Херсонес", "5": "Візантійські_написи"}


def iospe():
    xml = D / "iospe" / "xml"
    if not xml.exists():
        zipfile.ZipFile(D / "iospe" / "сирі_дані" / "iospe_xml.zip").extractall(xml)
    idx = {r["id"]: r for r in csv.DictReader(open(D / "iospe" / "index.csv", encoding="utf-8"))}
    for p in sorted(xml.glob("*.xml")):
        r = ET.parse(p).getroot()
        том = ТОМИ.get(p.stem.split(".")[0], "Інше")
        out = D / "iospe" / "документи" / том
        out.mkdir(parents=True, exist_ok=True)
        i = idx.get(p.stem, {})
        назва = за_мовою(r, f".//{NS}titleStmt/{NS}title")
        ed = r.find(f".//{NS}div[@type='edition']")
        текст = чисто(render(ed)) if ed is not None else ""
        пер = [(e.get(XLANG), чисто(render(e))) for e in r.iterfind(f".//{NS}div[@type='translation']")]
        ком = [чисто("".join(e.itertext())) for e in r.iterfind(f".//{NS}div[@type='commentary']")]
        поля = [("Місце походження", i.get("походження", "")), ("Датування", f"{i.get('дата_від','')} … {i.get('дата_до','')} (роки, від'ємні означають до н. е.)"),
                ("Тип пам'ятки", i.get("об_єкт", "")), ("Матеріал", i.get("матеріал", "")), ("Опис", i.get("опис", "")),
                ("Зберігання", за_мовою(r, f".//{NS}repository")), ("Фізичний опис", за_мовою(r, f".//{NS}support/{NS}p")),
                ("Письмо", за_мовою(r, f".//{NS}handNote/{NS}seg"))]
        md = f"# IOSPE {p.stem}. {назва}\n\n" + "".join(f"**{k}.** {v}\n\n" for k, v in поля if v.strip(" …()")) + f"## Текст\n\n```\n{текст}\n```\n\n"
        for м, т in пер:
            if т:
                md += f"## Переклад ({м or '?'})\n\n{т}\n\n"
        for к in ком:
            if к:
                md += f"## Коментар\n\n{к}\n\n"
        md += f"Джерело https://github.com/kingsdigitallab/iospe, ліцензія CC BY. Оригінальний XML в архіві сирі_дані/iospe_xml.zip\n"
        slug = re.sub(r"\W+", "_", назва.split(".")[0])[:50].strip("_")
        (out / f"{p.stem}_{slug}.md").write_text(md, encoding="utf-8")


# EDH
КРАЇНИ = {"ua": "Україна", "ro": "Румунія", "bg": "Болгарія", "cz": "Чехія", "pl": "Польща"}


def edh():
    for r in csv.DictReader(open(D / "edh" / "inscriptions.csv", encoding="utf-8")):
        к = КРАЇНИ[r["land"].rstrip("?")]
        out = D / "edh" / "документи" / к
        out.mkdir(parents=True, exist_ok=True)
        місце = r["fo_antik"] or r["fo_modern"] or "невідомо"
        поля = [("Країна", к), ("Провінція (код EDH)", r["provinz"]), ("Місце знахідки (антична назва)", r["fo_antik"]), ("Сучасна назва", r["fo_modern"]),
                ("Деталі знахідки", r["fundstelle"]), ("Координати", r["koordinaten1"]), ("Рік знахідки", r["fundjahr"]), ("Зберігання", r["aufbewahrung"]),
                ("Датування (роки, від'ємні до н. е.)", f"{r['dat_jahr_a']} … {r['dat_jahr_e']}"), ("Матеріал", r["material"]), ("Тип пам'ятки", r["denkmaltyp"]),
                ("Розміри (висота, ширина, глибина, см)", " × ".join(x for x in (r["hoehe"], r["breite"], r["tiefe"]) if x)), ("Стан збереження", r["erhaltung"])]
        md = f"# EDH {r['hd_nr']}. {місце}\n\n" + "".join(f"**{k}.** {v}\n\n" for k, v in поля if v.strip(" …"))
        md += f"## Текст (латинь, скорочення розкрито)\n\n```\n{r['atext']}\n```\n\n"
        if r["btext"]:
            md += f"## Текст у вихідному записі\n\n```\n{r['btext']}\n```\n\n"
        if r["kommentar"]:
            md += f"## Коментар\n\n{r['kommentar']}\n\n"
        if r["literatur"]:
            md += f"## Література\n\n{r['literatur'].replace(' # ', chr(10) + '- ')}\n\n"
        фото = sorted(out.glob(f"{r['hd_nr']}*.jpg"))
        if фото:
            md += "## Фото\n\n" + "\n\n".join(f"![{ф.stem}]({ф.name})" for ф in фото) + "\n\n"
        md += f"Джерело https://edh.ub.uni-heidelberg.de/edh/inschrift/{r['hd_nr']}, ліцензія CC BY-SA 4.0. Оригінальний XML в архіві сирі_дані/edh_xml.zip\n"
        (out / f"{r['hd_nr']}_{re.sub(r'\W+', '_', місце)[:40]}.md").write_text(md, encoding="utf-8")


def архів(папка, назва):  # потребує розпакованої папки xml
    xml = D / папка / "xml"
    if xml.exists():
        (D / папка / "сирі_дані").mkdir(exist_ok=True)
        with zipfile.ZipFile(D / папка / "сирі_дані" / f"{назва}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(xml.glob("*.xml")):
                z.write(p, p.name)


if __name__ == "__main__":
    iospe()
    edh()
