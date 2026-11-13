#!/usr/bin/env python3
"""cutout.py — recorta sheets de chroma (verde #00B140 ou magenta #FF00FF) em sprites nomeados.

Regras (do SKILL):
- Fundo = pixels CONECTADOS À BORDA com dominância de chroma > 40 e a até 110 da mediana do chroma.
  Só a partir da borda, senão roupa escura vaza.
- Faixa alfa suave de 2 px; dentro dela, despill (verde: G <= max(R,B)+6; magenta: min(R,B) <= G+6).
- Agrupa as peças por figura (dilatação), descarta ciscos, nomeia e gera contact sheet.

Uso: cutout.py sheet.png outdir --names a,b,c,... [--key magenta|green]
"""
import argparse, json, pathlib
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def chroma_mask(rgb, key):
    r, g, b = (rgb[..., i].astype(np.int32) for i in range(3))
    if key == "green":
        dom = g - np.maximum(r, b)
    else:  # magenta
        dom = np.minimum(r, b) - g
    cand = dom > 40
    med = np.median(rgb[cand], axis=0) if cand.any() else np.array([0, 177, 64] if key == "green" else [255, 0, 255])
    dist = np.linalg.norm(rgb.astype(np.int32) - med, axis=-1)
    cand &= dist < 110
    # só os componentes que tocam a borda
    n, lab = cv2.connectedComponents(cand.astype(np.uint8), connectivity=8)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border > 0]
    bg = np.isin(lab, border)
    # 2ª passada: buracos fechados (entre braço e corpo) só se forem chroma QUASE puro e grandes;
    # o limiar estrito evita que roupa escura ou vermelha vire buraco.
    strict = (dom > 120) & (dist < 45) & ~bg
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(strict.astype(np.uint8), connectivity=8)
    for i in range(1, n2):
        if st2[i, cv2.CC_STAT_AREA] > 60:
            bg |= lab2 == i
    return bg, med


def soft_alpha(bg, rgb, key, band=2.0):
    fg = (~bg).astype(np.uint8)
    dist = cv2.distanceTransform(fg, cv2.DIST_L2, 3)  # distância até o fundo
    alpha = np.clip(dist / band, 0, 1)
    alpha[fg == 0] = 0
    out = rgb.astype(np.int32).copy()
    inband = (fg == 1) & (dist <= band + 0.5)
    r, g, b = out[..., 0], out[..., 1], out[..., 2]
    if key == "green":
        cap = np.maximum(r, b) + 6
        g[inband] = np.minimum(g[inband], cap[inband])
    else:
        excess = np.clip(np.minimum(r, b) - g - 6, 0, None)
        r[inband] -= excess[inband]
        b[inband] -= excess[inband]
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out, (alpha * 255).astype(np.uint8)


def group_figures(alpha, min_frac=0.0005, gap=18):
    solid = (alpha > 127).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(solid, connectivity=8)
    keep = np.zeros_like(solid)
    min_area = min_frac * solid.size
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            keep[lab == i] = 1
    grown = cv2.dilate(keep, np.ones((gap * 2 + 1, gap * 2 + 1), np.uint8))
    n2, lab2, stats2, _ = cv2.connectedComponentsWithStats(grown, connectivity=8)
    figs = []
    for i in range(1, n2):
        x, y, w, h = stats2[i, :4]
        figs.append({"label": i, "box": [int(x), int(y), int(w), int(h)]})
    figs.sort(key=lambda f: (round(f["box"][1] / 400), f["box"][0]))  # linha a linha, esquerda→direita
    return figs, lab2, keep


def cut(sheet, outdir, names, key):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    rgb = np.array(Image.open(sheet).convert("RGB"))
    bg, med = chroma_mask(rgb, key)
    rgb2, alpha = soft_alpha(bg, rgb, key)
    figs, lab, keep = group_figures(alpha)
    if names and len(names) != len(figs):
        raise SystemExit(f"{sheet}: achei {len(figs)} figuras, mas recebi {len(names)} nomes")
    out = []
    for i, f in enumerate(figs):
        x, y, w, h = f["box"]
        m = (lab[y:y + h, x:x + w] == f["label"])
        a = alpha[y:y + h, x:x + w] * m
        ys, xs = np.nonzero(a > 8)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        rgba = np.dstack([rgb2[y:y + h, x:x + w], a])[y0:y1, x0:x1]
        name = names[i] if names else f"fig{i}"
        p = outdir / f"{name}.png"
        Image.fromarray(rgba, "RGBA").save(p)
        out.append({"name": name, "file": p.name, "size": [int(x1 - x0), int(y1 - y0)],
                    "sheet_box": [int(x + x0), int(y + y0), int(x1 - x0), int(y1 - y0)]})
    return out, med


def contact_sheet(sprites, outdir, path):
    outdir = pathlib.Path(outdir)
    th = 360
    ims = [Image.open(outdir / s["file"]) for s in sprites]
    ws = [max(1, int(im.width * th / im.height)) for im in ims]
    W = sum(ws) + 30 * (len(ims) + 1)
    sheet = Image.new("RGB", (max(W, 400), th + 80), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    # xadrez para ver a transparência e a franja
    for yy in range(0, th + 80, 20):
        for xx in range(0, sheet.width, 20):
            if (xx // 20 + yy // 20) % 2:
                d.rectangle([xx, yy, xx + 19, yy + 19], fill=(215, 215, 215))
    x = 30
    try:
        font = ImageFont.truetype(str(pathlib.Path(__file__).parent / "fonts" / "Lexend.ttf"), 22)
    except Exception:
        font = None
    for im, w, s in zip(ims, ws, sprites):
        t = im.resize((w, th), Image.LANCZOS)
        sheet.paste(t, (x, 20), t)
        d.text((x, th + 34), s["name"], fill=(20, 20, 20), font=font)
        x += w + 30
    sheet.save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("outdir")
    ap.add_argument("--names", default="")
    ap.add_argument("--key", default=None)
    a = ap.parse_args()
    key = a.key
    if key is None:
        dna = json.loads((pathlib.Path(__file__).resolve().parents[1] / "dna.json").read_text())
        key = dna["chroma_key"]["name"]
    names = [n for n in a.names.split(",") if n]
    sprites, med = cut(a.sheet, a.outdir, names, key)
    stem = pathlib.Path(a.sheet).stem
    contact_sheet(sprites, a.outdir, pathlib.Path(a.outdir) / f"contact_{stem}.png")
    (pathlib.Path(a.outdir) / f"{stem}.sprites.json").write_text(json.dumps(sprites, indent=2))
    print(f"{len(sprites)} sprites, chroma mediano {med.astype(int).tolist()}: " + ", ".join(s["name"] for s in sprites))
