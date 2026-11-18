#!/usr/bin/env python3
"""
Build an offline map for GPSMap on the PSP from OpenStreetMap data.

  python make_map.py                              (it asks which place you want)
  python make_map.py "Madison County, Alabama"    (look the place up by name)
  python make_map.py --bbox S W N E --name mymap  (give the area yourself)

Only needs Python 3 (no extra packages). Map data (c) OpenStreetMap contributors, ODbL.
"""
import argparse, json, math, os, shutil, struct, sys, time, unicodedata, urllib.request, urllib.parse
from array import array

# Jefferson County, AL with a little margin: south, west, north, east
DEFAULT_BBOX = (33.20, -87.38, 33.86, -86.45)
CELL = 0.02          # degrees per grid cell (~2 km)
SERVERS = ["https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]

CLASS_OF = {
    "motorway": 0, "motorway_link": 0, "trunk": 0, "trunk_link": 0,
    "primary": 1, "primary_link": 1,
    "secondary": 2, "secondary_link": 2, "tertiary": 2, "tertiary_link": 2,
    "residential": 3, "unclassified": 3, "living_street": 3,
    "service": 4, "road": 4,
}

# Searchable places ("POIs"). They only appear in the PSP's Find menu, never as clutter on the map.
# Edit this list to add or remove categories (keep the order: the PSP app has the same list).
POI_CATEGORIES = ["Gas stations", "Hospitals", "Urgent care", "Pharmacies", "Grocery stores", "Convenience stores",
                  "Restaurants", "Fast food", "Coffee shops", "Banks", "ATMs", "Post offices", "Police", "Fire stations", "Hotels"]
POI_DEFAULT_NAME = ["Gas station", "Hospital", "Urgent care", "Pharmacy", "Grocery", "Convenience store",
                    "Restaurant", "Fast food", "Coffee shop", "Bank", "ATM", "Post office", "Police", "Fire station", "Hotel"]
AMENITY_CAT = {"fuel": 0, "hospital": 1, "pharmacy": 3, "restaurant": 6, "fast_food": 7, "cafe": 8, "bank": 9,
               "atm": 10, "post_office": 11, "police": 12, "fire_station": 13}
SHOP_CAT = {"supermarket": 4, "convenience": 5}
TOURISM_CAT = {"hotel": 14, "motel": 14}
URGENT_WORDS = ("urgent", "immediate", "walk-in", "walk in", "express care")

def poi_category(tags):
    if tags.get("healthcare") == "urgent_care":
        return 2
    am = tags.get("amenity")
    if am == "clinic" and any(w in tags.get("name", "").lower() for w in URGENT_WORDS):
        return 2
    if am in AMENITY_CAT:
        return AMENITY_CAT[am]
    if tags.get("shop") in SHOP_CAT:
        return SHOP_CAT[tags["shop"]]
    if tags.get("tourism") in TOURISM_CAT:
        return TOURISM_CAT[tags["tourism"]]
    return None

# villages get their own type so they can be shown when zoomed out (suburbs and neighbourhoods are not)
PLACE_TYPE = {"city": 0, "town": 1, "suburb": 2, "village": 4, "hamlet": 3, "neighbourhood": 3}
PLACE_ORDER = {0: 0, 1: 1, 4: 2, 2: 3, 3: 4}      # importance order in the file: bigger places first

def ascii_name(text):
    """The PSP font is ASCII only: strip accents, drop anything else."""
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").strip()
    return t[:30]

def label_for(tags, cls):
    name = ascii_name(tags.get("name", ""))
    ref = ascii_name(tags.get("ref", "").split(";")[0]) if tags.get("ref") else ""
    if cls <= 1 and ref:
        return ref
    return name or ref

# ---------------------------------------------------------------------------------------------
# Routing graph: junctions become nodes, the road pieces between them become directed edges.
# ---------------------------------------------------------------------------------------------
DEFAULT_KMH = {"motorway": 105, "motorway_link": 55, "trunk": 80, "trunk_link": 50, "primary": 65, "primary_link": 45,
               "secondary": 55, "secondary_link": 45, "tertiary": 50, "tertiary_link": 40, "residential": 40,
               "unclassified": 45, "living_street": 15, "service": 20, "road": 30}
SPEED_FACTOR = 0.8     # real trips are slower than the posted limit (lights, turns, traffic)
NO_SERVICE = ("driveway", "parking_aisle", "drive-through", "emergency_access")

def parse_kmh(tags, hw):
    v = tags.get("maxspeed", "").strip().lower()
    kmh = None
    try:
        if v.endswith("mph"):
            kmh = float(v.split()[0]) * 1.609
        elif v and v[0].isdigit():
            kmh = float(v.split()[0])
    except ValueError:
        kmh = None
    return kmh if kmh and 5 <= kmh <= 140 else DEFAULT_KMH[hw]

def oneway_dir(tags, hw):
    ow = tags.get("oneway", "").lower()
    if ow in ("yes", "true", "1"): return 1
    if ow in ("-1", "reverse"): return -1
    if ow == "no": return 0
    if tags.get("junction") in ("roundabout", "circular") or hw in ("motorway", "motorway_link"): return 1
    return 0

def routable(tags):
    hw = tags.get("highway")
    if hw not in CLASS_OF: return False
    if tags.get("access") in ("no", "private") or tags.get("motor_vehicle") in ("no", "private"): return False
    if hw == "service" and tags.get("service") in NO_SERVICE: return False
    return True

def seg_m(a, b):
    dy = (a[0] - b[0]) * 110540.0
    dx = (a[1] - b[1]) * 111320.0 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)

def build_graph(elements, nid):
    """Returns the binary routing sections (nodes, csr, edges, einfo, geom) and counts."""
    ways = []; use = {}
    def pack(lat, lon):
        return (int(round(lat * 1e7)) + 900000000) * 4000000000 + (int(round(lon * 1e7)) + 1800000000)
    for el in elements:
        if el.get("kind") == "poi" or el.get("type") != "way" or "geometry" not in el:
            continue
        tags = el.get("tags", {})
        if not routable(tags): continue
        g = el["geometry"]
        if len(g) < 2: continue
        hw = tags["highway"]
        keys = [pack(p["lat"], p["lon"]) for p in g]
        coords = [(p["lat"], p["lon"]) for p in g]
        for k in keys: use[k] = use.get(k, 0) + 1
        use[keys[0]] += 1; use[keys[-1]] += 1          # way ends always count as junctions
        ways.append((keys, coords, parse_kmh(tags, hw), CLASS_OF[hw], oneway_dir(tags, hw), nid(label_for(tags, CLASS_OF[hw]))))
    junction = {k for k, c in use.items() if c >= 2}
    del use

    node_index = {}; nodes = array("f"); chains = []; edges = []
    def node(key, c):
        i = node_index.get(key)
        if i is None:
            i = len(nodes) // 2; node_index[key] = i; nodes.append(c[0]); nodes.append(c[1])
        return i
    for keys, coords, kmh, cls, ow, name in ways:
        eff = max(5, min(255, int(round(kmh * SPEED_FACTOR))))
        start = 0; length = 0.0
        for i in range(1, len(keys)):
            length += seg_m(coords[i - 1], coords[i])
            if keys[i] in junction or i == len(keys) - 1:
                a = node(keys[start], coords[start]); b = node(keys[i], coords[i])
                cid = len(chains); chains.append(coords[start:i + 1])
                ln = max(1, min(65535, int(round(length))))
                if ow >= 0: edges.append((a, b, ln, eff, cls, name, cid, 0))
                if ow <= 0: edges.append((b, a, ln, eff, cls, name, cid, 1))
                start = i; length = 0.0
    edges.sort(key=lambda e: e[0])
    n = len(nodes) // 2
    csr = array("I", [0]) * (n + 1)
    for e in edges: csr[e[0] + 1] += 1
    for i in range(n): csr[i + 1] += csr[i]
    geom = bytearray(); goff = []
    for c in chains:
        goff.append(len(geom))
        for la, lo in c: geom += struct.pack("<ff", la, lo)
    eb = bytearray(); ei = bytearray()
    for (a, b, ln, eff, cls, name, cid, rev) in edges:
        eb += struct.pack("<IHBB", b, ln, eff, cls)
        ei += struct.pack("<IIHBB", name, goff[cid], len(chains[cid]), rev, 0)
    return {"nodes": nodes.tobytes(), "csr": csr.tobytes(), "edges": bytes(eb), "einfo": bytes(ei), "geom": bytes(geom),
            "n": n, "m": len(edges)}

# ---------------------------------------------------------------------------------------------
# Finding an area by name (OpenStreetMap's Nominatim search) and sizing the download
# ---------------------------------------------------------------------------------------------
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "psp-gpsmap-builder/1.0 (free hobby PSP GPS project)"
WARN_KM2 = 10000       # Jefferson County (~6,400 km2) is the largest area tested on a real PSP so far
BLOCK_KM2 = 40000

def bbox_km(bbox):
    s, w, n, e = bbox
    return (e - w) * 111.32 * math.cos(math.radians((s + n) / 2)), (n - s) * 110.54

def expand_bbox(bbox, margin_km, min_km=10.0):
    """Add a margin around a place and make sure tiny places (a building, a village) still get a usable area."""
    s, w, n, e = bbox
    mid = (s + n) / 2
    dlat = margin_km / 110.54; dlon = margin_km / (111.32 * math.cos(math.radians(mid)))
    s, n, w, e = s - dlat, n + dlat, w - dlon, e + dlon
    wk, hk = bbox_km((s, w, n, e))
    if hk < min_km:
        pad = (min_km - hk) / 2 / 110.54; s -= pad; n += pad
    if wk < min_km:
        pad = (min_km - wk) / 2 / (111.32 * math.cos(math.radians(mid))); w -= pad; e += pad
    return (round(s, 4), round(w, 4), round(n, 4), round(e, 4))

def plan_pieces(bbox, piece_km=30.0):
    """How many download pieces (rows, columns): about 30 km each, so busy cities do not time out."""
    wk, hk = bbox_km(bbox)
    return max(1, int(math.ceil(hk / piece_km))), max(1, int(math.ceil(wk / piece_km)))

def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    t = "".join(c if c.isalnum() else "_" for c in t).strip("_")
    while "__" in t: t = t.replace("__", "_")
    return t[:40] or "map"

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def geocode(query, limit=6):
    """Look a place name up. Returns a list of {name, kind, bbox=(s,w,n,e)}."""
    url = NOMINATIM + "?" + urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": limit, "accept-language": "en"})
    last = None
    for attempt in range(3):
        try:
            data = http_get_json(url)
            break
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    else:
        raise SystemExit("Could not reach the place search service (%s).\nCheck your internet connection, or give the area yourself with --bbox SOUTH WEST NORTH EAST." % last)
    out = []
    for r in data:
        try:
            s, n, w, e = (float(x) for x in r["boundingbox"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append({"name": r.get("display_name", query), "kind": "%s/%s" % (r.get("category") or r.get("class") or "?", r.get("type", "?")), "bbox": (s, w, n, e)})
    return out

def choose_place(results, pick=None, interactive=True):
    if not results:
        raise SystemExit("No place found with that name. Try adding the state or country, e.g. \"Madison County, Alabama, USA\".")
    if pick is not None:
        if not 1 <= pick <= len(results): raise SystemExit("--pick must be between 1 and %d" % len(results))
        return results[pick - 1]
    if len(results) == 1 or not interactive:
        return results[0]
    print("\nI found these places:")
    for i, r in enumerate(results, 1):
        wk, hk = bbox_km(r["bbox"])
        print("  %d) %s\n       (%s, about %.0f x %.0f km)" % (i, r["name"], r["kind"], wk, hk))
    while True:
        ans = input("\nWhich one? (1-%d, or just press Enter for 1): " % len(results)).strip()
        if ans == "": return results[0]
        if ans.isdigit() and 1 <= int(ans) <= len(results): return results[int(ans) - 1]

def check_size(bbox, force=False, interactive=True, assume_yes=False):
    wk, hk = bbox_km(bbox); area = wk * hk
    nlat, nlon = plan_pieces(bbox)
    print("\nArea: about %.0f x %.0f km (%.0f square km), downloaded in %d pieces." % (wk, hk, area, nlat * nlon))
    if area > BLOCK_KM2 and not force:
        raise SystemExit("That area is too big for the PSP (the largest I have tested is about 6,400 square km).\nPick a smaller place such as a county or a city, or add --force if you want to try anyway.")
    if area > WARN_KM2:
        print("WARNING: this is larger than anything tested on a real PSP (about 6,400 square km). The map may be too big for the PSP's memory.")
    minutes = (2 * nlat * nlon + 1) * 0.7
    print("The download can take roughly %d-%d minutes. Please leave this window open." % (max(1, minutes * 0.5), minutes * 1.5))
    if interactive and not assume_yes:
        if input("Continue? [Y/n] ").strip().lower().startswith("n"): raise SystemExit("Cancelled.")

def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]

def overpass(query):
    data = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for attempt in range(10):
        server = SERVERS[attempt % len(SERVERS)]
        try:
            req = urllib.request.Request(server, data=data, headers={"User-Agent": "psp-gpsmap-builder/1.0"})
            with urllib.request.urlopen(req, timeout=400) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            print("   retry (%s)" % e, file=sys.stderr)
            time.sleep(min(60, 10 * (attempt + 1)))
    raise SystemExit("Download failed: %s" % last)

def download(bbox, nlat=None, nlon=None):
    s, w, n, e = bbox
    if nlat is None: nlat, nlon = plan_pieces(bbox)
    total_pieces = nlat * nlon
    ways = {}
    classes = "|".join(CLASS_OF)
    # downloaded pieces are cached per area, so building a different area never reuses the wrong data
    cache_dir = os.path.join("map_cache", "%.4f_%.4f_%.4f_%.4f" % tuple(bbox))
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
        if tuple(bbox) == DEFAULT_BBOX and os.path.isdir("map_cache"):      # keep the Jefferson County data from earlier runs
            for fn in os.listdir("map_cache"):
                src = os.path.join("map_cache", fn)
                if os.path.isfile(src) and fn.endswith(".json"):
                    shutil.move(src, os.path.join(cache_dir, fn))
    if tuple(bbox) == DEFAULT_BBOX and os.path.exists("overpass_cache.json"):
        print("Using road data from overpass_cache.json (delete it to download fresh data).")
        for el in json.load(open("overpass_cache.json", encoding="utf-8")).get("elements", []):
            if el.get("type") == "way":
                ways[el["id"]] = el
    else:
        for i in range(nlat):
            for j in range(nlon):
                n_piece = i * nlon + j + 1
                cache = os.path.join(cache_dir, "piece_%d_of_%d.json" % (n_piece, total_pieces))
                if os.path.exists(cache):
                    print("Piece %d of %d already downloaded, skipping." % (n_piece, total_pieces))
                    elements = json.load(open(cache, encoding="utf-8"))
                else:
                    bs = s + (n - s) * i / nlat; bn = s + (n - s) * (i + 1) / nlat
                    bw = w + (e - w) * j / nlon; be = w + (e - w) * (j + 1) / nlon
                    print("Downloading piece %d of %d ..." % (n_piece, total_pieces))
                    q = '[out:json][timeout:300];way["highway"~"^(%s)$"](%f,%f,%f,%f);out geom;' % (classes, bs, bw, bn, be)
                    elements = overpass(q).get("elements", [])
                    json.dump(elements, open(cache, "w", encoding="utf-8"))
                for el in elements:
                    if el.get("type") == "way":
                        ways[el["id"]] = el
    # place names (cities, towns, suburbs ...)
    pcache = os.path.join(cache_dir, "places.json")
    if os.path.exists(pcache):
        print("Place names already downloaded, skipping.")
        places = json.load(open(pcache, encoding="utf-8"))
    else:
        print("Downloading place names ...")
        q = '[out:json][timeout:120];node["place"~"^(%s)$"](%f,%f,%f,%f);out;' % ("|".join(PLACE_TYPE), s, w, n, e)
        places = overpass(q).get("elements", [])
        json.dump(places, open(pcache, "w", encoding="utf-8"))
    # searchable places, downloaded in pieces and cached like the roads
    pois = {}
    for i in range(nlat):
        for j in range(nlon):
            n_piece = i * nlon + j + 1
            cache = os.path.join(cache_dir, "poi_piece_%d_of_%d.json" % (n_piece, total_pieces))
            if os.path.exists(cache):
                print("Place-search piece %d of %d already downloaded, skipping." % (n_piece, total_pieces))
                elements = json.load(open(cache, encoding="utf-8"))
            else:
                bs = s + (n - s) * i / nlat; bn = s + (n - s) * (i + 1) / nlat
                bw = w + (e - w) * j / nlon; be = w + (e - w) * (j + 1) / nlon
                box = "(%f,%f,%f,%f)" % (bs, bw, bn, be)
                print("Downloading place-search piece %d of %d ..." % (n_piece, total_pieces))
                q = ('[out:json][timeout:300];('
                     'nwr["amenity"~"^(fuel|hospital|pharmacy|restaurant|fast_food|cafe|bank|atm|post_office|police|fire_station)$"]%s;'
                     'nwr["shop"~"^(supermarket|convenience)$"]%s;'
                     'nwr["tourism"~"^(hotel|motel)$"]%s;'
                     'nwr["healthcare"="urgent_care"]%s;'
                     'nwr["amenity"="clinic"]["name"~"urgent|immediate|walk|express",i]%s;'
                     ');out center tags;') % (box, box, box, box, box)
                elements = overpass(q).get("elements", [])
                json.dump(elements, open(cache, "w", encoding="utf-8"))
            for el in elements:
                pois[(el.get("type"), el.get("id"))] = el
    return list(ways.values()) + [p for p in places if p.get("type") == "node"] + [{"kind": "poi", **p} for p in pois.values()]

def densify(pts, step):
    out = [pts[0]]
    for (la, lo) in pts[1:]:
        pla, plo = out[-1]
        d = max(abs(la - pla), abs(lo - plo))
        if d > step:
            k = int(math.ceil(d / step))
            for t in range(1, k):
                out.append((pla + (la - pla) * t / k, plo + (lo - plo) * t / k))
        out.append((la, lo))
    return out

def build(elements, bbox, outfile, routing=True):
    s, w, n, e = bbox
    lat0, lon0 = f32(s), f32(w)
    ncols = int(math.ceil((e - w) / CELL)); nrows = int(math.ceil((n - s) / CELL))
    cells = {}
    total = 0
    span = 3 * CELL
    names = []; name_id = {}

    def nid(text):
        if not text:
            return 0xFFFFFFFF
        if text not in name_id:
            name_id[text] = len(names); names.append(text)
        return name_id[text]

    def enc(v, origin):
        return max(0, min(65535, int(round((v - origin) / span * 65535))))

    places = []
    pois = []          # (lat, lon, name_id, category)
    seen_poi = {}      # (category, name) -> [(lat, lon)] for removing duplicate buildings of one place
    for el in elements:
        tags = el.get("tags", {})
        if el.get("kind") == "poi":
            cat = poi_category(tags)
            if cat is None:
                continue
            lat = el.get("lat", el.get("center", {}).get("lat")); lon = el.get("lon", el.get("center", {}).get("lon"))
            if lat is None or lon is None:
                continue
            nm = ascii_name(tags.get("name", "") or tags.get("brand", "") or tags.get("operator", "")) or POI_DEFAULT_NAME[cat]
            prev = seen_poi.setdefault((cat, nm.lower()), [])
            if any(abs(lat - a) < 0.0015 and abs(lon - b) < 0.0015 for a, b in prev):
                continue
            prev.append((lat, lon))
            pois.append((lat, lon, nid(nm), cat))
            continue
        if el.get("type") == "node":
            ptype = PLACE_TYPE.get(tags.get("place"))
            nm = ascii_name(tags.get("name", ""))
            if ptype is not None and nm and "lat" in el:
                try: pop = int(str(tags.get("population", "0")).replace(",", "").split()[0])
                except (ValueError, IndexError): pop = 0
                places.append((el["lat"], el["lon"], nid(nm), ptype, pop))
            continue
        hw = tags.get("highway")
        if hw not in CLASS_OF or "geometry" not in el:
            continue
        pts = [(p["lat"], p["lon"]) for p in el["geometry"]]
        if len(pts) < 2:
            continue
        cls = CLASS_OF[hw]
        label = nid(label_for(tags, cls))
        pts = densify(pts, CELL * 0.5)

        def cell_of(p):
            return (int(math.floor((p[0] - lat0) / CELL)), int(math.floor((p[1] - lon0) / CELL)))

        def flush(run, cell):
            nonlocal total
            r, c = cell
            if len(run) < 2 or not (0 <= r < nrows and 0 <= c < ncols):
                return
            olat = lat0 + r * CELL - CELL; olon = lon0 + c * CELL - CELL
            body = b"".join(struct.pack("<HH", enc(p[1], olon), enc(p[0], olat)) for p in run)
            cells.setdefault(cell, []).append(struct.pack("<BBHI", cls, 0, len(run), label) + body)
            total += 1

        cur = cell_of(pts[0]); run = [pts[0]]
        for p in pts[1:]:
            c = cell_of(p)
            if c != cur:
                run.append(p)
                flush(run, cur)
                run = [run[-2], p]
                cur = c
            else:
                run.append(p)
        flush(run, cur)

    places.sort(key=lambda p: (PLACE_ORDER[p[3]], -p[4]))      # most important first: they win when names overlap
    places = [p[:4] for p in places]
    header_size = 88
    index_size = ncols * nrows * 8
    data = bytearray(); index = []
    for r in range(nrows):
        for c in range(ncols):
            recs = cells.get((r, c), [])
            index.append((header_size + index_size + len(data), len(recs)))
            for rec in recs:
                data += rec

    graph = build_graph(elements, nid) if routing else None
    names_index_off = header_size + index_size + len(data)
    blob_off = names_index_off + 4 * len(names)
    blob = bytearray(); offs = []
    for t in names:
        offs.append(blob_off + len(blob))
        blob += t.encode("ascii") + b"\0"
    places_off = blob_off + len(blob)
    pois_off = places_off + 16 * len(places)

    pois_end = pois_off + 16 * len(pois)
    pad = (-pois_end) % 8
    nodes_off = pois_end + pad
    if graph:
        gn, gm = graph["n"], graph["m"]
        csr_off = nodes_off + len(graph["nodes"])
        edges_off = csr_off + len(graph["csr"])
        einfo_off = edges_off + len(graph["edges"])
        geom_off = einfo_off + len(graph["einfo"])
    else:
        gn = gm = 0; csr_off = edges_off = einfo_off = geom_off = nodes_off
    with open(outfile, "wb") as f:
        f.write(b"PMAP")
        f.write(struct.pack("<IfffIII", 4, lat0, lon0, CELL, ncols, nrows, total))
        f.write(struct.pack("<IIII", len(names), names_index_off, len(places), places_off))
        f.write(struct.pack("<II", len(pois), pois_off))
        f.write(struct.pack("<IIIIIII", gn, gm, nodes_off, csr_off, edges_off, einfo_off, geom_off))
        f.write(b"\0" * 4)
        for off, cnt in index:
            f.write(struct.pack("<II", off, cnt))
        f.write(data)
        for o in offs:
            f.write(struct.pack("<I", o))
        f.write(blob)
        for (la, lo, nm, pt) in places:
            f.write(struct.pack("<ffIBBBB", la, lo, nm, pt, 0, 0, 0))
        for (la, lo, nm, ct) in pois:
            f.write(struct.pack("<ffIBBBB", la, lo, nm, ct, 0, 0, 0))
        f.write(b"\0" * pad)
        if graph:
            for k in ("nodes", "csr", "edges", "einfo", "geom"):
                f.write(graph[k])
    size = (geom_off + len(graph["geom"])) if graph else pois_end
    counts = {}
    for p in pois:
        counts[p[3]] = counts.get(p[3], 0) + 1
    print("Wrote %s: %d road pieces, %d place names, %d labels, %.1f MB, grid %dx%d" % (outfile, total, len(places), len(names), size / 1e6, ncols, nrows))
    if graph:
        resident = (len(graph["nodes"]) + len(graph["csr"]) + len(graph["edges"])) / 1e6 + einfo_off / 1e6
        print("Routing network: %d junctions, %d directed road links; needs about %.1f MB of PSP memory" % (gn, gm, resident))
        if resident > 16:
            print("WARNING: this is large for the PSP's memory; routing may fail to load. Tell Claude these numbers.")
    print("Searchable places: %d  (%s)" % (len(pois), ", ".join("%s %d" % (POI_CATEGORIES[c], counts[c]) for c in sorted(counts))))

def main():
    ap = argparse.ArgumentParser(description="Build an offline map for GPSMap on the PSP. Type a place name, or give --bbox.")
    ap.add_argument("place", nargs="?", help='place to map, e.g. "Madison County, Alabama" (if left out, you will be asked)')
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("S", "W", "N", "E"), help="give the area yourself instead of searching")
    ap.add_argument("--input", help="Overpass JSON file (skip the download)")
    ap.add_argument("--name", help="name shown in the PSP map menu (default: made from the place name)")
    ap.add_argument("--out", help="output file (default: NAME.pmap)")
    ap.add_argument("--margin", type=float, default=2.0, help="extra kilometres around the place (default 2)")
    ap.add_argument("--pick", type=int, help="if several places match, use this one (1 = best match)")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    ap.add_argument("--force", action="store_true", help="allow very large areas")
    ap.add_argument("--no-routing", action="store_true", help="skip the routing network (smaller file)")
    a = ap.parse_args()
    asked = a.place is None and a.bbox is None and a.input is None     # started without arguments (e.g. double-clicked)
    interactive = sys.stdin.isatty() and not a.yes

    name = a.name
    if a.input:
        bbox = tuple(a.bbox) if a.bbox else DEFAULT_BBOX
        elements = json.load(open(a.input, encoding="utf-8")).get("elements", [])
        name = name or "map"
    else:
        if a.bbox:
            bbox = tuple(a.bbox); name = name or "map"
        else:
            query = a.place
            if not query:
                print("GPSMap map maker")
                print("Type the place you want a map of, for example:  Madison County, Alabama")
                query = input("> ").strip()
                if not query: raise SystemExit("No place entered.")
            print("Looking up \"%s\" ..." % query)
            time.sleep(1)                                                     # be polite to the free search service
            place = choose_place(geocode(query), a.pick, interactive)
            print("Using: %s" % place["name"])
            bbox = expand_bbox(place["bbox"], a.margin)
            name = name or slug(", ".join(place["name"].split(",")[:2]))
        check_size(bbox, a.force, interactive, a.yes)
        elements = download(bbox)
    out = a.out or (name + ".pmap")
    build(elements, bbox, out, routing=not a.no_routing)
    print("\nDone! Copy %s into the GPSMap folder on your PSP's memory stick (ms0:/PSP/GAME/GPSMap/)." % out)
    print("It will then show up under START > Change map.")
    if asked and sys.stdin.isatty():
        input("\nPress Enter to close this window.")

if __name__ == "__main__":
    main()
