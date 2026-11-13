#!/usr/bin/env python3
"""quads.py — divide uma imagem 2x2 em 4 tiles 1920x1080.

Regra do SKILL: acha a linha e a coluna mais brancas perto do centro, anda para fora enquanto a
linha continua > 60% branca, apara mais 6 px; também apara bordas externas brancas; corta cada
quadrante em 16:9 (centro) e redimensiona para 1920x1080.
Devolve as caixas de corte (para converter os metadados dos tiles).
"""
import numpy as np
from PIL import Image

WHITE = 240


def _white_frac(a, axis):
    return (a.min(axis=2) > WHITE).mean(axis=axis)


def _gutter(frac, n):
    lo, hi = int(n * 0.4), int(n * 0.6)
    c = lo + int(np.argmax(frac[lo:hi]))
    a = c
    while a > 0 and frac[a - 1] > 0.6:
        a -= 1
    b = c
    while b < n - 1 and frac[b + 1] > 0.6:
        b += 1
    return a - 6, b + 6


def _trim_outer(frac, lo, hi):
    while lo < hi and frac[lo] > 0.6:
        lo += 1
    while hi > lo and frac[hi - 1] > 0.6:
        hi -= 1
    return lo, hi


def split(path, out_size=(1920, 1080)):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    Hh, Ww = a.shape[:2]
    rows, cols = _white_frac(a, 1), _white_frac(a, 0)
    r0, r1 = _gutter(rows, Hh)
    c0, c1 = _gutter(cols, Ww)
    boxes = {"TL": [0, 0, c0, r0], "TR": [c1, 0, Ww, r0], "BL": [0, r1, c0, Hh], "BR": [c1, r1, Ww, Hh]}
    out = {}
    for k, (x0, y0, x1, y1) in boxes.items():
        sub = a[y0:y1, x0:x1]
        ry0, ry1 = _trim_outer(_white_frac(sub, 1), 0, sub.shape[0])
        rx0, rx1 = _trim_outer(_white_frac(sub, 0), 0, sub.shape[1])
        x0, y0, x1, y1 = x0 + rx0 + 2, y0 + ry0 + 2, x0 + rx1 - 2, y0 + ry1 - 2  # 2 px contra antialias
        w, h = x1 - x0, y1 - y0
        if w / h > 16 / 9:
            nw = int(h * 16 / 9); x0 += (w - nw) // 2; w = nw
        else:
            nh = int(w * 9 / 16); y0 += (h - nh) // 2; h = nh
        tile = im.crop((x0, y0, x0 + w, y0 + h)).resize(out_size, Image.LANCZOS)
        out[k] = (tile, [x0, y0, w, h])
    return out, {"rows": [r0, r1], "cols": [c0, c1]}
