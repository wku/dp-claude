"""Обхід Telamon (грецькі написи Болгарії) з дотриманням robots.txt (пауза 5 с, без /search/ та /XMLs/).
Зберігає HTML сторінок надписів у data/telamon/html. Можна переривати й запускати знову."""
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = "https://telamon.uni-sofia.bg"
OUT = Path(__file__).resolve().parent.parent / "data" / "написи" / "telamon"
STATE = OUT / "state.json"
ПАУЗА = 5
ДОЗВОЛЕНО = re.compile(r"^/(epi/view_ins/|epi/view_id/|list/)")
ЗАБОРОНЕНО = re.compile(r"/(en/|bg/|mk/|sr/)?(search|static|admin|XMLs|app)/")
SEEDS = [ROOT + p for p in ("/index", "/list/places/findsps/", "/list/places/", "/list/persons/attesteds/", "/list/bibliographys",
                              "/list/lemmas/", "/list/divines/", "/list/museums/", "/list/organisations/", "/list/persons/officials/")]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ancient-texts-research (+https://github.com/wku/dp-claude)"})
    for i in range(3):
        try:
            return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        except Exception as e:
            time.sleep(30 * (i + 1))
    return None


def main():
    st = json.loads(STATE.read_text()) if STATE.exists() else {"queue": SEEDS, "done": []}
    done, queue = set(st["done"]), list(st["queue"])
    while queue:
        # спершу сторінки надписів, потім списки
        k = next((j for j, u in enumerate(queue) if "/epi/view_ins/" in u), 0)
        url = queue.pop(k)
        if url in done:
            continue
        html = get(url)
        time.sleep(ПАУЗА)
        done.add(url)
        if html is None:
            continue
        path = urllib.parse.urlparse(url).path
        m = re.search(r"/epi/view_ins/([^/?#]+)", path)
        if m:
            (OUT / "html" / f"{m.group(1)}.html").write_text(html, encoding="utf-8")
        for h in re.findall(r'href="([^"#]+)"', html):
            u = urllib.parse.urljoin(url, h.replace("&amp;", "&"))
            p = urllib.parse.urlparse(u)
            if p.netloc == "telamon.uni-sofia.bg" and ДОЗВОЛЕНО.match(p.path) and not ЗАБОРОНЕНО.search(p.path) and u not in done and u not in queue:
                queue.append(u)
        if len(done) % 20 == 0:
            STATE.write_text(json.dumps({"queue": queue, "done": sorted(done)}))
            print(len(done), "сторінок,", len(list((OUT / "html").glob("*.html"))), "надписів, у черзі", len(queue), flush=True)
    STATE.write_text(json.dumps({"queue": [], "done": sorted(done)}))


if __name__ == "__main__":
    main()
