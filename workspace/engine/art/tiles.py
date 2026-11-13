"""tiles.py — os lugares que viram tiles de quad (close-ups de objetos são ótimos tiles).
Cada função devolve (corpo_svg_em_1920x1080, meta). O meta usa coordenadas desse espaço 1920x1080;
make_art converte para o tile final depois do split.
VAZIOS: sem pessoas. Blanks em branco para o código escrever.
"""
from svgkit import C, PAL, ROLE, circle, ellipse, g, mix, path, poly, rect, shade

W, H = 1920, 1080
stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"], ROLE["coal"], ROLE["berry"])
hl, warm = C["highlight"], C["warm"]
wood = mix(berry, coal, 0.55)
paper = mix(C["card"], hl, 0.08)
kraft = mix(stone, warm, 0.35)


def card_closeup():
    """Close no tampo da mesa do restaurante: o cartãozinho de papelão ao lado da xícara."""
    o = [rect(0, 0, W, H, mix(wood, warm, 0.15))]
    for y in range(60, H, 170):
        o.append(rect(0, y, W, 10, shade(mix(wood, warm, 0.15), 0.9)))
    o += [ellipse(1500, 330, 260, 210, "#ffffff"), ellipse(1500, 330, 170, 136, shade(paper, 0.93)),
          ellipse(1500, 320, 120, 96, mix(coal, warm, 0.35))]  # xícara vista de cima
    o += [rect(1730, 300, 120, 50, "#ffffff", rx=25)]
    # cartão (blank) levemente girado
    o.append(g([rect(-330, -200, 660, 400, shade(kraft, 0.8), rx=26),
                rect(-340, -212, 660, 400, kraft, rx=26),
                rect(-300, -170, 240, 64, shade(kraft, 0.9), rx=10)], "translate(840,560) rotate(-6)"))
    for i, (x, y) in enumerate([(300, 880), (380, 930), (250, 960)]):
        o += [circle(x, y, 46, shade(hl, 0.85)), circle(x, y, 34, hl)]
    meta = {"blanks": {"card_face": [560, 400, 560, 300]}, "anchors": {"card": [830, 560], "cup": [1500, 320]},
            "portals": {"card": [500, 360, 680, 400]}, "floor_y": 1000, "light": "warm indoor lamps"}
    return o, meta


def dresser_wallet():
    """Quarto à noite, close na cômoda: a carteira esquecida em cima dela."""
    wall = mix(ice, coal, 0.35)
    o = [rect(0, 0, W, H, wall), rect(0, 760, W, 320, shade(wall, 0.75))]
    o += [rect(1280, 120, 460, 420, shade(wall, 0.8), rx=8), rect(1300, 140, 420, 380, mix(coal, ice, 0.12)),
          circle(1600, 230, 40, mix(ice, "#ffffff", 0.5))]  # janela com lua
    o += [rect(300, 520, 1100, 60, wood, rx=12), rect(330, 580, 1040, 420, shade(wood, 0.9), rx=8)]
    for i in range(3):
        y = 610 + i * 130
        o += [rect(370, y, 960, 110, wood, rx=8), rect(810, y + 45, 80, 18, hl, rx=9)]
    # abajur e poça de luz
    o += [circle(470, 330, 260, hl, 'opacity="0.10"'), circle(470, 330, 150, hl, 'opacity="0.12"'),
          rect(455, 360, 30, 160, coal), poly([(380, 370), (560, 370), (520, 250), (420, 250)], berry), ellipse(470, 520, 90, 14, coal)]
    # carteira
    o += [rect(820, 455, 330, 80, shade(coal, 1.25), rx=16), rect(820, 455, 330, 30, shade(coal, 1.45), rx=14),
          rect(1080, 470, 50, 20, shade(coal, 1.7), rx=8)]
    meta = {"blanks": {}, "anchors": {"wallet": [985, 490], "lamp": [470, 330]},
            "portals": {"window": [1300, 140, 420, 380]}, "floor_y": 1000, "light": "cold night with a warm lamp"}
    return o, meta


def telephone():
    """Telefone de parede do restaurante, close, com bloco de recados em branco."""
    o = [rect(0, 0, W, 640, mix(stone, warm, 0.10)), rect(0, 640, W, 440, pine), rect(0, 628, W, 24, shade(pine, 0.8))]
    o += [rect(760, 120, 400, 640, wood, rx=40), rect(800, 170, 320, 140, shade(wood, 0.8), rx=30),
          circle(960, 420, 110, coal), circle(960, 420, 70, shade(coal, 1.3)),
          rect(1180, 150, 70, 300, coal, rx=35), rect(1165, 140, 100, 70, coal, rx=30), rect(1165, 400, 100, 70, coal, rx=30)]
    o += [path("M1215,470 C1240,560 1180,600 1215,690 C1250,780 1190,800 1215,870", "none",
               f'stroke="{coal}" stroke-width="14" fill="none" stroke-linecap="round"')]
    o += [rect(300, 200, 330, 420, paper, rx=6), rect(300, 200, 330, 50, berry, rx=6), circle(465, 190, 14, C["alert"])]
    meta = {"blanks": {"notepad": [320, 270, 290, 330]}, "anchors": {"phone": [960, 420], "handset": [1215, 300]},
            "portals": {"dial": [850, 310, 220, 220]}, "floor_y": 1040, "light": "warm indoor lamps"}
    return o, meta


def calendar():
    """Calendário de parede, folha em branco com grade de dias vazia."""
    o = [rect(0, 0, W, H, mix(stone, ice, 0.3))]
    o += [rect(520, 70, 880, 960, shade(paper, 0.9), rx=14), rect(500, 50, 880, 960, paper, rx=14),
          rect(500, 50, 880, 170, berry, rx=14), rect(500, 190, 880, 30, berry)]
    for k in (640, 1240):
        o.append(rect(k - 12, 20, 24, 70, coal, rx=12))
    x0, y0, cw, ch = 540, 260, 114, 140
    for r in range(5):
        for c in range(7):
            o.append(rect(x0 + c * cw + 6, y0 + r * ch + 6, cw - 12, ch - 12, shade(paper, 0.94), rx=8))
    meta = {"blanks": {"month": [540, 70, 800, 120]}, "anchors": {"day30": [x0 + 1 * cw + cw / 2, y0 + 4 * ch + ch / 2]},
            "grid": [x0, y0, cw, ch], "portals": {"sheet": [500, 50, 880, 960]}, "floor_y": 1040, "light": "daylight"}
    return o, meta


def cash_register():
    """Caixa registradora de 1950 no balcão, visor em branco."""
    o = [rect(0, 0, W, 620, mix(stone, warm, 0.12)), rect(0, 620, W, 460, wood), rect(0, 600, W, 40, shade(wood, 0.8))]
    o += [rect(560, 260, 800, 380, berry, rx=40), rect(560, 520, 800, 120, shade(berry, 0.8), rx=20),
          rect(700, 120, 520, 170, shade(berry, 0.85), rx=24), rect(740, 150, 440, 110, mix(coal, ice, 0.1), rx=10)]
    for r in range(3):
        for c in range(6):
            o.append(circle(700 + c * 105, 330 + r * 62, 26, paper))
    o += [rect(1380, 430, 120, 30, coal, rx=15), circle(1510, 445, 34, hl)]
    for i, x in enumerate(range(240, 520, 70)):
        o += [ellipse(x, 700 + (i % 2) * 20, 46, 16, shade(hl, 0.85)), ellipse(x, 692 + (i % 2) * 20, 46, 16, hl)]
    meta = {"blanks": {"display": [760, 160, 400, 90]}, "anchors": {"drawer": [960, 580], "coins": [380, 700]},
            "portals": {"display": [740, 150, 440, 110]}, "floor_y": 1040, "light": "warm indoor lamps"}
    return o, meta


def nyc_map():
    """Mapa de Nova York num quadro de cortiça: ilha abstrata, ruas em grade, faixa de título em branco."""
    o = [rect(0, 0, W, H, mix(kraft, wood, 0.25)), rect(150, 70, 1620, 940, shade(wood, 0.8), rx=12),
         rect(180, 100, 1560, 880, mix(ice, "#ffffff", 0.2))]
    island = [(820, 960), (760, 820), (740, 640), (780, 470), (860, 300), (960, 170), (1060, 130), (1090, 210),
              (1040, 380), (1000, 560), (960, 760), (900, 930)]
    o.append(poly(island, mix(stone, "#ffffff", 0.3)))
    o.append(poly([(1180, 980), (1150, 760), (1260, 560), (1500, 520), (1740, 600), (1740, 980)], mix(stone, pine, 0.25)))
    o.append(poly([(180, 520), (520, 470), (640, 640), (600, 980), (180, 980)], mix(stone, pine, 0.25)))
    o.append(rect(880, 470, 70, 140, mix(pine, "#ffffff", 0.3), rx=10))  # parque
    pts = " ".join(f"{x},{y}" for x, y in island)
    streets = "".join(rect(600, 200 + k * 80, 700, 7, shade(mix(stone, "#ffffff", 0.3), 0.88),
                           extra=f'transform="rotate(-25 900 {200 + k * 80})"') for k in range(11))
    o.append(f'<clipPath id="isl"><polygon points="{pts}"/></clipPath><g clip-path="url(#isl)">{streets}</g>')
    o.append(rect(220, 130, 600, 90, paper, rx=8))
    pins = [(860, 820), (900, 700), (840, 640), (930, 590), (960, 520), (880, 470), (990, 430), (930, 380),
            (1010, 330), (960, 300), (1040, 250), (900, 760), (820, 720), (980, 650)]
    meta = {"blanks": {"title": [240, 140, 560, 70]}, "anchors": {"pins": pins, "island": [920, 560]},
            "portals": {"island": [740, 130, 360, 830]}, "floor_y": 1040, "light": "daylight"}
    return o, meta


def newspaper():
    """Jornal de 1950 aberto na mesa: manchete e foto em branco, colunas como barras."""
    o = [rect(0, 0, W, H, mix(wood, warm, 0.1))]
    o += [rect(360, 70, 1220, 960, shade(paper, 0.88), rx=4), rect(340, 50, 1220, 960, paper, rx=4),
          rect(380, 90, 1140, 90, shade(paper, 0.93)), rect(380, 190, 1140, 8, coal)]
    o += [rect(380, 230, 1140, 150, shade(paper, 0.95))]  # faixa da manchete (blank)
    o += [rect(380, 410, 620, 380, mix(stone, coal, 0.3))]
    o += [rect(430, 600, 520, 160, shade(berry, 0.7), rx=30), rect(470, 470, 160, 160, mix(stone, warm, 0.2), rx=12)]
    for c in range(2):
        for r in range(16):
            o.append(rect(1040 + c * 245, 420 + r * 34, 220 - (r % 4 == 3) * 80, 12, shade(paper, 0.8), rx=6))
    for r in range(5):
        o.append(rect(380, 820 + r * 34, 620 - (r % 3 == 2) * 160, 12, shade(paper, 0.8), rx=6))
    meta = {"blanks": {"masthead": [400, 95, 1100, 80], "headline": [400, 240, 1100, 130]},
            "anchors": {"photo": [690, 600]}, "portals": {"photo": [380, 410, 620, 380]}, "floor_y": 1040, "light": "daylight"}
    return o, meta


def globe():
    """Globo de mesa num escritório à noite: o mundo inteiro."""
    o = [rect(0, 0, W, H, mix(coal, ice, 0.2)), rect(0, 820, W, 260, shade(wood, 0.9))]
    o += [circle(960, 430, 360, hl, 'opacity="0.08"'), circle(960, 450, 310, mix(ice, pine, 0.25)),
          path("M780,330 Q850,250 960,280 Q1010,340 940,400 Q860,420 820,480 Q760,440 780,330 Z", mix(stone, pine, 0.45)),
          path("M1000,470 Q1100,430 1160,500 Q1150,620 1060,680 Q990,620 1000,470 Z", mix(stone, pine, 0.45)),
          path("M720,560 Q790,540 830,600 Q800,690 740,700 Q700,640 720,560 Z", mix(stone, pine, 0.45)),
          path("M1180,300 Q1230,330 1220,390 Q1180,380 1180,300 Z", mix(stone, pine, 0.45))]
    o += [path("M600,450 A360,360 0 0 0 1320,450", "none", f'stroke="{shade(hl,0.7)}" stroke-width="22" fill="none"'),
          rect(940, 760, 40, 70, shade(hl, 0.7)), rect(800, 820, 320, 40, shade(hl, 0.7), rx=20)]
    meta = {"blanks": {}, "anchors": {"globe": [960, 450]}, "portals": {"globe": [700, 190, 520, 520]}, "floor_y": 840,
            "light": "night office lamp"}
    return o, meta


TILES = {"card_closeup": card_closeup, "dresser_wallet": dresser_wallet, "telephone": telephone, "calendar": calendar,
         "cash_register": cash_register, "nyc_map": nyc_map, "newspaper": newspaper, "globe": globe}


# ───────────── El Niño ─────────────
def _lonlat(lon, lat, lon0=110, k=10, x0=60, y0=540):
    if lon < 0:
        lon += 360
    return x0 + (lon - lon0) * k, y0 - lat * k


def pacific_map():
    """Mapa chapado do Pacífico equatorial: Austrália e Indonésia à esquerda, Américas à direita.
    A faixa do equador fica livre: o código pinta a água quente por cima."""
    sea = mix(ice, pine, 0.25); land = mix(stone, warm, 0.25)
    o = [rect(0, 0, W, H, sea)]
    for lat in (-30, -15, 15, 30):
        o.append(rect(0, 540 - lat * 10 - 2, W, 4, mix(sea, "#ffffff", 0.18)))
    o.append(rect(0, 538, W, 5, mix(sea, "#ffffff", 0.35)))  # equador
    P = lambda pts: poly([_lonlat(a, b) for a, b in pts], land)
    o.append(P([(114, -22), (114, -34), (118, -35), (124, -33), (129, -31.5), (135, -34.5), (138, -35), (140, -38), (146, -39),
                (150, -37.5), (153, -32), (153.5, -28), (153, -25), (149, -21), (146, -19), (145.5, -15), (143.5, -11), (142, -10.8),
                (141.5, -13), (141.5, -17), (140, -17.5), (137, -16), (136, -12), (132, -11.3), (129.5, -14.5), (126, -14),
                (122, -17.5), (121, -19.5), (117, -20.5)]))
    o.append(P([(131, -1), (141, -2.5), (147, -6), (150, -10.5), (146, -9), (141, -9), (137, -5), (132, -3)]))
    o.append(P([(104, 41), (122, 41), (122, 30), (118, 24), (110, 20), (108, 12), (105, 9), (104, 1.5), (101, 3), (99, 8), (99, 41)]))
    for (lo, la, rx, ry) in [(114, 0.5, 4.5, 4), (110, -7.2, 5, 1.1), (121, -2, 1.6, 3.5), (123, 11, 2, 5), (102, -1, 2.5, 4.5)]:
        x, y = _lonlat(lo, la); o.append(ellipse(x, y, rx * 10, ry * 10, land))
    o.append(P([(-124, 41), (-124, 40.5), (-122.5, 37.5), (-120.5, 34.5), (-117, 32.5), (-114.8, 31.5), (-112.5, 29.5), (-109, 25.5),
                (-105.5, 23), (-105.5, 20.5), (-103, 18.5), (-98, 16.5), (-95, 16), (-92, 14.7), (-88, 13.2), (-86, 11.5), (-83, 8.5),
                (-79.5, 7.5), (-78, 7), (-77.4, 4), (-78.8, 1.5), (-80.5, -0.5), (-80.9, -2.2), (-81.3, -4.5), (-81.1, -6), (-79.5, -8),
                (-77, -12), (-76, -14), (-71, -18), (-70.3, -25), (-71.5, -30), (-73.5, -37), (-73.7, -41), (-55, -41), (-55, 41)]))
    for lo, la in [(-149.4, -17.6), (-151.5, -16.8), (-145, -15)]:  # Taiti e vizinhas
        x, y = _lonlat(lo, la); o.append(circle(x, y, 7, land))
    px, py = _lonlat(-81.1, -5.1); dx, dy = _lonlat(130.8, -12.5); tx, ty = _lonlat(-149.4, -17.6)
    meta = {"blanks": {}, "anchors": {"peru": [px, py], "darwin": [dx, dy], "tahiti": [tx, ty],
                                      "band_w": list(_lonlat(150, 0)), "band_e": list(_lonlat(-85, 0)), "brazil_dir": [1900, 640]},
            "portals": {"ocean": [800, 330, 700, 420]}, "floor_y": 1000, "light": "flat map"}
    return o, meta


def sea_cutaway():
    """Corte do oceano: céu em cima, linha d'água, camadas de água (clara em cima, funda embaixo).
    O código desenha a nuvem de tempestade (mito) e a camada quente se espalhando (realidade)."""
    sky = mix(ice, "#ffffff", 0.35); s1 = mix(ice, pine, 0.3); s2 = mix(ice, pine, 0.55); s3 = mix(pine, coal, 0.45)
    o = [rect(0, 0, W, 470, sky), rect(0, 470, W, 200, s1), rect(0, 670, W, 210, s2), rect(0, 880, W, 200, s3)]
    for x in range(0, W, 160):
        o.append(path(f"M{x},470 Q{x+40},450 {x+80},470 Q{x+120},490 {x+160},470 Z", s1))
    for x, y in [(300, 760), (1500, 720), (900, 960), (1200, 820), (520, 930)]:
        o += [ellipse(x, y, 34, 14, shade(s2, 0.8)), poly([(x + 30, y), (x + 54, y - 14), (x + 54, y + 14)], shade(s2, 0.8))]
    for x, y, r in [(200, 140, 50), (1700, 190, 40)]:
        o += [ellipse(x, y, r * 2, r * 0.8, "#ffffff"), ellipse(x + r * 0.6, y - r * 0.4, r, r * 0.7, "#ffffff")]
    meta = {"blanks": {}, "anchors": {"surface": [960, 470], "deep": [960, 900], "cloud": [960, 200]},
            "portals": {"water": [560, 480, 800, 380]}, "floor_y": 1000, "light": "daylight over the sea"}
    return o, meta


def fishing_net():
    """Close na areia: rede de pesca vazia jogada ao lado de um cesto vazio e do casco do barco."""
    sand = mix(stone, warm, 0.32); wood = mix(berry, coal, 0.5); rope = mix(stone, coal, 0.25)
    o = [rect(0, 0, W, H, sand)]
    for x, y in [(200, 200), (1500, 160), (1700, 900), (300, 950), (1100, 120)]:
        o.append(ellipse(x, y, 60, 12, shade(sand, 0.9)))
    o += [path("M1380,0 L1920,0 L1920,420 Q1700,360 1540,240 Q1440,140 1380,0 Z", wood),
          path("M1420,0 L1480,0 Q1540,160 1650,240 Q1780,320 1920,350 L1920,380 Q1720,330 1600,240 Q1470,140 1420,0 Z", shade(wood, 0.8))]
    # rede: losangos em linha fina dentro de uma mancha
    net = [ellipse(860, 560, 520, 300, shade(sand, 0.94))]
    for i in range(-10, 11):
        net.append(rect(860 + i * 52 - 2, 270, 4, 580, rope, extra=f'transform="rotate(28 {860+i*52} 560)"'))
        net.append(rect(860 + i * 52 - 2, 270, 4, 580, rope, extra=f'transform="rotate(-28 {860+i*52} 560)"'))
    cid = "netclip"
    o.append(f'<clipPath id="{cid}">' + ellipse(860, 560, 500, 280, "#000") + "</clipPath>")
    o.append(g(net[1:], "") .replace("<g>", f'<g clip-path="url(#{cid})">'))
    o += [circle(420 + i * 110, 300 + (i % 2) * 20, 18, mix(warm, hl, 0.5)) for i in range(0, 9)]  # boias
    # cesto vazio
    o += [ellipse(1500, 760, 200, 70, shade(kraft, 0.8)), path("M1300,760 L1340,960 L1660,960 L1700,760 Z", kraft),
          ellipse(1500, 760, 200, 70, shade(kraft, 0.6)), ellipse(1500, 770, 170, 50, shade(kraft, 0.45))]
    for k in range(4):
        o.append(rect(1320 + k * 10, 800 + k * 40, 360 - k * 20, 8, shade(kraft, 0.85)))
    meta = {"blanks": {}, "anchors": {"net": [860, 560], "basket": [1500, 770]}, "portals": {"net": [520, 330, 700, 460]},
            "floor_y": 1000, "light": "hot daylight"}
    return o, meta


def pacific_horizon():
    """Horizonte do oceano aberto com duas ilhas pequenas (uma de cada lado do Pacífico).
    O código desenha a gangorra em cima."""
    sky = mix(ice, "#ffffff", 0.3); sea = mix(ice, pine, 0.38); land = mix(pine, stone, 0.3)
    o = [rect(0, 0, W, 640, sky), rect(0, 640, W, 440, sea), circle(960, 250, 90, mix(hl, "#ffffff", 0.4))]
    for x, y in [(160, 760), (700, 900), (1300, 820), (1700, 960), (420, 1010), (1050, 720)]:
        o.append(rect(x, y, 140, 9, mix(sea, "#ffffff", 0.3), rx=4))
    for cx in (330, 1590):
        o += [ellipse(cx, 650, 180, 40, land), ellipse(cx, 646, 140, 26, mix(land, warm, 0.25)),
              rect(cx - 6, 520, 12, 120, mix(berry, coal, 0.5))]
        for a in (-50, -10, 30, 70, 130):
            o.append(g(ellipse(0, -40, 18, 56, land), f"translate({cx},{524}) rotate({a})"))
    meta = {"blanks": {}, "anchors": {"pivot": [960, 640], "left_island": [330, 640], "right_island": [1590, 640]},
            "portals": {"sky": [560, 120, 800, 400]}, "floor_y": 650, "light": "bright midday"}
    return o, meta


def brazil_map():
    """Mapa chapado do Brasil sobre o oceano. O código põe sol/rachadura no Norte-Nordeste e nuvem de chuva no Sul."""
    sea = mix(ice, pine, 0.2); land = mix(pine, stone, 0.35)
    o = [rect(0, 0, W, H, sea)]
    for lat in (0, -15, -30):
        o.append(rect(0, 540 - (lat + 14.5) * 22 - 2, W, 4, mix(sea, "#ffffff", 0.15)))
    pts = [(-73.9, -7.5), (-72.5, -5.0), (-70.0, -4.2), (-69.4, -1.2), (-69.9, 1.0), (-67.0, 2.0), (-64.0, 2.5), (-62.0, 4.0),
           (-60.7, 5.2), (-59.8, 4.4), (-60.0, 2.0), (-56.5, 1.9), (-54.0, 2.2), (-51.6, 4.2), (-50.0, 1.8), (-49.5, 0.0),
           (-48.0, -1.0), (-44.5, -2.5), (-41.0, -2.9), (-38.5, -3.7), (-35.2, -5.4), (-34.8, -7.5), (-35.5, -9.5), (-37.0, -11.0),
           (-38.9, -13.5), (-39.0, -17.5), (-39.8, -19.5), (-41.0, -22.0), (-43.2, -23.0), (-45.5, -23.8), (-48.0, -25.5),
           (-48.6, -28.5), (-50.0, -30.5), (-52.0, -32.5), (-53.4, -33.7), (-53.5, -32.0), (-55.8, -30.9), (-57.6, -30.2),
           (-55.0, -27.5), (-54.6, -25.6), (-54.3, -24.0), (-55.5, -22.5), (-57.8, -22.1), (-58.0, -20.0), (-57.5, -18.0),
           (-58.4, -16.3), (-60.2, -15.0), (-60.5, -13.7), (-62.5, -13.0), (-65.0, -11.8), (-65.4, -10.0), (-66.5, -9.8),
           (-68.5, -11.0), (-70.5, -11.0), (-70.6, -9.5), (-72.2, -10.0), (-73.0, -9.4)]
    P = lambda lo, la: (960 + (lo + 54.5) * 22, 540 - (la + 14.5) * 22)
    o += [poly([(x + 10, y + 12) for x, y in (P(*p) for p in pts)], shade(land, 0.8)), poly([P(*p) for p in pts], land)]
    # vizinhos à margem (sem nomes)
    o.append(path("M0,0 L560,0 L560,250 Q470,320 420,420 L380,640 Q330,780 360,1080 L0,1080 Z", mix(stone, warm, 0.25)))
    meta = {"blanks": {}, "anchors": {"north": list(P(-60, -4)), "northeast": list(P(-40.5, -8)), "south": list(P(-51.5, -28))},
            "portals": {"brazil": [620, 120, 680, 860]}, "floor_y": 1000, "light": "flat map"}
    return o, meta


def bushfire():
    """Mato australiano seco com eucaliptos e fogo chapado; céu alaranjado de fumaça."""
    skyc = mix(warm, hl, 0.35); ground = mix(warm, berry, 0.35)
    o = [rect(0, 0, W, H, skyc), rect(0, 0, W, 260, mix(skyc, coal, 0.25)), circle(1450, 260, 70, mix(hl, "#ffffff", 0.3))]
    o += [path("M0,700 Q400,640 900,690 Q1400,740 1920,680 L1920,1080 L0,1080 Z", ground)]
    for x, h in [(150, 420), (470, 520), (820, 380), (1180, 560), (1560, 460), (1820, 400)]:
        o += [rect(x - 12, 720 - h, 24, h, mix(stone, coal, 0.45), rx=8)]
        for dx, dy, r in [(-60, -h + 30, 80), (50, -h + 10, 90), (0, -h - 40, 85)]:
            o.append(ellipse(x + dx, 720 + dy, r, r * 0.6, mix(coal, pine, 0.4)))
    for x in range(40, W, 180):
        o += [path(f"M{x},760 Q{x+20},620 {x+60},560 Q{x+70},650 {x+110},600 Q{x+120},700 {x+150},760 Z", C["alert"]),
              path(f"M{x+30},760 Q{x+45},680 {x+70},640 Q{x+85},700 {x+115},760 Z", hl)]
    meta = {"blanks": {}, "anchors": {"fire": [960, 680]}, "portals": {"sky": [560, 100, 800, 400]}, "floor_y": 900,
            "light": "orange smoky daylight"}
    return o, meta


TILES.update({"pacific_map": pacific_map, "sea_cutaway": sea_cutaway, "fishing_net": fishing_net,
              "pacific_horizon": pacific_horizon, "brazil_map": brazil_map, "bushfire": bushfire})
