#!/usr/bin/env python3
"""rig.py — transforma um sprite frontal SEM braços num boneco (puppet).

Passos (do SKILL):
- Pescoço: a linha alfa mais estreita abaixo da cabeça (busca entre 25% e 65% da altura).
- Soquetes dos ombros: primeira linha abaixo do pescoço com largura > 2x o pescoço = topo do tronco;
  os soquetes ficam nos cantos arredondados, recuados para dentro.
- Caixas dos olhos: componentes escuros pequenos e quase redondos dentro da cabeça, em par simétrico.
- Separa cabeça e corpo, e pinta o "buraco" sob a cabeça com a cor do próprio pescoço
  (estende o pescoço para cima) para o aceno nunca mostrar fresta.
- Cores: pele (moda da cabeça sem os escuros) e manga (amostra no soquete).
Saída: <nome>_body.png, <nome>_head.png, <nome>_head_<emoção>.png e um bloco no rig.json.

Uso: rig.py sprites_dir nome_base --front frank_front --alt shocked=frank_front_alt
"""
import argparse, json, pathlib
import cv2
import numpy as np
from PIL import Image


def row_widths(a):
    solid = a > 127
    w = np.zeros(a.shape[0], int)
    for y in range(a.shape[0]):
        xs = np.nonzero(solid[y])[0]
        w[y] = (xs[-1] - xs[0] + 1) if len(xs) else 0
    return w


def find_neck(a):
    h = a.shape[0]
    w = row_widths(a)
    lo, hi = int(h * 0.25), int(h * 0.65)
    seg = w[lo:hi].astype(float)
    seg[seg == 0] = 1e9
    m = seg.min()
    rows = np.nonzero(seg <= m * 1.03)[0] + lo  # todas as linhas "mais estreitas"
    # o ponto de corte fica no meio da faixa do pescoço
    neck_y = int(np.median(rows))
    xs = np.nonzero(a[neck_y] > 127)[0]
    return neck_y, int((xs[0] + xs[-1]) / 2), int(m), int(rows.min()), int(rows.max())


def find_sockets(a, neck_bottom, neck_w):
    w = row_widths(a)
    h = a.shape[0]
    top = next(y for y in range(neck_bottom, h) if w[y] > 2 * neck_w)
    # linha de referência: um pouco abaixo do topo, onde o canto arredondado já abriu
    ref = min(h - 1, top + int(0.05 * h))
    xs = np.nonzero(a[ref] > 127)[0]
    inset = int(0.035 * h)
    return top, [int(xs[0] + inset), ref], [int(xs[-1] - inset), ref]


def find_skin(rgb, a, neck_y):
    """Moda das cores numa faixa central do rosto (bochechas), acima da sombra do queixo.
    Não depende de limiar de luminância: funciona em pele clara e escura, e ignora o cabelo."""
    H, W = a.shape
    y0, y1 = max(0, neck_y - int(0.22 * H)), max(1, neck_y - int(0.10 * H))
    xs = np.nonzero(a[(y0 + y1) // 2] > 200)[0]
    cx, half = (xs[0] + xs[-1]) // 2, (xs[-1] - xs[0]) * 0.3
    band = rgb[y0:y1, int(cx - half):int(cx + half)][a[y0:y1, int(cx - half):int(cx + half)] > 200]
    return mode_colour(band)


def find_eyes(rgb, a, neck_y, skin):
    head = rgb[:neck_y].astype(int)
    lum = 0.2126 * head[..., 0] + 0.7152 * head[..., 1] + 0.0722 * head[..., 2]
    skin_lum = 0.2126 * skin[0] + 0.7152 * skin[1] + 0.0722 * skin[2]
    # escuro RELATIVO à pele: olho atrás de lente clara (Ralph) e pele escura (garçom) continuam funcionando
    dark = ((lum < skin_lum * 0.62) & (a[:neck_y] > 200)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(dark, connectivity=8)
    H = a.shape[0]
    cands = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if not (0.00015 * H * H < area < 0.004 * H * H):
            continue
        if not (0.55 < w / max(h, 1) < 1.6):  # olhos são redondos; sobrancelhas e chapéu não
            continue
        if y < neck_y * 0.3:  # abaixo do chapéu
            continue
        cands.append((x, y, w, h, cen[i]))
    best, score = None, 1e9
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            A, B = cands[i], cands[j]
            s = abs(A[4][1] - B[4][1]) + abs(A[2] * A[3] - B[2] * B[3]) * 0.01
            if abs(A[4][0] - B[4][0]) > 0.05 * H and s < score:
                best, score = (A, B), s
    if not best:
        return []
    eyes = sorted(best, key=lambda e: e[0])
    pad = 0.25
    return [[int(e[0] - e[2] * pad), int(e[1] - e[3] * pad), int(e[2] * (1 + 2 * pad)), int(e[3] * (1 + 2 * pad))] for e in eyes]


def mode_colour(px):
    q = (px // 6) * 6
    vals, counts = np.unique(q.reshape(-1, 3), axis=0, return_counts=True)
    return [int(v) + 3 for v in vals[counts.argmax()]]


def split(rgba, neck_y, neck_top, cx, ext):
    """Cabeça = linhas < neck_y (+ sobreposição); corpo = linhas >= neck_y, com o pescoço
    estendido para cima por `ext` px usando as cores da própria linha do pescoço."""
    h, w = rgba.shape[:2]
    overlap = max(2, int(0.006 * h))
    head = rgba[:neck_y + overlap].copy()
    body = np.zeros_like(rgba)
    body[neck_y:] = rgba[neck_y:]
    src = rgba[neck_y + 1]
    for y in range(max(0, neck_y - ext), neck_y):
        body[y] = src
    return head, body


def rig_one(sdir, name, front, alts):
    sdir = pathlib.Path(sdir)
    im = np.array(Image.open(sdir / f"{front}.png").convert("RGBA"))
    rgb, a = im[..., :3], im[..., 3]
    H, W = a.shape
    neck_y, neck_x, neck_w, ntop, nbot = find_neck(a)
    torso_top, sl, sr = find_sockets(a, nbot, neck_w)
    skin = find_skin(rgb, a, neck_y)
    eyes = find_eyes(rgb, a, neck_y, skin)
    if len(eyes) != 2:
        raise SystemExit(f"{name}: achei {len(eyes)} olhos (preciso de 2); confira {front}.png")
    sleeve = [int(v) for v in rgb[sl[1], sl[0]]]
    ext = int(0.05 * H)
    head, body = split(im, neck_y, ntop, neck_x, ext)
    Image.fromarray(head, "RGBA").save(sdir / f"{name}_head.png")
    Image.fromarray(body, "RGBA").save(sdir / f"{name}_body.png")
    heads = {"neutral": f"{name}_head.png"}
    for emo, sprite in alts.items():
        im2 = np.array(Image.open(sdir / f"{sprite}.png").convert("RGBA"))
        # o sheet foi desenhado com o mesmo corpo, então a mesma linha de pescoço serve;
        # se o tamanho divergir, recalcula
        ny2 = neck_y if im2.shape == im.shape else find_neck(im2[..., 3])[0]
        h2, _ = split(im2, ny2, ny2, neck_x, ext)
        Image.fromarray(h2, "RGBA").save(sdir / f"{name}_head_{emo}.png")
        heads[emo] = f"{name}_head_{emo}.png"
    return {
        "size": [W, H], "neck": [neck_x, neck_y], "neck_width": neck_w, "torso_top": torso_top,
        "sockets": {"l": sl, "r": sr}, "eyes": eyes, "skin": skin, "sleeve": sleeve,
        "body": f"{name}_body.png", "heads": heads,
    }


def debug_overlay(sdir, name, front, r):
    sdir = pathlib.Path(sdir)
    im = cv2.cvtColor(np.array(Image.open(sdir / f"{front}.png").convert("RGBA")), cv2.COLOR_RGBA2BGRA)
    bg = np.full_like(im, 255); a = im[..., 3:4] / 255.0
    out = (im[..., :3] * a + bg[..., :3] * (1 - a)).astype(np.uint8)
    cv2.line(out, (0, r["neck"][1]), (out.shape[1], r["neck"][1]), (0, 0, 255), 2)
    for k in ("l", "r"):
        cv2.circle(out, tuple(r["sockets"][k]), 10, (255, 0, 0), 3)
    for e in r["eyes"]:
        cv2.rectangle(out, (e[0], e[1]), (e[0] + e[2], e[1] + e[3]), (0, 200, 0), 2)
    cv2.imwrite(str(sdir / f"{name}_rig_debug.png"), out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sprites_dir"); ap.add_argument("name")
    ap.add_argument("--front", required=True)
    ap.add_argument("--alt", action="append", default=[], help="emoção=sprite")
    ap.add_argument("--extra", action="append", default=[], help="papel=sprite (side, back, pose_a...)")
    a = ap.parse_args()
    alts = dict(x.split("=") for x in a.alt)
    r = rig_one(a.sprites_dir, a.name, a.front, alts)
    r["whole"] = {k: f"{v}.png" for k, v in (x.split("=") for x in a.extra)}
    debug_overlay(a.sprites_dir, a.name, a.front, r)
    rp = pathlib.Path(a.sprites_dir) / "rig.json"
    allr = json.loads(rp.read_text()) if rp.exists() else {}
    allr[a.name] = r
    rp.write_text(json.dumps(allr, indent=2))
    (pathlib.Path(a.sprites_dir) / "rig.js").write_text("window.RIG=" + json.dumps(allr) + ";\n")
    print(json.dumps({k: r[k] for k in ("size", "neck", "sockets", "eyes", "skin", "sleeve")}))
