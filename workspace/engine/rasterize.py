#!/usr/bin/env python3
"""rasterize.py — SVG → PNG pelo Chromium do Playwright (sem cairo).
Uso: rasterize.py entrada.svg saida.png [--scale 2]
Também importável: rasterize_many([(svg_str, out_path, scale), ...])
"""
import argparse, pathlib, re
from playwright.sync_api import sync_playwright


def _size(svg):
    m = re.search(r'width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"', svg)
    return int(float(m.group(1))), int(float(m.group(2)))


def rasterize_many(jobs):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for svg, out, scale in jobs:
            w, h = _size(svg)
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
            pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.close()
        b.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("svg"); ap.add_argument("png"); ap.add_argument("--scale", type=float, default=1)
    a = ap.parse_args()
    rasterize_many([(pathlib.Path(a.svg).read_text(), a.png, a.scale)])
