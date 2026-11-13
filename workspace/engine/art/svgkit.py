"""svgkit.py — helpers de SVG chapado (sem contorno, sem gradiente) que leem o dna.json."""
import colorsys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DNA = json.loads((ROOT / "dna.json").read_text())
C = DNA["code_colours"]
PAL = {c["name"]: c["hex"] for c in DNA["palette"]["colors"]}


def _hls(hexc):
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def _roles(cols):
    """Papéis das 5 cores de QUALQUER paleta (white label): os desenhos usam o papel, nunca o nome.
    coal = a mais escura (tinta, noite); ice/stone = as DUAS mais claras (céu, paredes; stone = a menos
    saturada delas); das 2 que sobram: berry = a mais saturada (destaque), pine = a outra (painéis, lambri)."""
    cs = list(cols)
    coal = min(cs, key=lambda c: _hls(c)[1]); cs.remove(coal)
    lights = sorted(cs, key=lambda c: -_hls(c)[1])[:2]
    stone = min(lights, key=lambda c: _hls(c)[2]); ice = [c for c in lights if c != stone][0]
    rest = [c for c in cs if c not in lights]
    berry = max(rest, key=lambda c: _hls(c)[2]); pine = [c for c in rest if c != berry][0]
    return {"ice": ice, "stone": stone, "pine": pine, "coal": coal, "berry": berry}


ROLE = _roles(PAL.values())
KEY = DNA["chroma_key"]["hex"]


def shade(hexc, k=0.86):
    """A única sombra permitida: a mesma cor, um pouco mais escura."""
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(hh, max(0, l * k), s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def tint(hexc, k=1.12):
    return shade(hexc, k)


def mix(a, b, p):
    a = [int(a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * p) for x, y in zip(a, b))


def rect(x, y, w, h, fill, rx=0, extra=""):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" {extra}/>'


def circle(cx, cy, r, fill, extra=""):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" {extra}/>'


def ellipse(cx, cy, rx, ry, fill, extra=""):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" {extra}/>'


def path(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def poly(pts, fill, extra=""):
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{s}" fill="{fill}" {extra}/>'


def g(inner, transform=""):
    t = f' transform="{transform}"' if transform else ""
    return f"<g{t}>{''.join(inner) if isinstance(inner, list) else inner}</g>"


def svg(w, h, body, bg=None):
    b = rect(0, 0, w, h, bg) if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'shape-rendering="geometricPrecision">{b}{"".join(body) if isinstance(body, list) else body}</svg>')
