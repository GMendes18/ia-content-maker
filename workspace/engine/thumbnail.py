#!/usr/bin/env python3
"""thumbnail.py — thumbnail 1280x720 no layout sorteado, a partir dos plates e sprites do vídeo.
Regras: mesmos personagens, iluminação mais saturada, emoções extremas, quarto superior livre, SEM texto.

Layout implementado: "before and after split" (os outros entram quando forem sorteados).
Uso: thumbnail.py videos/<nome> thumb.json
thumb.json: {"before": {"plate": "...", "char": "frank", "sprite": "frank_pose_pockets", "focus": [x, y]},
             "after":  {"plate": "...", "char": "frank", "pose": "cheer", "prop": "card", "focus": [x, y]}}
"""
import json, math, pathlib, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[1]
W, H = 1280, 720


def plate_crop(vd, name, focus, zoom=1.25):
    for p in (vd / "art" / f"{name}.png", vd / "tiles" / f"{name}.png"):
        if p.exists():
            im = Image.open(p).convert("RGB"); break
    sx = im.width / 1920
    cw, ch = 1920 / zoom * sx, 1080 / zoom * sx
    cx = min(max(focus[0] * sx, cw / 2), im.width - cw / 2); cy = min(max(focus[1] * sx, ch / 2), im.height - ch / 2)
    return im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.LANCZOS)


def puppet_still(sp_dir, rig, pose, emotion="neutral"):
    """Desenha o boneco frontal com braços num PNG (mesmas regras do rig: manga até o cotovelo, pele no antebraço)."""
    body = Image.open(sp_dir / rig["body"]).convert("RGBA")
    head = Image.open(sp_dir / rig["heads"].get(emotion, rig["heads"]["neutral"])).convert("RGBA")
    pad = 400
    im = Image.new("RGBA", (body.width + 2 * pad, body.height + pad), (0, 0, 0, 0))
    im.alpha_composite(body, (pad, pad)); im.alpha_composite(head, (pad, pad))
    d = ImageDraw.Draw(im)
    Hs = rig["size"][1]; dna = json.loads((ROOT / "dna.json").read_text())
    L1, L2, th = dna["ranges"]["arm"]["L1"] * Hs, dna["ranges"]["arm"]["L2"] * Hs, dna["ranges"]["arm"]["thickness"] * Hs
    targets = {"cheer": [(-0.55, -0.75), (0.55, -0.75)], "up": [(-0.32, -0.9), (0.32, -0.9)],
               "point_r": [(0.1, 0.9), (0.9, -0.25)], "point_l": [(-0.9, -0.25), (-0.1, 0.9)]}[pose]
    hands = []
    for side, (tx, ty) in zip(("l", "r"), targets):
        sx, sy = rig["sockets"][side]; sx += pad; sy += pad
        Lt = L1 + L2; hx, hy = sx + tx * Lt, sy + ty * Lt
        dist = min(math.hypot(hx - sx, hy - sy), (L1 + L2) * 0.999)
        base = math.atan2(hy - sy, hx - sx); off = math.acos(max(-1, min(1, (L1 ** 2 + dist ** 2 - L2 ** 2) / (2 * L1 * dist))))
        out = -1 if side == "l" else 1
        cands = [(sx + L1 * math.cos(base + s * off), sy + L1 * math.sin(base + s * off)) for s in (1, -1)]
        ex, ey = max(cands, key=lambda e: e[1] + 0.6 * out * (e[0] - sx))
        hx, hy = sx + dist * math.cos(base), sy + dist * math.sin(base)
        for (a, b, col, w) in (((sx, sy), (ex, ey), tuple(rig["sleeve"]), th), ((ex, ey), (hx, hy), tuple(rig["skin"]), th * 0.9)):
            d.line([a, b], fill=col, width=int(w))
            for p in (a, b):
                d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)
        r = th * 0.78
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=tuple(rig["skin"]))
        hands.append((hx, hy))
    return im, hands, pad


def shadow(canvas, x, y, w):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x - w / 2, y - w * 0.09, x + w / 2, y + w * 0.09], fill=(0, 0, 0, 70))
    canvas.alpha_composite(sh)


def main(vd, cfg_path):
    vd = pathlib.Path(vd); cfg = json.loads(pathlib.Path(cfg_path).read_text())
    sp = vd / "sprites"; rig = json.loads((sp / "rig.json").read_text())
    dna = json.loads((ROOT / "dna.json").read_text()); C = dna["code_colours"]
    b, a = cfg["before"], cfg["after"]
    left = plate_crop(vd, b["plate"], b["focus"]).convert("RGBA")
    right = plate_crop(vd, a["plate"], a["focus"]).convert("RGBA")
    # antes: frio e mais escuro; depois: quente e saturado
    left = ImageEnhance.Brightness(ImageEnhance.Color(left.convert("RGB")).enhance(0.85)).enhance(0.78).convert("RGBA")
    right = ImageEnhance.Color(ImageEnhance.Brightness(right.convert("RGB")).enhance(1.08)).enhance(1.35).convert("RGBA")
    canvas = Image.new("RGBA", (W, H))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (W * 0.54, 0), (W * 0.46, H), (0, H)], fill=255)
    canvas.paste(right, (0, 0)); canvas.paste(left, (0, 0), mask)
    # personagem "antes": sprite inteiro em choque
    fb = Image.open(sp / f"{b['sprite']}.png").convert("RGBA")
    hb = 470; fb = fb.resize((int(fb.width * hb / fb.height), hb), Image.LANCZOS)
    shadow(canvas, 300, 705, 300); canvas.alpha_composite(fb, (300 - fb.width // 2, 705 - hb))
    # personagem "depois": boneco com braços em comemoração + cartão erguido
    fa, hands, pad = puppet_still(sp, rig[a["char"]], a.get("pose", "cheer"))
    k = 470 / rig[a["char"]]["size"][1]
    fa = fa.resize((int(fa.width * k), int(fa.height * k)), Image.LANCZOS)
    ax = 960 - fa.width // 2; ay = 705 - int((rig[a["char"]]["size"][1] + pad) * k)
    shadow(canvas, 960, 705, 300); canvas.alpha_composite(fa, (ax, ay))
    if a.get("prop") == "card":
        hx, hy = hands[1][0] * k + ax, hands[1][1] * k + ay
        card = Image.new("RGBA", (240, 156), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
        dc.rounded_rectangle([0, 0, 239, 155], 16, fill=(210, 176, 140)); dc.rounded_rectangle([24, 44, 84, 84], 8, fill=C["highlight"])
        dc.rectangle([24, 108, 190, 120], fill=C["alert"])
        card = card.rotate(14, expand=True, resample=Image.BICUBIC)
        canvas.alpha_composite(card, (int(hx - 40), int(hy - card.height + 30)))
    # faixa divisória no destaque do episódio
    div = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(div).line([(W * 0.54, -10), (W * 0.46, H + 10)], fill=cfg.get("divider", C["headline_a"]), width=18)
    canvas.alpha_composite(div)
    out = vd / "thumbnail.png"
    canvas.convert("RGB").save(out, quality=95)
    print("thumbnail:", out)


def faceoff(vd, cfg):
    """Layout "two characters facing off", capa VERTICAL 1080x1920: dois cenários em diagonal, os dois
    personagens apontando um para o outro com emoção extrema; quarto superior livre; sem texto."""
    vd = pathlib.Path(vd); sp = vd / "sprites"; rig = json.loads((sp / "rig.json").read_text())
    dna = json.loads((ROOT / "dna.json").read_text()); C = dna["code_colours"]
    CW, CH = 1080, 1920
    def bg(name, focus):
        for p in (vd / "art" / f"{name}.png", vd / "tiles" / f"{name}.png"):
            if p.exists():
                im = Image.open(p).convert("RGB"); break
        k = CH / im.height; im = im.resize((int(im.width * k), CH), Image.LANCZOS)
        x = int(min(max(focus * im.width / 1920 - CW / 2, 0), im.width - CW)); return im.crop((x, 0, x + CW, CH))  # focus em coordenadas do mundo
    L, R = cfg["left"], cfg["right"]
    left = ImageEnhance.Color(bg(L["plate"], L["focus"])).enhance(1.3).convert("RGBA")
    right = ImageEnhance.Color(bg(R["plate"], R["focus"])).enhance(1.3).convert("RGBA")
    canvas = right.copy(); mask = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (CW * 0.62, 0), (CW * 0.38, CH), (0, CH)], fill=255)
    canvas.paste(left, (0, 0), mask)
    for side, c, x in (("l", L, 270), ("r", R, 810)):
        fig, hands, pad = puppet_still(sp, rig[c["char"]], "point_r" if side == "l" else "point_l", "shocked")
        k = 760 / rig[c["char"]]["size"][1]
        fig = fig.resize((int(fig.width * k), int(fig.height * k)), Image.LANCZOS)
        shadow(canvas, x, 1800, 420)
        canvas.alpha_composite(fig, (x - fig.width // 2, 1800 - int((rig[c["char"]]["size"][1] + pad) * k)))
    div = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ImageDraw.Draw(div).line([(CW * 0.62, -10), (CW * 0.38, CH + 10)], fill=cfg.get("divider", C["headline_a"]), width=22)
    canvas.alpha_composite(div)
    out = vd / "capa_vertical.png"; canvas.convert("RGB").save(out); print("capa:", out)


if __name__ == "__main__":
    cfg = json.loads(pathlib.Path(sys.argv[2]).read_text())
    faceoff(sys.argv[1], cfg) if cfg.get("layout") == "faceoff" else main(sys.argv[1], sys.argv[2])
