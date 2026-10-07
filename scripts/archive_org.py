"""Завантаження метаданих і повного тексту (OCR) видань з Internet Archive."""
import json, time, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "archive_org"
ВИДАННЯ = [
    "inscriptionesan00petegoog",  # Латишев, IOSPE, том 1 (1885)
    "inscriptionesty00russgoog",  # Латишев, Tyrae Olbiae Chersonesi, 2 вид.
    "LatyshevInscriptionesAntiquaeOraeSeptentrionalisPontiEuxiniGraecaeEtLatinaeVol4IV",  # том 4 (1901)
    "pontika2",
    "izobrazheniiaraz00vaks",
]


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


for i in ВИДАННЯ:
    d = OUT / i
    d.mkdir(exist_ok=True)
    meta = get(f"https://archive.org/metadata/{i}")
    (d / "metadata.json").write_bytes(meta)
    for f in json.loads(meta)["files"]:
        if f["format"] in ФОРМАТИ and int(f.get("size", 0)) <= МАКС and not (d / f["name"]).exists():
            print(i, f["name"], save(f"https://archive.org/download/{i}/{f['name']}", d / f["name"]))
            time.sleep(5)
