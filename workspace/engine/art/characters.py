"""characters.py — sheets de personagem em SVG no build do DNA (chunky rounded-square heads,
stubby legs, wide shoulders), sobre fundo chroma. Cada personagem é um dict fixo (CHAR_SPEC),
o equivalente em código da "descrição colada palavra por palavra" do prompt de arte.

Views do base sheet: front_neutral (SEM braços), front_alt (SEM braços, 2ª emoção),
side_walk, back, pose_a, pose_b.
"""
from svgkit import C, KEY, circle, ellipse, g, path, poly, rect, shade, svg

INK = C["ink"]


def _head(sp, cx, gy, u, emotion="neutral"):
    """Cabeça quadrada arredondada + rosto. Coordenadas: gy = chão, u = altura/100."""
    skin, sk2 = sp["skin"], shade(sp["skin"], 0.88)
    o = []
    # orelhas (atrás da cabeça)
    o.append(rect(cx - 21 * u, gy - 76 * u, 5 * u, 8 * u, sk2, rx=2.5 * u))
    o.append(rect(cx + 16 * u, gy - 76 * u, 5 * u, 8 * u, sk2, rx=2.5 * u))
    # cabeça
    o.append(rect(cx - 18 * u, gy - 88 * u, 36 * u, 33 * u, skin, rx=9 * u))
    # sombra única: faixa inferior da mandíbula, recortada pela forma da cabeça
    cid = f"hc{int(cx)}{int(gy)}{emotion}"
    o.append(f'<clipPath id="{cid}">' + rect(cx - 18 * u, gy - 88 * u, 36 * u, 33 * u, "#000", rx=9 * u) + '</clipPath>')
    o.append(rect(cx - 18 * u, gy - 64 * u, 36 * u, 10 * u, sk2, extra=f'clip-path="url(#{cid})"'))
    # costeletas
    hair = sp["hair"]
    o.append(rect(cx - 18 * u, gy - 84 * u, 4 * u, 11 * u, hair, rx=1.5 * u))
    o.append(rect(cx + 14 * u, gy - 84 * u, 4 * u, 11 * u, hair, rx=1.5 * u))
    ey = gy - 71 * u
    if emotion == "neutral":
        for sx in (-1, 1):
            o.append(ellipse(cx + sx * 7.5 * u, ey, 2.0 * u, 2.5 * u, INK))
            o.append(rect(cx + sx * 7.5 * u - 3.2 * u, gy - 78.5 * u, 6.4 * u, 1.7 * u, hair, rx=0.85 * u))
        # boca: sorriso leve preenchido
        o.append(path(f"M{cx-4.5*u:.1f},{gy-62.5*u:.1f} Q{cx:.1f},{gy-58.2*u:.1f} {cx+4.5*u:.1f},{gy-62.5*u:.1f} "
                      f"Q{cx:.1f},{gy-60.6*u:.1f} {cx-4.5*u:.1f},{gy-62.5*u:.1f} Z", INK))
    elif emotion == "shocked":
        for sx in (-1, 1):
            o.append(ellipse(cx + sx * 7.5 * u, ey, 2.4 * u, 3.0 * u, INK))
            o.append(rect(cx + sx * 7.5 * u - 3.0 * u, gy - 81.5 * u, 6.0 * u, 1.7 * u, hair, rx=0.85 * u,
                          extra=f'transform="rotate({-sx*10} {cx+sx*7.5*u:.1f} {gy-80.6*u:.1f})"'))
        o.append(ellipse(cx, gy - 60.5 * u, 3.0 * u, 3.6 * u, INK))
        o.append(ellipse(cx, gy - 58.6 * u, 1.9 * u, 1.3 * u, C["alert"]))
    # nariz
    o.append(rect(cx - 2.2 * u, gy - 70 * u, 4.4 * u, 5.5 * u, sk2, rx=2.2 * u))
    if sp.get("mustache"):
        o.append(path(f"M{cx-6*u:.1f},{gy-64.6*u:.1f} Q{cx:.1f},{gy-67.5*u:.1f} {cx+6*u:.1f},{gy-64.6*u:.1f} "
                      f"Q{cx+3*u:.1f},{gy-63*u:.1f} {cx:.1f},{gy-64*u:.1f} Q{cx-3*u:.1f},{gy-63*u:.1f} {cx-6*u:.1f},{gy-64.6*u:.1f} Z", sp["hair"]))
    if sp.get("glasses"):
        for sx in (-1, 1):
            o.append(rect(cx + sx * 7.5 * u - 4.4 * u, ey - 3.8 * u, 8.8 * u, 7.6 * u, "#ffffff", rx=2.5 * u, extra='opacity="0.28"'))
        o.append(rect(cx - 3.2 * u, ey - 2.6 * u, 6.4 * u, 1.1 * u, shade(sp["hair"], 1.0), rx=0.5 * u))
    return o


def _hat(sp, cx, gy, u, back=False):
    if not sp.get("hat"):  # sem chapéu: bloco de cabelo no topo (risca de lado opcional)
        hair = sp["hair"]
        o = [rect(cx - 19 * u, gy - 93 * u, 38 * u, 14 * u, hair, rx=7 * u)]
        if not back:
            o.append(rect(cx + 2 * u, gy - 93 * u, 3 * u, 6 * u, shade(hair, 0.8), rx=1.5 * u))
            o.append(rect(cx - 19 * u, gy - 84 * u, 5 * u, 9 * u, hair, rx=2 * u))
            o.append(rect(cx + 14 * u, gy - 84 * u, 5 * u, 9 * u, hair, rx=2 * u))
        else:
            o.append(rect(cx - 18 * u, gy - 86 * u, 36 * u, 16 * u, hair, rx=6 * u))
        return o
    hat, band = sp["hat"], sp["hat_band"]
    o = [rect(cx - 15 * u, gy - 98 * u, 30 * u, 14 * u, hat, rx=5 * u),
         rect(cx - 15 * u, gy - 90 * u, 30 * u, 3.4 * u, band),
         rect(cx - 6 * u, gy - 98 * u, 12 * u, 2.6 * u, shade(hat, 0.8), rx=1.3 * u),  # amassado da copa
         rect(cx - 24 * u, gy - 87 * u, 48 * u, 4.2 * u, hat, rx=2.1 * u)]
    return o


def _legs(sp, cx, gy, u):
    tr, sh = sp["trousers"], sp["shoes"]
    return [rect(cx - 14 * u, gy - 17 * u, 10 * u, 14 * u, tr, rx=2 * u),
            rect(cx + 4 * u, gy - 17 * u, 10 * u, 14 * u, shade(tr, 0.9), rx=2 * u),
            rect(cx - 18 * u, gy - 5 * u, 15 * u, 5 * u, sh, rx=2.5 * u),
            rect(cx + 3 * u, gy - 5 * u, 15 * u, 5 * u, sh, rx=2.5 * u)]


def _torso(sp, cx, gy, u, back=False):
    j, j2 = sp["jacket"], shade(sp["jacket"], 0.82)
    y0, y1 = gy - 52 * u, gy - 14 * u
    d = (f"M{cx-16*u:.1f},{y0:.1f} L{cx+16*u:.1f},{y0:.1f} Q{cx+23*u:.1f},{y0:.1f} {cx+23*u:.1f},{y0+7*u:.1f} "
         f"L{cx+17*u:.1f},{y1-3*u:.1f} Q{cx+17*u:.1f},{y1:.1f} {cx+14*u:.1f},{y1:.1f} L{cx-14*u:.1f},{y1:.1f} "
         f"Q{cx-17*u:.1f},{y1:.1f} {cx-17*u:.1f},{y1-3*u:.1f} L{cx-23*u:.1f},{y0+7*u:.1f} "
         f"Q{cx-23*u:.1f},{y0:.1f} {cx-16*u:.1f},{y0:.1f} Z")
    o = [rect(cx - 5 * u, gy - 58 * u, 10 * u, 8 * u, shade(sp["skin"], 0.86)),  # pescoço
         path(d, j)]
    # sombra única: lado direito do paletó
    o.append(path(f"M{cx+15*u:.1f},{y0:.1f} L{cx+16*u:.1f},{y0:.1f} Q{cx+23*u:.1f},{y0:.1f} {cx+23*u:.1f},{y0+7*u:.1f} "
                  f"L{cx+17*u:.1f},{y1-3*u:.1f} Q{cx+17*u:.1f},{y1:.1f} {cx+14*u:.1f},{y1:.1f} L{cx+11*u:.1f},{y1:.1f} Z", j2))
    if back:
        o.append(rect(cx - 0.8 * u, y0 + 10 * u, 1.6 * u, 28 * u, j2))
        o.append(rect(cx - 6 * u, y0 - 1 * u, 12 * u, 4 * u, sp["shirt"], rx=1.5 * u))  # gola
        return o
    sh, tie = sp["shirt"], sp["tie"]
    o.append(poly([(cx - 6.5 * u, y0), (cx + 6.5 * u, y0), (cx, y0 + 17 * u)], sh))
    if sp.get("neckwear", "tie") == "none":  # camisa de trabalho, sem gravata
        pass
    elif sp.get("neckwear", "tie") == "bow":
        o.append(poly([(cx, y0 + 2 * u), (cx - 6 * u, y0 - 0.5 * u), (cx - 6 * u, y0 + 4.5 * u)], tie))
        o.append(poly([(cx, y0 + 2 * u), (cx + 6 * u, y0 - 0.5 * u), (cx + 6 * u, y0 + 4.5 * u)], tie))
        o.append(rect(cx - 1.6 * u, y0 + 0.4 * u, 3.2 * u, 3.2 * u, shade(tie, 0.85), rx=1 * u))
    else:
        o.append(poly([(cx - 1.6 * u, y0 + 2.6 * u), (cx + 1.6 * u, y0 + 2.6 * u), (cx + 2.4 * u, y0 + 13 * u),
                       (cx, y0 + 16 * u), (cx - 2.4 * u, y0 + 13 * u)], tie))
        o.append(rect(cx - 2.2 * u, y0 - 0.2 * u, 4.4 * u, 3.2 * u, shade(tie, 0.85), rx=1 * u))
    o.append(poly([(cx - 6.5 * u, y0), (cx - 11 * u, y0), (cx - 2 * u, y0 + 21 * u), (cx, y0 + 17 * u)], j2))
    o.append(poly([(cx + 6.5 * u, y0), (cx + 11 * u, y0), (cx + 2 * u, y0 + 21 * u), (cx, y0 + 17 * u)], j2))
    o.append(circle(cx, y0 + 24 * u, 1.3 * u, j2))
    o.append(circle(cx, y0 + 31 * u, 1.3 * u, j2))
    o.append(rect(cx - 15 * u, y0 + 26 * u, 8 * u, 1.6 * u, j2, rx=0.8 * u))  # bolso
    return o


def _arm(x0, y0, x1, y1, x2, y2, sleeve, skin, u, t=3.6):
    """Braço inteiro para sprites inteiros (side/back/poses): mesmas regras do rig."""
    w = t * u
    return [f'<path d="M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f}" stroke="{sleeve}" stroke-width="{w:.1f}" stroke-linecap="round" fill="none"/>',
            f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke="{skin}" stroke-width="{w*0.92:.1f}" stroke-linecap="round" fill="none"/>',
            circle(x2, y2, w * 0.72, skin)]


def front(sp, cx, gy, H, emotion="neutral"):
    u = H / 100
    return g(_legs(sp, cx, gy, u) + _torso(sp, cx, gy, u) + _head(sp, cx, gy, u, emotion) + _hat(sp, cx, gy, u))


def back(sp, cx, gy, H):
    u = H / 100
    o = _legs(sp, cx, gy, u)
    j = sp["jacket"]
    o += _arm(cx - 18 * u, gy - 46 * u, cx - 21 * u, gy - 34 * u, cx - 20 * u, gy - 22 * u, shade(j, 0.95), sp["skin"], u)
    o += _arm(cx + 18 * u, gy - 46 * u, cx + 21 * u, gy - 34 * u, cx + 20 * u, gy - 22 * u, shade(j, 0.95), sp["skin"], u)
    o += _torso(sp, cx, gy, u, back=True)
    sk2 = shade(sp["skin"], 0.88)
    o += [rect(cx - 21 * u, gy - 76 * u, 5 * u, 8 * u, sk2, rx=2.5 * u), rect(cx + 16 * u, gy - 76 * u, 5 * u, 8 * u, sk2, rx=2.5 * u),
          rect(cx - 18 * u, gy - 88 * u, 36 * u, 33 * u, sp["skin"], rx=9 * u),
          rect(cx - 18 * u, gy - 86 * u, 36 * u, 14 * u, sp["hair"], rx=6 * u)]
    o += _hat(sp, cx, gy, u, back=True)
    return g(o)


def side_walk(sp, cx, gy, H):
    """Perfil andando para a direita, braço de trás escondido, braço da frente balançando."""
    u = H / 100
    tr, shoes, j = sp["trousers"], sp["shoes"], sp["jacket"]
    o = []
    hip = (cx, gy - 16 * u)
    for ang, col in ((24, shade(tr, 0.88)), (-22, tr)):
        o.append(g([rect(-5 * u, 0, 10 * u, 14 * u, col, rx=2 * u),
                    rect(-5 * u, 11 * u, 15 * u, 5 * u, shoes, rx=2.5 * u)],
                   f"translate({hip[0]:.1f},{hip[1]:.1f}) rotate({ang})"))
    y0, y1 = gy - 52 * u, gy - 14 * u
    o.append(rect(cx - 13 * u, y0, 27 * u, y1 - y0, j, rx=7 * u))
    o.append(rect(cx - 13 * u, y0 + 6 * u, 6 * u, y1 - y0 - 8 * u, shade(j, 0.82), rx=3 * u))
    o.append(poly([(cx + 7 * u, y0 + 1 * u), (cx + 12.5 * u, y0 + 3 * u), (cx + 12 * u, y0 + 11 * u)], sp["shirt"]))
    o.append(poly([(cx + 11 * u, y0 + 4 * u), (cx + 13 * u, y0 + 5 * u), (cx + 12 * u, y0 + 14 * u)], sp["tie"]))
    o.append(rect(cx - 4 * u, gy - 58 * u, 9 * u, 8 * u, shade(sp["skin"], 0.86)))
    # cabeça de perfil
    sk, sk2 = sp["skin"], shade(sp["skin"], 0.88)
    o.append(rect(cx - 15 * u, gy - 88 * u, 32 * u, 33 * u, sk, rx=9 * u))
    o.append(rect(cx + 15 * u, gy - 73 * u, 4.5 * u, 6 * u, sk2, rx=2.2 * u))  # nariz
    o.append(rect(cx - 8 * u, gy - 76 * u, 5 * u, 8 * u, sk2, rx=2.5 * u))  # orelha
    o.append(rect(cx - 15 * u, gy - 86 * u, 9 * u, 14 * u, sp["hair"], rx=4 * u))
    o.append(ellipse(cx + 9 * u, gy - 71 * u, 1.8 * u, 2.4 * u, INK))
    o.append(rect(cx + 6 * u, gy - 78 * u, 6 * u, 1.6 * u, sp["hair"], rx=0.8 * u))
    o.append(path(f"M{cx+7*u:.1f},{gy-62*u:.1f} Q{cx+11*u:.1f},{gy-59*u:.1f} {cx+14*u:.1f},{gy-62.5*u:.1f} Z", INK))
    if sp.get("hat"):
        o += [rect(cx - 13 * u, gy - 98 * u, 28 * u, 14 * u, sp["hat"], rx=5 * u),
              rect(cx - 13 * u, gy - 90 * u, 28 * u, 3.4 * u, sp["hat_band"]),
              rect(cx - 20 * u, gy - 87 * u, 44 * u, 4.2 * u, sp["hat"], rx=2.1 * u)]
    else:
        o += [rect(cx - 16 * u, gy - 93 * u, 34 * u, 13 * u, sp["hair"], rx=6.5 * u)]
        if sp.get("mustache"):
            o.append(rect(cx + 10 * u, gy - 65.5 * u, 8 * u, 2.6 * u, sp["hair"], rx=1.3 * u))
    # braço da frente balançando para trás
    o += _arm(cx + 1 * u, gy - 47 * u, cx - 5 * u, gy - 36 * u, cx - 3 * u, gy - 25 * u, j, sp["skin"], u)
    return g(o)


def pose_pockets(sp, cx, gy, H):
    """Pose 5: apalpando os bolsos, em choque (procurando a carteira)."""
    u = H / 100
    j = sp["jacket"]
    o = [front(sp, cx, gy, H, "shocked")]
    o += _arm(cx - 17 * u, gy - 45 * u, cx - 25 * u, gy - 33 * u, cx - 15 * u, gy - 24 * u, j, sp["skin"], u)
    o += _arm(cx + 17 * u, gy - 45 * u, cx + 25 * u, gy - 33 * u, cx + 15 * u, gy - 24 * u, j, sp["skin"], u)
    return g(o)


def pose_sitting(sp, cx, gy, H):
    """Pose 6: sentado de frente numa cadeira, mãos no colo."""
    u = H / 100
    j, tr, chair = sp["jacket"], sp["trousers"], sp.get("chair", "#6b2335")
    drop = 9 * u  # o corpo inteiro desce: coxas vistas de frente ficam escondidas
    gyb = gy + drop
    o = [rect(cx - 22 * u, gy - 62 * u, 44 * u, 50 * u, chair, rx=6 * u),          # encosto atrás do tronco
         rect(cx - 21 * u, gy - 4 * u, 5 * u, 4 * u, shade(chair, .8)), rect(cx + 16 * u, gy - 4 * u, 5 * u, 4 * u, shade(chair, .8)),
         rect(cx - 24 * u, gy - 17 * u, 48 * u, 6 * u, shade(chair, .85), rx=3 * u),  # assento
         rect(cx - 22 * u, gy - 12 * u, 5 * u, 12 * u, shade(chair, .8)), rect(cx + 17 * u, gy - 12 * u, 5 * u, 12 * u, shade(chair, .8)),
         rect(cx - 14 * u, gy - 11 * u, 10 * u, 8 * u, tr, rx=2 * u), rect(cx + 4 * u, gy - 11 * u, 10 * u, 8 * u, shade(tr, .9), rx=2 * u),
         rect(cx - 18 * u, gy - 5 * u, 15 * u, 5 * u, sp["shoes"], rx=2.5 * u), rect(cx + 3 * u, gy - 5 * u, 15 * u, 5 * u, sp["shoes"], rx=2.5 * u)]
    o += _torso(sp, cx, gyb, u) + _head(sp, cx, gyb, u) + _hat(sp, cx, gyb, u)
    o.append(rect(cx - 16 * u, gyb - 20 * u, 32 * u, 9 * u, tr, rx=4 * u))  # coxas em escorço
    o += _arm(cx - 17 * u, gyb - 45 * u, cx - 21 * u, gyb - 33 * u, cx - 7 * u, gyb - 19 * u, j, sp["skin"], u)
    o += _arm(cx + 17 * u, gyb - 45 * u, cx + 21 * u, gyb - 33 * u, cx + 7 * u, gyb - 19 * u, j, sp["skin"], u)
    return g(o)


VIEWS = ["front_neutral", "front_alt", "side_walk", "back", "pose_a", "pose_b"]


def base_sheet(sp, cell=700, H=1150):
    """6 views numa linha, com muito espaço de chroma entre elas."""
    W, Hs = cell * 6, int(H * 1.3)
    gy = Hs - 80
    body = [front(sp, cell * 0.5, gy, H, "neutral"),
            front(sp, cell * 1.5, gy, H, sp.get("alt_emotion", "shocked")),
            side_walk(sp, cell * 2.5, gy, H),
            back(sp, cell * 3.5, gy, H),
            pose_pockets(sp, cell * 4.5, gy, H),
            pose_sitting(sp, cell * 5.5, gy, H)]
    return svg(W, Hs, body, bg=KEY)
