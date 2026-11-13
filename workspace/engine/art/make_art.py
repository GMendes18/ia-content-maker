#!/usr/bin/env python3
"""make_art.py — gera os plates e sheets de um vídeo a partir de um art.json.

art.json:
{ "plates": ["restaurant_1950_night", ...],
  "characters": { "frank": { ...CHAR_SPEC... } } }

Saída em videos/<nome>/art/: <plate>.png (3840x2160), <plate>.json (meta), <char>_base.png,
<plate>_grid.png (grade para medir os blanks) e contact_art.png.
Este é o substituto em código do modelo de imagem; com Gemini/GPT Image a saída é a mesma.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from characters import base_sheet
from plates import PLATES
from tiles import TILES
from svgkit import svg as mksvg
from quads import split as split_quad
import json as _json
from rasterize import rasterize_many
from PIL import Image, ImageDraw


def grid_overlay(png, out, step=100):
    im = Image.open(png).convert("RGB").resize((1920, 1080))
    d = ImageDraw.Draw(im)
    for x in range(0, 1920, step):
        d.line([(x, 0), (x, 1080)], fill=(255, 0, 255) if x % 500 == 0 else (255, 255, 255), width=1)
        d.text((x + 3, 3), str(x), fill=(255, 255, 255))
    for y in range(0, 1080, step):
        d.line([(0, y), (1920, y)], fill=(255, 0, 255) if y % 500 == 0 else (255, 255, 255), width=1)
        d.text((3, y + 3), str(y), fill=(255, 255, 255))
    im.save(out)


def main(video_dir):
    vd = pathlib.Path(video_dir)
    spec = json.loads((vd / "art.json").read_text())
    art = vd / "art"
    art.mkdir(parents=True, exist_ok=True)
    jobs = []
    for name in spec["plates"]:
        svg, meta = PLATES[name]()
        (art / f"{name}.json").write_text(json.dumps(meta, indent=2))
        jobs.append((svg, art / f"{name}.png", 2))
    for cname, cs in spec["characters"].items():
        jobs.append((base_sheet(cs), art / f"{cname}_base.png", 1))
    # quads: 4 lugares numa imagem 2x2 com calhas brancas (mesmo formato que viria do modelo de imagem)
    quad_specs = spec.get("quads", [])
    gut, Q = 24, (3840, 2160)
    QS = 2  # quads rasterizados em 2x → tiles 3840x2160 (o vertical amplia ~1.8x)
    for qi, names4 in enumerate(quad_specs):
        body, metas = [], {}
        s_ = min((1920 - gut / 2) / 1920, (1080 - gut / 2) / 1080)
        for k, (name, (qx, qy)) in enumerate(zip(names4, [(0, 0), (1920, 0), (0, 1080), (1920, 1080)])):
            o, meta = TILES[name]()
            ox = qx + (0 if qx == 0 else gut / 2) + ((1920 - gut / 2) - 1920 * s_) / 2
            oy = qy + (0 if qy == 0 else gut / 2) + ((1080 - gut / 2) - 1080 * s_) / 2
            body.append(f'<g transform="translate({ox:.2f},{oy:.2f}) scale({s_:.5f})"><svg width="1920" height="1080" overflow="hidden">{"".join(o)}</svg></g>')
            metas[name] = (meta, ox, oy, s_)
        jobs.append((mksvg(*Q, body, bg="#ffffff"), art / f"quad{qi}.png", QS))
        spec.setdefault("_quad_meta", []).append(metas)
    rasterize_many(jobs)
    tiles_dir = vd / "tiles"; tiles_dir.mkdir(exist_ok=True)
    for qi, names4 in enumerate(quad_specs):
        parts, gutters = split_quad(art / f"quad{qi}.png", (1920 * QS, 1080 * QS))
        for name, key in zip(names4, ["TL", "TR", "BL", "BR"]):
            tile, box = parts[key]; cx0, cy0, cw, ch = [v / QS for v in box]  # caixa de volta em unidades do SVG
            tile.save(tiles_dir / f"{name}.png")
            meta, ox, oy, s_ = spec["_quad_meta"][qi][name]
            def mp(x, y):  # desenho 1920x1080 → quad → tile final 1920x1080
                return [round((ox + x * s_ - cx0) * 1920 / cw, 1), round((oy + y * s_ - cy0) * 1080 / ch, 1)]
            def mr(r):
                a = mp(r[0], r[1]); b = mp(r[0] + r[2], r[1] + r[3]); return [a[0], a[1], round(b[0] - a[0], 1), round(b[1] - a[1], 1)]
            m2 = {"name": name, "kind": "tile", "size": [1920, 1080], "light": meta.get("light"),
                  "floor_y": mp(0, meta.get("floor_y", 1000))[1],
                  "blanks": {k: mr(v) for k, v in meta.get("blanks", {}).items()},
                  "portals": {k: mr(v) for k, v in meta.get("portals", {}).items()},
                  "anchors": {k: ([mp(*p) for p in v] if isinstance(v[0], (list, tuple)) else mp(*v)) for k, v in meta.get("anchors", {}).items()}}
            if "grid" in meta:
                gx, gy_, gw, gh = meta["grid"]; a = mp(gx, gy_); b = mp(gx + gw, gy_ + gh)
                m2["grid"] = [a[0], a[1], round(b[0] - a[0], 2), round(b[1] - a[1], 2)]
            (tiles_dir / f"{name}.json").write_text(_json.dumps(m2, indent=1))
        print(f"quad{qi}: calhas linhas {gutters['rows']} colunas {gutters['cols']} → {', '.join(names4)}")
    for name in spec["plates"]:
        grid_overlay(art / f"{name}.png", art / f"{name}_grid.png")
    # contact sheet da arte
    ims = [Image.open(j[1]).convert("RGB") for j in jobs]  # inclui os quads inteiros
    thumbs = [im.resize((640, int(640 * im.height / im.width))) for im in ims]
    H = sum(t.height for t in thumbs) + 20 * len(thumbs)
    sheet = Image.new("RGB", (680, H), (30, 30, 30))
    y = 10
    for t, j in zip(thumbs, jobs):
        sheet.paste(t, (20, y)); ImageDraw.Draw(sheet).text((24, y + 4), pathlib.Path(j[1]).name, fill=(255, 255, 255))
        y += t.height + 20
    sheet.save(art / "contact_art.png")
    print("arte ok:", [str(j[1].name) for j in jobs])


if __name__ == "__main__":
    main(sys.argv[1])
