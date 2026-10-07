"""Тексти античних авторів про Причорномор'я з відкритих репозиторіїв Perseus (TEI XML) у читабельний txt.
Вихідні репозиторії клонуються окремо (git clone --depth 1) у папку CLONES."""
import re, sys
import xml.etree.ElementTree as ET
from pathlib import Path

CLONES = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/user/clones")
OUT = Path(__file__).resolve().parent.parent / "data" / "античні_автори"
G, L = "canonical-greekLit/data", "canonical-latinLit/data"
# (папка автора, джерело, мова, назва твору, опис)
ТВОРИ = [
    ("Геродот", f"{G}/tlg0016/tlg001/tlg0016.tlg001.perseus-grc2.xml", "грецька", "Історія",
     "Книга 4 описує Скіфію, північне узбережжя Чорного моря, Борисфен (Дніпро), Ольвію та народи сучасної України. V століття до н. е."),
    ("Геродот", f"{G}/tlg0016/tlg001/tlg0016.tlg001.perseus-eng2.xml", "англійська", "Історія (переклад)", "Англійський переклад Історії Геродота."),
    ("Страбон", f"{G}/tlg0099/tlg001/tlg0099.tlg001.perseus-grc2.xml", "грецька", "Географія",
     "Книга 7 описує Причорномор'я, Крим, Дніпро та Дністер. Кінець I століття до н. е."),
    ("Страбон", f"{G}/tlg0099/tlg001/tlg0099.tlg001.perseus-eng3.xml", "англійська", "Географія (переклад)", "Англійський переклад Географії Страбона."),
    ("Діон Хрісостом", f"{G}/tlg0612/tlg001/tlg0612.tlg001.perseus-grc2.xml", "грецька", "Промови",
     "Промова 36 (Борисфенітська) розповідає про відвідування Ольвії. Кінець I століття."),
    ("Арріан", f"{G}/tlg0074/tlg004/tlg0074.tlg004.perseus-grc2.xml", "грецька", "Периплу Чорного моря",
     "Опис узбережжя Чорного моря, зокрема північного (Ольвія, Тіра, Тавріка). II століття."),
    ("Прокопій Кесарійський", f"{G}/tlg4029/tlg001/tlg4029.tlg001.perseus-grc2.xml", "грецька", "Війни",
     "Історія воєн Юстиніана, містить відомості про готів, гунів, склавінів, анті та Крим. VI століття."),
    ("Гіппократ", f"{G}/tlg0627/tlg002/tlg0627.tlg002.perseus-grc2.xml", "грецька", "Про повітря, води та місцевості",
     "Опис скіфів і їхньої країни (розділи 17 до 22). V століття до н. е."),
    ("Гіппократ", f"{G}/tlg0627/tlg002/tlg0627.tlg002.perseus-eng3.xml", "англійська", "Про повітря, води та місцевості (переклад)", "Англійський переклад."),
    ("Овідій", f"{L}/phi0959/phi008/phi0959.phi008.perseus-lat2.xml", "латинська", "Скорботні елегії (Tristia)",
     "Вірші з вигнання в Томи (Констанца, Румунія). I століття."),
    ("Овідій", f"{L}/phi0959/phi009/phi0959.phi009.perseus-lat2.xml", "латинська", "Листи з Понту (Ex Ponto)",
     "Листи з Томів про життя на узбережжі Чорного моря. I століття."),
    ("Пліній Старший", f"{L}/phi0978/phi001/phi0978.phi001.perseus-lat2.xml", "латинська", "Природнича історія",
     "Книга 4 описує Скіфію і Причорномор'я. I століття."),
    ("Амміан Марцеллін", f"{L}/stoa0023/stoa001/stoa0023.stoa001.perseus-lat2.xml", "латинська", "Діяння",
     "Книга 31 розповідає про гунів і готів у Причорномор'ї, IV століття."),
]
SKIP = {"note", "bibl", "teiHeader"}


def render(e, глибина=0):
    t = e.tag.split("}")[-1]
    if t in SKIP:
        return e.tail or ""
    s = e.text or ""
    n = e.get("n")
    for c in e:
        ct = c.tag.split("}")[-1]
        if ct == "div" and c.get("type") == "textpart":
            s += f"\n\n[{c.get('subtype', '')} {c.get('n', '')}]\n"
        s += render(c, глибина + 1)
    if t in ("p", "l", "head"):
        s += "\n"
    return s + (e.tail or "")


for автор, шлях, мова, назва, опис in ТВОРИ:
    p = CLONES / шлях
    if not p.exists():
        print("немає", p)
        continue
    body = ET.parse(p).getroot().find(".//{http://www.tei-c.org/ns/1.0}body")
    txt = re.sub(r"\n{3,}", "\n\n", re.sub(r" ?\n ?", "\n", re.sub(r"[ \t]+", " ", render(body)))).strip()
    if "phi0959" in шлях:  # вірші, один рядок на рядок
        txt = re.sub(r"\n\n(?!\[)", "\n", txt)
    d = OUT / автор
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{назва.split('(')[0].strip().replace(' ', '_')}_{мова}.txt"
    f.write_text(f"{автор}. {назва}\nМова. {мова}\nДжерело {p.name}, Perseus Digital Library (CC BY-SA)\n\n{txt}\n", encoding="utf-8")
    with open(d / "ОПИС.md", "a", encoding="utf-8") as o:
        o.write(f"- {f.name}. {назва}, мова {мова}. {опис}\n")
    print(f.name, len(txt))
