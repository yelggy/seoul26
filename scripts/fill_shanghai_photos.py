#!/usr/bin/env python3
import json, re, time, urllib.parse, urllib.request, html, sys
from pathlib import Path

UA = "Seoul26Bot/1.0 (personal trip site; carlo@users.noreply.github.com)"
OUT = Path("/workspace/seoul26/shanghai")
THUMB_W = 960
COMPAT = re.compile(r"^(CC[- ]BY(-SA)?[- ]?\d(\.\d)?|CC0|Public domain|PD[- ].*|CC[- ]Zero)", re.I)
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

PLACES = {
  "jingan-temple": {
    "name": "Jing'an Temple", "category": "Sehenswürdigkeiten",
    "note": "Goldener Tempel an der Nanjing West Road, umgeben von Hochhäusern. Kurzbesuch lohnt – danach Starbucks Reserve oder Jing'an-Viertel.",
    "maps_q": "Jing'an Temple Shanghai", "lat": 31.22340, "lng": 121.44560,
    "files": ["Jing'an Temple.jpg", "Jing An Temple, Shanghai.jpg", "Shanghai Jing'an Temple 2016.jpg", "Jingan Temple.jpg"],
    "search": "Jing'an Temple Shanghai",
  },
  "tianzifang": {
    "name": "Tianzifang", "category": "Viertel",
    "note": "Enge Gassen mit Shops, Galerien und Cafés in alten Shikumen-Häusern. Ideal zum Spazieren – abends gemütlich, tagsüber fotogen.",
    "maps_q": "Tianzifang Shanghai", "lat": 31.21055, "lng": 121.46640,
    "files": ["Tianzifang Shanghai.jpg", "Tianzifang, Shanghai.jpg", "Tianzi Fang.jpg"],
    "search": "Tianzifang Shanghai",
  },
  "wukang-road": {
    "name": "Wukang Road", "category": "Viertel",
    "note": "Allee in der ehemaligen französischen Konzession mit Villen und Cafés. Ruhiger Spaziergang – eher vormittags oder spätnachmittags.",
    "maps_q": "Wukang Road Shanghai", "lat": 31.20780, "lng": 121.43860,
    "files": ["Wukang Building.jpg", "Wukang Road Shanghai.jpg", "Wukang Mansion.jpg", "Normandie Apartments Shanghai.jpg"],
    "search": "Wukang Road Shanghai",
  },
  "shanghai-science-museum": {
    "name": "Shanghai Science and Technology Museum", "category": "Technik",
    "note": "Großes Technikmuseum in Pudong (Metro Century Avenue / Science Museum). Unter anderem Roboter- und AI-Ausstellungen – Öffnungszeiten vor Ort prüfen.",
    "maps_q": "Shanghai Science and Technology Museum", "lat": 31.22028, "lng": 121.53778,
    "files": ["Shanghai Science and Technology Museum.jpg", "Shanghai Science & Technology Museum.jpg", "Science and Technology Museum Shanghai.jpg"],
    "search": "Shanghai Science and Technology Museum",
  },
  "yangs-fried-dumplings": {
    "name": "Yang's Fried Dumplings", "category": "Essen",
    "note": "Legendäre Shengjianbao (angebratene Teigtaschen). Filiale an der Huanghe Road nahe People's Square – früh kommen, es gibt oft Schlange.",
    "maps_q": "Yang's Fried Dumplings Huanghe Road Shanghai", "lat": 31.23390, "lng": 121.47530,
    "files": ["Shengjianbao.jpg", "Shengjian bao.jpg", "Pan-fried pork buns.jpg", "Shanghai fried dumplings.jpg"],
    "search": "Shengjianbao Shanghai",
  },
  "jia-jia-tang-bao": {
    "name": "Jia Jia Tang Bao", "category": "Essen",
    "note": "Winziger Laden für Xiaolongbao an der Huanghe Road. Schnell, günstig und nah am People's Square – ideal vor oder nach dem Bund.",
    "maps_q": "Jia Jia Tang Bao Shanghai Huanghe Road", "lat": 31.23450, "lng": 121.47880,
    "files": ["Xiaolongbao.jpg", "Xiao Long Bao.jpg", "Soup dumplings.jpg", "Shanghai xiaolongbao.jpg"],
    "search": "Xiaolongbao Shanghai",
  },
  "nanxiang-steamed-bun": {
    "name": "Nanxiang Steamed Bun Restaurant", "category": "Essen",
    "note": "Klassiker für Xiaolongbao direkt am Yu-Garden-Basar. Touristisch, aber praktisch wenn ihr sowieso dort seid – Take-away-Schlangen sind kürzer.",
    "maps_q": "Nanxiang Steamed Bun Restaurant Yuyuan Shanghai", "lat": 31.22700, "lng": 121.49250,
    "files": ["Nanxiang Steamed Bun Restaurant.jpg", "Nanxiang Xiaolongbao.jpg", "Xiaolongbao.jpg"],
    "search": "Nanxiang steamed bun Shanghai",
  },
  "starbucks-reserve-roastery": {
    "name": "Starbucks Reserve Roastery", "category": "Essen",
    "note": "Eine der größten Starbucks-Roasteries der Welt an der Nanjing West Road. Gut für Kaffee und Architektur-Fotos – nahe Jing'an Temple.",
    "maps_q": "Starbucks Reserve Roastery Shanghai Nanjing West Road", "lat": 31.22150, "lng": 121.45080,
    "files": ["Starbucks Reserve Roastery Shanghai.jpg", "Starbucks Reserve Roastery in Shanghai.jpg", "Shanghai Starbucks Reserve Roastery.jpg"],
    "search": "Starbucks Reserve Roastery Shanghai",
  },
}

def urlopen(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)

def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def maps_url(q):
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)

def info_to_image(info, descriptionurl=""):
    mime = info.get("mime") or ""
    if not mime.startswith("image/") or "svg" in mime or "tiff" in mime:
        return None
    meta = info.get("extmetadata") or {}
    lic = strip_html((meta.get("LicenseShortName") or {}).get("value") or "")
    if not lic or not COMPAT.match(lic):
        return None
    artist = re.sub(r"\s+", " ", strip_html((meta.get("Artist") or {}).get("value") or ""))[:90] or "Wikimedia Commons"
    tu = (info.get("thumburl") or "").split("?")[0]
    if "thumb.wikimedia.org" in tu:
        tu = tu.replace("https://thumb.wikimedia.org/", "https://upload.wikimedia.org/")
    if not tu or "upload.wikimedia.org" not in tu:
        return None
    return {
        "url": tu,
        "author": artist,
        "license": lic,
        "licenseUrl": (meta.get("LicenseUrl") or {}).get("value") or LICENSE_URLS.get(lic, ""),
        "source": descriptionurl or info.get("descriptionurl") or "",
    }

def fetch_file(title):
    params = {
        "action": "query", "titles": "File:" + title, "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size", "iiurlwidth": str(THUMB_W), "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urlopen(url) as r:
                data = json.load(r)
            break
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"  retry {title}: {e} sleep {wait}s", flush=True)
            time.sleep(wait)
    else:
        return None
    pages = list(((data.get("query") or {}).get("pages") or {}).values())
    if not pages or "imageinfo" not in pages[0]:
        return None
    return info_to_image(pages[0]["imageinfo"][0], pages[0]["imageinfo"][0].get("descriptionurl") or "")

def verify(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
            with urllib.request.urlopen(req, timeout=25) as r:
                if r.status == 200 and (r.headers.get("Content-Type") or "").startswith("image/"):
                    return True
        except Exception as e:
            if "429" in str(e):
                time.sleep(15 * (attempt + 1))
                continue
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-1023"})
                with urllib.request.urlopen(req, timeout=25) as r:
                    return r.status in (200, 206) and (r.headers.get("Content-Type") or "").startswith("image/")
            except Exception as e2:
                if "429" in str(e2):
                    time.sleep(15 * (attempt + 1))
                    continue
                print(f"  verify fail: {e2}", flush=True)
                return False
    return False

def search_fallback(query, needed=3):
    params = {
        "action": "query", "generator": "search", "gsrsearch": query,
        "gsrnamespace": "6", "gsrlimit": "10", "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime", "iiurlwidth": str(THUMB_W), "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            with urlopen(url) as r:
                data = json.load(r)
            break
        except Exception as e:
            time.sleep(12 * (attempt + 1))
    else:
        return []
    pages = list(((data.get("query") or {}).get("pages") or {}).values())
    pages = sorted(pages, key=lambda p: p.get("index", 99))
    out = []
    for page in pages:
        info = (page.get("imageinfo") or [None])[0]
        if not info:
            continue
        img = info_to_image(info)
        if not img:
            continue
        if not verify(img["url"]):
            time.sleep(1.5)
            continue
        out.append(img)
        print(f"  +search {page.get('title', '')[:64]} [{img['license']}]", flush=True)
        time.sleep(2.0)
        if len(out) >= needed:
            break
    return out

def load_or_base(pid, meta):
    path = OUT / f"{pid}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {
        "name": meta["name"], "city": "Shanghai", "when": "Shanghai",
        "note": meta["note"], "maps": maps_url(meta["maps_q"]), "photos": maps_url(meta["maps_q"]),
        "lat": meta["lat"], "lng": meta["lng"], "from": "", "category": meta["category"], "images": [],
    }

def main():
    for pid, meta in PLACES.items():
        doc = load_or_base(pid, meta)
        images = list(doc.get("images") or [])
        print(f"\n=== {pid} (have {len(images)}) ===", flush=True)
        seen = {i.get("url") for i in images}
        for fname in meta["files"]:
            if len(images) >= 3:
                break
            print(f"  try File:{fname}", flush=True)
            img = fetch_file(fname)
            time.sleep(2.0)
            if not img:
                print("  missing/skip", flush=True)
                continue
            if img["url"] in seen:
                continue
            if not verify(img["url"]):
                print("  bad url", flush=True)
                time.sleep(2)
                continue
            images.append(img)
            seen.add(img["url"])
            print(f"  + {fname} [{img['license']}]", flush=True)
            time.sleep(1.5)
        if len(images) < 2:
            print("  fallback search…", flush=True)
            time.sleep(3)
            for s in search_fallback(meta.get("search") or meta["name"], needed=3 - len(images)):
                if s["url"] not in seen:
                    images.append(s)
                    seen.add(s["url"])
                if len(images) >= 3:
                    break
        doc["images"] = images[:3]
        doc["name"] = meta["name"]
        doc["note"] = meta["note"]
        doc["category"] = meta["category"]
        doc["lat"] = meta["lat"]
        doc["lng"] = meta["lng"]
        doc["maps"] = maps_url(meta["maps_q"])
        doc["photos"] = maps_url(meta["maps_q"])
        doc["city"] = "Shanghai"
        doc["when"] = "Shanghai"
        doc["from"] = ""
        assert 30.7 <= doc["lat"] <= 31.9 and 120.8 <= doc["lng"] <= 122.2
        (OUT / f"{pid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {pid}: {len(doc['images'])} photos", flush=True)

    mag_path = OUT / "maglev-pvg.json"
    mag = json.loads(mag_path.read_text())
    mag["category"] = "Technik"
    mag["name"] = "Shanghai Maglev"
    mag_path.write_text(json.dumps(mag, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    MANIFEST = [
        "the-bund", "shanghai-tower", "oriental-pearl-tower", "yu-garden", "city-god-temple",
        "nanjing-road", "peoples-square", "tianzifang", "xintiandi", "wukang-road", "jingan-temple",
        "huangpu-night-cruise", "lujiazui-riverside", "maglev-pvg", "shanghai-science-museum",
        "yangs-fried-dumplings", "jia-jia-tang-bao", "nanxiang-steamed-bun", "starbucks-reserve-roastery",
    ]
    (OUT / "manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")
    print("\nDONE")
    for pid in MANIFEST:
        d = json.loads((OUT / f"{pid}.json").read_text())
        print(f"  {pid}: {d['category']} · {len(d.get('images') or [])} · {d['name']}")

if __name__ == "__main__":
    main()
