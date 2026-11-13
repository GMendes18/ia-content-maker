#!/usr/bin/env python3
"""build_page.py — monta videos/<nome>/index.html ligando DNA, plates, rig, palavras e shots.
Uso: build_page.py videos/<nome> [--lang pt]
Os shots ficam em videos/<nome>/shots/*.js (um arquivo por capítulo, carregados em ordem).
"""
import argparse, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir"); ap.add_argument("--lang", default="pt")
    ap.add_argument("--format", default="landscape", choices=["landscape", "vertical"])
    a = ap.parse_args()
    vd = pathlib.Path(a.video_dir).resolve()
    rel = lambda p: "/" + str(pathlib.Path(p).resolve().relative_to(ROOT))
    dna = json.loads((ROOT / "dna.json").read_text())
    (ROOT / "dna.js").write_text("window.DNA=" + json.dumps(dna, ensure_ascii=False) + ";\n")
    plates = {}
    for meta_p in sorted((vd / "art").glob("*.json")):
        meta = json.loads(meta_p.read_text())
        png = meta_p.with_suffix(".png")
        if png.exists():
            meta["src"] = rel(png)
            plates[meta["name"]] = meta
    tiles = vd / "tiles"
    if tiles.exists():
        for meta_p in sorted(tiles.glob("*.json")):
            meta = json.loads(meta_p.read_text()); meta["src"] = rel(meta_p.with_suffix(".png")); plates[meta["name"]] = meta
    (vd / "plates.js").write_text("window.PLATES=" + json.dumps(plates) + ";\n")
    shots = sorted((vd / "shots").glob("*.js"))
    vcfg = json.loads((vd / "video.json").read_text()) if (vd / "video.json").exists() else {}
    stings = {}
    if vcfg.get("title"):
        stings["intro"] = {"title": vcfg["title"], "plate": vcfg["intro_plate"], "dur": 2.6, "night": vcfg.get("intro_night", 0)}
    if vcfg.get("outro_plate"):
        stings["outro"] = {"name": (dna["channel"].get("name") or "MEU CANAL").upper(), "plate": vcfg["outro_plate"], "dur": 3.6,
                           "char": vcfg.get("outro_char"), "floor": vcfg.get("outro_floor", 880), "night": vcfg.get("outro_night", 0)}
    accent = vcfg.get("accent", {}).get("banner_hex")
    font_file = ROOT / "engine" / "fonts" / (dna["traits"]["font"][0].replace(" ", "") + ".ttf")
    V = a.format == "vertical"; CW, CH = (1080, 1920) if V else (1920, 1080)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{vd.name}</title>
<style>html,body{{margin:0;background:#111}}canvas{{display:block;max-width:100vw;max-height:100vh}}</style></head>
<body><canvas id="c" width="{CW}" height="{CH}"></canvas>
<script>window.FORMAT={json.dumps(a.format)};window.CAPTIONS={json.dumps(V)};window.STINGS={json.dumps(stings, ensure_ascii=False)};window.ACCENT={json.dumps(accent)};window.LANG={json.dumps(a.lang)};window.FONT_URL={json.dumps(rel(font_file))};window.SPRITES={json.dumps(rel(vd / 'sprites') + '/')};</script>
<script src="/dna.js"></script><script src="plates.js"></script><script src="words.js"></script>
<script src="sprites/rig.js"></script><script src="/engine/runtime/engine.js"></script>
{''.join(f'<script src="shots/{s.name}"></script>' for s in shots)}
<script>ENGINE.boot().then(()=>{{const q=new URLSearchParams(location.search);if(q.has('t'))seek(+q.get('t'));else{{const t0=performance.now();(function f(){{seek(((performance.now()-t0)/1000)%END);requestAnimationFrame(f)}})()}}}}).catch(e=>{{window.BOOT_ERROR=String(e);console.error(e)}});</script>
</body></html>"""
    page = "index_vertical.html" if V else "index.html"
    (vd / page).write_text(html)
    print(f"{page}: {len(plates)} plates, {len(shots)} arquivo(s) de shots")


if __name__ == "__main__":
    main()
