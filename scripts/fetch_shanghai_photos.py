#!/usr/bin/env python3
"""Fetch Wikimedia Commons photos for Shanghai places and write JSON files."""
import json, re, time, urllib.parse, urllib.request, html, sys
from pathlib import Path

UA = "Seoul26Bot/1.0 (personal trip site; carlo@users.noreply.github.com)"
OUT = Path("/workspace/seoul26/shanghai")
OUT.mkdir(exist_ok=True)
THUMB_W = 960  # Wikimedia only allows listed sizes; 800px rejected

COMPAT = re.compile(
    r"^(CC[- ]BY(-SA)?[- ]?\d(\.\d)?|CC0|Public domain|PD[- ].*|CC[- ]Zero)",
    re.I,
)
LICENSE_URLS = {
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "CC BY-SA 2.5": "https://creativecommons.org/licenses/by-sa/2.5/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "Public domain": "https://creativecommons.org/publicdomain/mark/1.0/",
}

# No robotaxi entries. Zhujiajiao skipped (too far). Drone show skipped (no reliable venue/time).
PLACES = [
  {
    "id": "the-bund",
    "name": "The Bund (Waitan)",
    "query": "The Bund Shanghai",
    "category": "Sehenswürdigkeiten",
    "note": "Klassische Uferpromenade mit Kolonialbauten und Blick auf die Pudong-Skyline. Abends besonders stark – gut zu Fuß erreichbar vom Metro-Halt East Nanjing Road.",
    "maps_q": "The Bund Shanghai",
    "lat": 31.24037, "lng": 121.49058,
    "file_hints": ["The Bund", "Waitan Shanghai"],
  },
  {
    "id": "shanghai-tower",
    "name": "Shanghai Tower",
    "query": "Shanghai Tower",
    "category": "Aussicht",
    "note": "Höchster Aussichtspunkt der Stadt in Lujiazui. Tickets vorab buchen; bei klarem Wetter Blick bis zum Bund und darüber hinaus.",
    "maps_q": "Shanghai Tower Lujiazui Shanghai",
    "lat": 31.23359, "lng": 121.50551,
    "file_hints": ["Shanghai Tower observation", "Shanghai Tower exterior"],
  },
  {
    "id": "oriental-pearl-tower",
    "name": "Oriental Pearl Tower",
    "query": "Oriental Pearl Tower Shanghai",
    "category": "Aussicht",
    "note": "Ikone von Pudong mit Kugeln und Aussichtsplattformen. Lohnt sich vor allem für das Foto von außen und die Skyline-Kulisse am Abend.",
    "maps_q": "Oriental Pearl Tower Shanghai",
    "lat": 31.23974, "lng": 121.49981,
    "file_hints": ["Oriental Pearl Tower", "Oriental Pearl"],
  },
  {
    "id": "yu-garden",
    "name": "Yu Garden (Yuyuan)",
    "query": "Yu Garden Shanghai",
    "category": "Sehenswürdigkeiten",
    "note": "Klassischer Ming-Garten mit Pavillons und Teichen, direkt am Basar. Am besten früh oder spät am Tag – mittags oft sehr voll.",
    "maps_q": "Yu Garden Shanghai",
    "lat": 31.22735, "lng": 121.49215,
    "file_hints": ["Yuyuan Garden", "Yu Yuan"],
  },
  {
    "id": "city-god-temple",
    "name": "City God Temple",
    "query": "City God Temple Shanghai",
    "category": "Sehenswürdigkeiten",
    "note": "Taoistischer Tempel mitten im Altstadtviertel, wenige Schritte vom Yu Garden. Kurz und gut zwischen Basar und Garten.",
    "maps_q": "City God Temple Shanghai",
    "lat": 31.22585, "lng": 121.49240,
    "file_hints": ["Chenghuang Temple Shanghai", "City God Temple Shanghai"],
  },
  {
    "id": "nanjing-road",
    "name": "Nanjing Road Pedestrian Street",
    "query": "Nanjing Road Pedestrian Street Shanghai",
    "category": "Viertel",
    "note": "Belebte Fußgängerzone vom People's Square zum Bund. Gut als Verbindungsweg am Abend – Läden, Snackstände, Neonlicht.",
    "maps_q": "Nanjing Road Pedestrian Street Shanghai",
    "lat": 31.23520, "lng": 121.47880,
    "file_hints": ["Nanjing Road Shanghai", "Nanjing Rd night"],
  },
  {
    "id": "peoples-square",
    "name": "People's Square",
    "query": "People's Square Shanghai",
    "category": "Sehenswürdigkeiten",
    "note": "Zentraler Platz mit Metro-Knoten, Museum und Park. Praktischer Startpunkt für Nanjing Road und die Innenstadt.",
    "maps_q": "People's Square Shanghai",
    "lat": 31.23042, "lng": 121.47370,
    "file_hints": ["People's Square Shanghai", "Renmin Square Shanghai"],
  },
  {
    "id": "tianzifang",
    "name": "Tianzifang",
    "query": "Tianzifang Shanghai",
    "category": "Viertel",
    "note": "Enge Gassen mit Shops, Galerien und Cafés in alten Shikumen-Häusern. Ideal zum Spazieren – abends gemütlich, tagsüber fotogen.",
    "maps_q": "Tianzifang Shanghai",
    "lat": 31.21055, "lng": 121.46640,
    "file_hints": ["Tianzifang", "Tianzi Fang"],
  },
  {
    "id": "xintiandi",
    "name": "Xintiandi",
    "query": "Xintiandi Shanghai",
    "category": "Viertel",
    "note": "Aufgearbeitete Shikumen-Gassen mit Restaurants und Bars. Gute Abendoption nahe der Metro South Huangpi Road.",
    "maps_q": "Xintiandi Shanghai",
    "lat": 31.22080, "lng": 121.47480,
    "file_hints": ["Xintiandi", "Xin Tian Di Shanghai"],
  },
  {
    "id": "wukang-road",
    "name": "Wukang Road",
    "query": "Wukang Road Shanghai",
    "category": "Viertel",
    "note": "Allee in der ehemaligen französischen Konzession mit Villen und Cafés. Ruhiger Spaziergang – eher vormittags oder spätnachmittags.",
    "maps_q": "Wukang Road Shanghai",
    "lat": 31.20780, "lng": 121.43860,
    "file_hints": ["Wukang Road", "Wukang Building"],
  },
  {
    "id": "jingan-temple",
    "name": "Jing'an Temple",
    "query": "Jing'an Temple Shanghai",
    "category": "Sehenswürdigkeiten",
    "note": "Goldener Tempel an der Nanjing West Road, umgeben von Hochhäusern. Kurzbesuch lohnt – danach Starbucks Reserve oder Jing'an-Viertel.",
    "maps_q": "Jing'an Temple Shanghai",
    "lat": 31.22340, "lng": 121.44560,
    "file_hints": ["Jing'an Temple", "Jingan Temple"],
  },
  {
    "id": "huangpu-night-cruise",
    "name": "Huangpu River Night Cruise",
    "query": "Huangpu River night Shanghai Bund",
    "category": "Nacht",
    "note": "Nachtfahrt auf dem Huangpu mit Bund und Lujiazui illuminiert. Abfahrt z. B. Shiliupu oder Oriental Pearl – Tickets am Pier oder online.",
    "maps_q": "Huangpu River Cruise Shiliupu Pier Shanghai",
    "lat": 31.23090, "lng": 121.49550,
    "file_hints": ["Huangpu River night", "Bund night cruise"],
  },
  {
    "id": "lujiazui-riverside",
    "name": "Lujiazui Riverside Promenade",
    "query": "Lujiazui skyline Shanghai night",
    "category": "Nacht",
    "note": "Uferweg auf der Pudong-Seite mit Blick zurück auf den Bund. Abends kostenlos und nah an Oriental Pearl / Shanghai Tower.",
    "maps_q": "Lujiazui Riverside Promenade Shanghai",
    "lat": 31.23880, "lng": 121.49720,
    "file_hints": ["Lujiazui night", "Pudong skyline Bund"],
  },
  {
    "id": "maglev-pvg",
    "name": "Shanghai Maglev",
    "query": "Shanghai Maglev train",
    "category": "Technik",
    "note": "Schnellster kommerzieller Zug der Welt (PVG ↔ Longyang Road, ca. 8 Min.). Praktisch bei der Ankunft – Richtung Flughafen am Abflugtag Zeitpuffer einplanen.",
    "maps_q": "Shanghai Maglev Longyang Road Station",
    "lat": 31.20315, "lng": 121.55686,
    "file_hints": ["Shanghai Maglev", "Transrapid Shanghai"],
  },
  {
    "id": "shanghai-science-museum",
    "name": "Shanghai Science and Technology Museum",
    "query": "Shanghai Science and Technology Museum",
    "category": "Technik",
    "note": "Großes Technikmuseum in Pudong (Metro Century Avenue / Science Museum). Unter anderem Roboter- und AI-Ausstellungen – Öffnungszeiten vor Ort prüfen.",
    "maps_q": "Shanghai Science and Technology Museum",
    "lat": 31.22028, "lng": 121.53778,
    "file_hints": ["Shanghai Science and Technology Museum", "Shanghai Science Museum"],
  },
  {
    "id": "yangs-fried-dumplings",
    "name": "Yang's Fried Dumplings",
    "query": "Shengjianbao Shanghai fried dumplings",
    "category": "Essen",
    "note": "Legendäre Shengjianbao (angebratene Teigtaschen). Filiale an der Huanghe Road nahe People's Square – früh kommen, es gibt oft Schlange.",
    "maps_q": "Yang's Fried Dumplings Huanghe Road Shanghai",
    "lat": 31.23390, "lng": 121.47530,
    "file_hints": ["Shengjianbao", "Xiaoyang Shengjian"],
  },
  {
    "id": "jia-jia-tang-bao",
    "name": "Jia Jia Tang Bao",
    "query": "Xiaolongbao Shanghai soup dumplings",
    "category": "Essen",
    "note": "Winziger Laden für Xiaolongbao an der Huanghe Road. Schnell, günstig und nah am People's Square – ideal vor oder nach dem Bund.",
    "maps_q": "Jia Jia Tang Bao Shanghai Huanghe Road",
    "lat": 31.23450, "lng": 121.47880,
    "file_hints": ["Xiaolongbao", "soup dumplings Shanghai"],
  },
  {
    "id": "nanxiang-steamed-bun",
    "name": "Nanxiang Steamed Bun Restaurant",
    "query": "Nanxiang Xiaolongbao Yuyuan",
    "category": "Essen",
    "note": "Klassiker für Xiaolongbao direkt am Yu-Garden-Basar. Touristisch, aber praktisch wenn ihr sowieso dort seid – Take-away-Schlangen sind kürzer.",
    "maps_q": "Nanxiang Steamed Bun Restaurant Yuyuan Shanghai",
    "lat": 31.22700, "lng": 121.49250,
    "file_hints": ["Nanxiang steamed bun", "Nanxiang Xiaolongbao"],
  },
  {
    "id": "starbucks-reserve-roastery",
    "name": "Starbucks Reserve Roastery",
    "query": "Starbucks Reserve Roastery Shanghai",
    "category": "Essen",
    "note": "Eine der größten Starbucks-Roasteries der Welt an der Nanjing West Road. Gut für Kaffee und Architektur-Fotos – nahe Jing'an Temple.",
    "maps_q": "Starbucks Reserve Roastery Shanghai Nanjing West Road",
    "lat": 31.22150, "lng": 121.45080,
    "file_hints": ["Starbucks Reserve Roastery Shanghai", "Starbucks Roastery Shanghai"],
  },
]

def urlopen(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)

def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()

def commons_search(query, limit=15):
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": str(THUMB_W),
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    with urlopen(url) as r:
        data = json.load(r)
    pages = (data.get("query") or {}).get("pages") or {}
    return list(pages.values())

def normalize_thumb(info):
    """Prefer upload.wikimedia.org URL at allowed size."""
    tu = (info.get("thumburl") or "").split("?")[0]
    full = (info.get("url") or "").split("?")[0]
    if tu:
        if "thumb.wikimedia.org" in tu:
            tu = tu.replace("https://thumb.wikimedia.org/", "https://upload.wikimedia.org/")
        if "upload.wikimedia.org" in tu:
            return tu
    # Build from full URL with allowed size
    m = re.search(r"upload\.wikimedia\.org/wikipedia/commons/([0-9a-f])/([0-9a-f]{2})/([^/]+)$", full)
    if not m:
        return None
    a, b, name = m.group(1), m.group(2), m.group(3)
    if not re.search(r"\.(jpe?g|png|webp)$", name, re.I):
        return None
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{b}/{name}/{THUMB_W}px-{name}"

def verify_image(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status == 200 and (r.headers.get("Content-Type") or "").startswith("image/"):
                return True
    except Exception:
        pass
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-2047"})
        with urllib.request.urlopen(req, timeout=25) as r:
            ctype = r.headers.get("Content-Type") or ""
            return r.status in (200, 206) and ctype.startswith("image/")
    except Exception as e:
        print(f"  verify fail: {e}", file=sys.stderr)
        return False

def pick_images(place, needed=3):
    queries = [place["query"]] + [f"{h}" for h in place.get("file_hints", [])[:2]]
    seen = set()
    chosen = []
    for q in queries:
        if len(chosen) >= needed:
            break
        try:
            pages = commons_search(q, limit=15)
        except Exception as e:
            print(f"  search fail {q}: {e}", file=sys.stderr)
            time.sleep(0.4)
            continue
        time.sleep(0.3)
        pages = sorted(pages, key=lambda p: p.get("index", 999))
        for page in pages:
            if len(chosen) >= needed:
                break
            title = page.get("title") or ""
            info = (page.get("imageinfo") or [None])[0]
            if not info:
                continue
            mime = info.get("mime") or ""
            if not mime.startswith("image/") or mime in ("image/svg+xml", "image/tiff", "image/gif"):
                continue
            meta = info.get("extmetadata") or {}
            lic = strip_html((meta.get("LicenseShortName") or {}).get("value") or "")
            if not lic or not COMPAT.match(lic):
                continue
            artist = strip_html((meta.get("Artist") or {}).get("value") or "")
            artist = re.sub(r"\s+", " ", artist)[:90] or "Wikimedia Commons"
            thumb = normalize_thumb(info)
            if not thumb or thumb in seen:
                continue
            lic_url = (meta.get("LicenseUrl") or {}).get("value") or LICENSE_URLS.get(lic, "")
            if not verify_image(thumb):
                continue
            seen.add(thumb)
            chosen.append({
                "url": thumb,
                "author": artist,
                "license": lic,
                "licenseUrl": lic_url,
                "source": info.get("descriptionurl") or "",
            })
            print(f"  + {title[:72]} [{lic}]")
    return chosen

def maps_url(q):
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)

def main():
    # Clear old json except keep folder
    for p in OUT.glob("*.json"):
        p.unlink()
    manifest = []
    report = []
    for place in PLACES:
        print(f"\n=== {place['name']} ===")
        images = pick_images(place, needed=3)
        if len(images) < 2:
            print("  broadening…")
            alt = dict(place)
            alt["query"] = place["name"].split("(")[0].strip()
            more = pick_images(alt, needed=3)
            # merge unique
            urls = {i["url"] for i in images}
            for m in more:
                if m["url"] not in urls:
                    images.append(m)
                    urls.add(m["url"])
                if len(images) >= 3:
                    break
        images = images[:3]
        # Validate coords in Shanghai box
        lat, lng = place["lat"], place["lng"]
        assert 30.7 <= lat <= 31.9 and 120.8 <= lng <= 122.2, (place["id"], lat, lng)
        doc = {
            "name": place["name"],
            "city": "Shanghai",
            "when": "Shanghai",
            "note": place["note"],
            "maps": maps_url(place["maps_q"]),
            "photos": maps_url(place["maps_q"]),
            "lat": lat,
            "lng": lng,
            "from": "",
            "category": place["category"],
            "images": images,
        }
        (OUT / f"{place['id']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest.append(place["id"])
        report.append((place["id"], place["category"], len(images)))
        print(f"  wrote {place['id']}.json ({len(images)} photos)")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\nSUMMARY")
    for i, c, n in report:
        print(f"  {i}: {c} · {n} photos")
    low = [r for r in report if r[2] < 2]
    if low:
        print("WARN low photos:", low, file=sys.stderr)

if __name__ == "__main__":
    main()
