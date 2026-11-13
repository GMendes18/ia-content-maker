"""plates.py — hero plates em SVG, VAZIOS (sem pessoas), vista frontal, chão livre no meio.
Cada plate devolve (svg, meta). O meta traz os retângulos em branco (blanks) onde o código
escreve depois, os portais (porta/janela/tela) do zoom_through e a linha do chão.
Coordenadas do mundo: 1920x1080. Rasterizado em 2x (3840x2160) para aguentar zoom.
"""
from svgkit import C, PAL, ROLE, circle, ellipse, g, mix, path, poly, rect, shade, svg

W, H = 1920, 1080


def restaurant_1950_night():
    """Nova York, 1950, noite: um restaurante com luminárias quentes, janela para a rua escura,
    quadro de menu em branco, porta com escotilha. Materiais: madeira pintada, ladrilho, toalha."""
    stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"],
                                     ROLE["coal"], ROLE["berry"])
    warm, hl = C["warm"], C["highlight"]
    wall = mix(stone, warm, 0.10)  # parede tingida pela luz quente das luminárias
    o = [rect(0, 0, W, 820, wall), rect(0, 0, W, 58, shade(wall, 0.84))]
    # lambri verde
    o += [rect(0, 600, W, 220, pine), rect(0, 588, W, 24, shade(pine, 0.8))]
    for x in range(40, W, 160):
        o.append(rect(x, 632, 112, 160, shade(pine, 0.9), rx=6))
    # chão de ladrilho, vista frontal
    o.append(rect(0, 820, W, 260, mix(stone, coal, 0.35)))
    tile = shade(mix(stone, coal, 0.35), 0.88)
    for row, y in enumerate(range(820, 1080, 52)):
        for i, x in enumerate(range(-60 if row % 2 else 0, W, 120)):
            if i % 2 == 0:
                o.append(rect(x, y, 60, 52, tile))
    o.append(rect(0, 816, W, 10, shade(pine, 0.7)))  # rodapé
    # janela (portal) — rua à noite
    wx, wy, ww, wh = 110, 150, 420, 370
    night = mix(coal, ice, 0.18)
    o += [rect(wx - 18, wy - 18, ww + 36, wh + 36, shade(stone, 0.92), rx=8), rect(wx, wy, ww, wh, night)]
    o.append(circle(wx + 320, wy + 80, 34, mix(ice, "#ffffff", 0.4)))
    skyline = [(0, 230), (60, 230), (60, 150), (130, 150), (130, 200), (190, 200), (190, 120), (250, 120),
               (250, 210), (300, 210), (300, 170), (360, 170), (360, 240), (420, 240), (420, wh), (0, wh)]
    o.append(poly([(wx + x, wy + y) for x, y in skyline], shade(night, 0.7)))
    for bx, by in [(80, 175), (95, 205), (205, 140), (220, 170), (205, 200), (320, 190), (75, 250)]:
        o.append(rect(wx + bx, wy + by, 12, 16, mix(hl, wall, 0.25), rx=2))
    o += [rect(wx + ww / 2 - 7, wy, 14, wh, shade(stone, 0.92)), rect(wx, wy + wh / 2 - 7, ww, 14, shade(stone, 0.92))]
    o.append(rect(wx - 30, wy + wh + 12, ww + 60, 18, shade(stone, 0.85), rx=6))  # peitoril
    # quadro de menu em BRANCO (blank) com moldura
    bx, by, bw, bh = 1120, 140, 440, 300
    o += [rect(bx, by, bw, bh, shade(berry, 0.55), rx=14), rect(bx + 22, by + 22, bw - 44, bh - 44, coal, rx=6),
          rect(bx + bw / 2 - 60, by - 40, 120, 14, shade(berry, 0.55), rx=7)]
    o.append(rect(bx + 30, by + bh - 18, bw - 60, 10, shade(berry, 0.45), rx=5))  # calha do giz
    # relógio de parede (sem números)
    o += [circle(820, 230, 62, shade(berry, 0.55)), circle(820, 230, 50, mix(ice, "#ffffff", 0.6)),
          rect(817, 192, 6, 42, coal, rx=3), rect(817, 227, 30, 6, coal, rx=3), circle(820, 230, 7, berry)]
    # luminárias pendentes + poças de luz chapadas
    for lx in (330, 960):
        o.append(rect(lx - 2, 58, 4, 60, coal))
        ly = 118
        o.append(circle(lx, ly + 40, 150, hl, 'opacity="0.10"'))
        o.append(circle(lx, ly + 40, 90, hl, 'opacity="0.12"'))
        o.append(path(f"M{lx-46},{ly+30} Q{lx-46},{ly-8} {lx},{ly-8} Q{lx+46},{ly-8} {lx+46},{ly+30} Z", berry))
        o.append(rect(lx - 46, ly + 26, 92, 8, shade(berry, 0.8), rx=4))
        o.append(ellipse(lx, ly + 36, 18, 8, mix(hl, "#ffffff", 0.4)))
    # porta (portal) com escotilha
    dx, dy, dw, dh = 1660, 250, 200, 570
    o += [rect(dx - 16, dy - 16, dw + 32, dh + 16, shade(pine, 0.7), rx=6), rect(dx, dy, dw, dh, mix(stone, pine, 0.25)),
          rect(dx + 20, dy + 300, dw - 40, 230, shade(mix(stone, pine, 0.25), 0.9), rx=8),
          circle(dx + dw / 2, dy + 140, 62, shade(stone, 0.8)), circle(dx + dw / 2, dy + 140, 50, night),
          circle(dx + 30, dy + 300, 11, hl)]
    # mesa à esquerda com toalha, prato e xícara (perto da janela)
    tx, ty, tw = 160, 700, 420
    cloth = mix(C["card"], ice, 0.2)
    o += [rect(tx + 40, ty + 60, 18, 120, coal), rect(tx + tw - 58, ty + 60, 18, 120, coal),
          rect(tx, ty, tw, 30, cloth, rx=8), path(f"M{tx},{ty+22} L{tx+tw},{ty+22} L{tx+tw-16},{ty+96} L{tx+16},{ty+96} Z", cloth),
          path(f"M{tx+tw*0.62},{ty+22} L{tx+tw},{ty+22} L{tx+tw-16},{ty+96} L{tx+tw*0.62},{ty+96} Z", shade(cloth, 0.9)),
          ellipse(tx + 150, ty - 2, 74, 15, "#ffffff"), ellipse(tx + 150, ty - 4, 46, 9, shade(cloth, 0.92)),
          rect(tx + 280, ty - 46, 46, 44, "#ffffff", rx=10), rect(tx + 322, ty - 36, 16, 22, "#ffffff", rx=8),
          ellipse(tx + 303, ty - 2, 40, 8, shade(cloth, 0.9))]
    # cadeira
    o += [rect(tx + tw + 20, ty - 120, 20, 300, shade(berry, 0.5), rx=8), rect(tx + tw + 20, ty + 60, 110, 22, shade(berry, 0.5), rx=8),
          rect(tx + tw + 110, ty + 70, 18, 110, shade(berry, 0.45), rx=6)]
    # booth à direita
    o += [rect(1180, 540, 420, 240, berry, rx=40), rect(1180, 540, 420, 50, shade(berry, 0.85), rx=40),
          rect(1180, 700, 420, 120, shade(berry, 0.8), rx=16),
          rect(1250, 680, 280, 26, stone, rx=8), rect(1378, 700, 24, 120, coal)]
    meta = {
        "name": "restaurant_1950_night", "kind": "hero", "size": [W, H], "floor_y": 900,
        "light": "warm indoor lamps at night",
        "blanks": {"menu_board": [bx + 40, by + 40, bw - 80, bh - 96]},
        "portals": {"window": [wx, wy, ww, wh], "door_porthole": [dx + dw / 2 - 50, dy + 90, 100, 100],
                    "menu_board": [bx + 22, by + 22, bw - 44, bh - 44]},
        "anchors": {"table_plate": [tx + 150, ty - 4], "cup": [tx + 303, ty - 24], "door": [dx + dw / 2, dy + dh],
                    "clock": [820, 230]},
        "open_floor": [620, 1120],
    }
    return svg(W, H, o), meta


def street_1950_night():
    """Rua de Nova York, 1950, noite fria: fachada do restaurante, poste, calçada."""
    stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"],
                                     ROLE["coal"], ROLE["berry"])
    hl = C["highlight"]
    sky = mix(coal, ice, 0.22)
    o = [rect(0, 0, W, H, sky), circle(1600, 160, 60, mix(ice, "#ffffff", 0.45))]
    far = shade(sky, 0.8)
    for x, w, h in [(0, 220, 520), (220, 160, 640), (380, 260, 470), (1500, 200, 600), (1700, 220, 520)]:
        o.append(rect(x, 820 - h, w, h, far))
        for wy in range(820 - h + 40, 780, 70):
            for wx in range(x + 24, x + w - 30, 54):
                if (wx * 7 + wy * 3) % 5 < 2:
                    o.append(rect(wx, wy, 22, 30, mix(hl, far, 0.35), rx=3))
    # fachada do restaurante
    fx, fw = 500, 820
    o += [rect(fx, 240, fw, 580, mix(stone, berry, 0.15)), rect(fx - 20, 220, fw + 40, 36, shade(stone, 0.8), rx=6),
          rect(fx + 40, 300, fw - 80, 110, shade(berry, 0.7), rx=10)]  # letreiro em branco (blank)
    o += [rect(fx + 60, 470, 300, 260, mix(hl, stone, 0.35)), rect(fx + 460, 470, 300, 260, mix(hl, stone, 0.35)),
          rect(fx + 360, 450, 100, 370, shade(pine, 0.8)), circle(fx + 440, 640, 8, hl)]
    for x in (fx + 60, fx + 460):
        o += [rect(x + 146, 470, 8, 260, shade(stone, 0.85)), rect(x, 596, 300, 8, shade(stone, 0.85))]
    # toldo
    for i in range(10):
        o.append(rect(fx + 40 + i * 74, 420, 74, 40, berry if i % 2 == 0 else mix(stone, "#ffffff", .4)))
    # calçada e rua
    o += [rect(0, 820, W, 80, mix(stone, coal, 0.4)), rect(0, 900, W, 180, shade(coal, 1.1)),
          rect(0, 820, W, 8, shade(mix(stone, coal, 0.4), 0.85))]
    for x in range(40, W, 260):
        o.append(rect(x, 980, 140, 12, mix(stone, coal, 0.2), rx=6))
    # poste com poça de luz
    px = 300
    o += [circle(px + 60, 390, 220, hl, 'opacity="0.08"'), circle(px + 60, 390, 120, hl, 'opacity="0.12"'),
          rect(px - 8, 380, 16, 450, coal), rect(px - 8, 370, 80, 14, coal, rx=7),
          path(f"M{px+30},{396} L{px+90},{396} L{px+80},{372} L{px+40},{372} Z", coal),
          ellipse(px + 60, 400, 24, 9, mix(hl, "#ffffff", 0.4))]
    meta = {"name": "street_1950_night", "kind": "hero", "size": [W, H], "floor_y": 870,
            "light": "cold night street, warm shop windows",
            "blanks": {"shop_sign": [fx + 60, 312, fw - 120, 86]},
            "portals": {"left_window": [fx + 60, 470, 300, 260], "door": [fx + 360, 450, 100, 370]},
            "anchors": {"door": [fx + 410, 820], "lamp": [px + 60, 400]},
            "open_floor": [420, 1500]}
    return svg(W, H, o), meta


PLATES = {"restaurant_1950_night": restaurant_1950_night, "street_1950_night": street_1950_night}


def office_1950_day():
    """Escritório em Nova York, 1950, de dia: janela com a cidade, mesa com máquina de escrever,
    arquivo, quadro-negro em branco (para o código escrever a ideia), porta com vidro."""
    stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"],
                                     ROLE["coal"], ROLE["berry"])
    hl = C["highlight"]
    wood = mix(berry, coal, 0.55)
    wall = mix(ice, stone, 0.55)
    o = [rect(0, 0, W, 830, wall), rect(0, 0, W, 50, shade(wall, 0.85)),
         rect(0, 830, W, 250, mix(wood, stone, 0.35)), rect(0, 822, W, 14, shade(wood, 0.8))]
    for x in range(0, W, 160):  # tábuas do piso
        o.append(rect(x, 836, 6, 244, shade(mix(wood, stone, 0.35), 0.9)))
    # janela (portal) com a cidade de dia
    wx, wy, ww, wh = 90, 140, 520, 430
    sky = mix(ice, "#ffffff", 0.25)
    o += [rect(wx - 20, wy - 20, ww + 40, wh + 40, shade(stone, 0.85), rx=6), rect(wx, wy, ww, wh, sky)]
    for bx, bw, bh in [(0, 110, 260), (110, 90, 330), (200, 140, 220), (340, 80, 300), (420, 100, 240)]:
        o.append(rect(wx + bx, wy + wh - bh, bw, bh, mix(stone, ice, 0.35)))
        for yy in range(wy + wh - bh + 24, wy + wh - 20, 46):
            for xx in range(wx + bx + 14, wx + bx + bw - 20, 30):
                o.append(rect(xx, yy, 14, 22, mix(stone, coal, 0.2)))
    o += [rect(wx + ww / 2 - 8, wy, 16, wh, shade(stone, 0.85)), rect(wx, wy + wh / 2 - 8, ww, 16, shade(stone, 0.85))]
    # quadro-negro (blank) com moldura de madeira
    bx, by, bw, bh = 720, 130, 640, 360
    o += [rect(bx, by, bw, bh, wood, rx=12), rect(bx + 20, by + 20, bw - 40, bh - 40, mix(pine, coal, 0.55), rx=6),
          rect(bx + 30, by + bh - 16, bw - 60, 12, shade(wood, 0.8), rx=6)]
    # porta com vidro (portal)
    dx, dy, dw, dh = 1630, 240, 220, 590
    o += [rect(dx - 14, dy - 14, dw + 28, dh + 14, shade(wood, 0.85), rx=6), rect(dx, dy, dw, dh, wood),
          rect(dx + 30, dy + 40, dw - 60, 230, mix(ice, "#ffffff", 0.4), rx=8), circle(dx + 30, dy + 330, 12, hl)]
    # arquivo de aço
    o += [rect(1420, 470, 170, 360, mix(stone, coal, 0.25), rx=8)]
    for i in range(3):
        o += [rect(1436, 486 + i * 115, 138, 100, mix(stone, coal, 0.15), rx=6), rect(1480, 520 + i * 115, 50, 14, coal, rx=7)]
    # mesa com máquina de escrever, papéis e luminária de mesa
    o += [rect(560, 650, 640, 40, wood, rx=8), rect(590, 690, 40, 140, shade(wood, 0.8)), rect(1130, 690, 40, 140, shade(wood, 0.8)),
          rect(620, 690, 520, 90, shade(wood, 0.9))]
    o += [rect(760, 570, 260, 80, coal, rx=18), rect(790, 540, 200, 40, shade(coal, 1.3), rx=10), rect(820, 500, 140, 60, paper_c := mix(C["card"], hl, 0.08))]
    o += [rect(1060, 620, 100, 30, paper_c, rx=4), rect(1070, 605, 100, 30, shade(paper_c, 0.95), rx=4)]
    o += [circle(640, 560, 120, hl, 'opacity="0.10"'), rect(632, 580, 14, 70, coal), path("M590,590 L690,590 L660,530 L620,530 Z", pine)]
    # cabideiro com chapéu
    o += [rect(470, 330, 14, 500, coal), rect(440, 820, 74, 12, coal, rx=6), rect(430, 330, 94, 12, coal, rx=6),
          rect(450, 300, 54, 34, coal, rx=12), rect(436, 326, 82, 10, coal, rx=5)]
    meta = {"name": "office_1950_day", "kind": "hero", "size": [W, H], "floor_y": 920, "light": "daylight",
            "blanks": {"blackboard": [bx + 50, by + 45, bw - 100, bh - 100], "typewriter_page": [828, 506, 124, 44]},
            "portals": {"window": [wx, wy, ww, wh], "blackboard": [bx + 20, by + 20, bw - 40, bh - 40], "door_glass": [dx + 30, dy + 40, dw - 60, 230]},
            "anchors": {"desk": [880, 650], "door": [dx + dw / 2, dy + dh], "file": [1505, 470]},
            "open_floor": [300, 1600]}
    return svg(W, H, o), meta


PLATES["office_1950_day"] = office_1950_day


def harbor_paita_1890_day():
    """Praia de pescadores em Paita, Peru, ~1890, de dia: mar no horizonte, barco de madeira na areia,
    rede secando em varas, casinhas de adobe com torre de igreja à esquerda. Centro livre para o pescador."""
    stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"],
                                     ROLE["coal"], ROLE["berry"])
    hl, warm = C["highlight"], C["warm"]
    sky = mix(ice, "#ffffff", 0.3); sea = mix(ice, pine, 0.38); sand = mix(stone, warm, 0.32)
    wood = mix(berry, coal, 0.5)
    o = [rect(0, 0, W, 470, sky), circle(1480, 150, 70, mix(hl, "#ffffff", 0.35)),
         path("M0,470 L0,380 Q160,330 330,380 Q470,350 600,420 L600,470 Z", mix(stone, ice, 0.25)),
         path("M1300,470 Q1480,360 1650,410 Q1800,370 1920,400 L1920,470 Z", mix(stone, ice, 0.25)),
         rect(0, 460, W, 260, sea)]
    for y, xs in [(520, range(80, W, 340)), (590, range(240, W, 380)), (660, range(40, W, 300))]:
        for x in xs:
            o.append(rect(x, y, 120, 8, mix(sea, "#ffffff", 0.35), rx=4))
    o += [path(f"M0,720 Q480,690 960,712 Q1440,734 1920,705 L1920,{H} L0,{H} Z", sand),
          rect(0, 700, W, 16, mix(sea, "#ffffff", 0.55), rx=8)]
    for x, y in [(200, 860), (650, 990), (1180, 940), (1650, 1020), (1500, 830)]:
        o.append(ellipse(x, y, 40, 8, shade(sand, 0.9)))
    # casinhas de adobe e torre da igreja (esquerda, longe)
    adobe = mix(warm, stone, 0.55)
    for x, w, h in [(30, 150, 120), (190, 120, 100), (320, 140, 130)]:
        o += [rect(x, 720 - h, w, h, adobe), rect(x - 6, 720 - h - 12, w + 12, 16, shade(adobe, 0.8), rx=4),
              rect(x + w / 2 - 16, 720 - 60, 32, 60, shade(adobe, 0.7), rx=4)]
    o += [rect(250, 470, 70, 150, mix(adobe, "#ffffff", 0.3)), poly([(240, 470), (285, 420), (330, 470)], berry),
          rect(276, 500, 18, 30, shade(adobe, 0.6), rx=9)]
    # barco de madeira na areia (casco = blank para o nome)
    bx = 620
    o += [path(f"M{bx},760 L{bx+420},760 Q{bx+400},860 {bx+330},868 L{bx+80},868 Q{bx+20},850 {bx},760 Z", wood),
          rect(bx + 20, 750, 400, 20, shade(wood, 0.8), rx=8), rect(bx + 200, 470, 14, 290, shade(wood, 0.8)),
          path(f"M{bx+216},490 L{bx+216},720 L{bx+360},720 Z", mix(stone, "#ffffff", 0.5))]
    # varas com a rede secando (direita)
    nx = 1300
    o += [rect(nx, 560, 14, 300, wood), rect(nx + 300, 560, 14, 300, wood)]
    for i in range(7):
        o.append(rect(nx + 14, 580 + i * 32, 286, 4, mix(stone, coal, 0.2)))
    for i in range(10):
        o.append(rect(nx + 14 + i * 30, 580, 4, 200, mix(stone, coal, 0.2)))
    o += [ellipse(nx + 150, 880, 120, 18, mix(stone, coal, 0.3)), rect(nx + 60, 840, 70, 40, mix(stone, wood, 0.4), rx=8)]
    meta = {"name": "harbor_paita_1890_day", "kind": "hero", "size": [W, H], "floor_y": 900,
            "light": "hot coastal daylight",
            "blanks": {"boat_name": [bx + 90, 782, 240, 56]},
            "portals": {"sea": [520, 470, 900, 230]},
            "anchors": {"boat": [bx + 210, 800], "net": [nx + 150, 680], "sea": [960, 580]},
            "open_floor": [400, 1500]}
    return svg(W, H, o), meta


PLATES["harbor_paita_1890_day"] = harbor_paita_1890_day


def observatory_india_1920():
    """Sala do observatório na Índia, anos 1920: janela em arco com palmeira e céu quente,
    barômetro grande na parede (ponteiro desenhado pelo código), quadro de papel em branco, mesa com mapas."""
    stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"],
                                     ROLE["coal"], ROLE["berry"])
    hl, warm = C["highlight"], C["warm"]
    wall = mix(stone, warm, 0.28); wood = mix(berry, coal, 0.5)
    o = [rect(0, 0, W, 840, wall), rect(0, 0, W, 60, shade(wall, 0.85)), rect(0, 790, W, 50, shade(wall, 0.9))]
    floor = mix(warm, berry, 0.35)
    o.append(rect(0, 840, W, 240, floor))
    for i, x in enumerate(range(0, W, 120)):
        for j, y in enumerate(range(840, H, 80)):
            if (i + j) % 2:
                o.append(rect(x, y, 120, 80, shade(floor, 0.92)))
    # janela em arco (portal) com palmeira
    wx, wy, ww, wh = 140, 210, 420, 470
    sky = mix(hl, "#ffffff", 0.45)
    o += [path(f"M{wx-24},{wy+wh+24} L{wx-24},{wy+ww/2} A{ww/2+24},{ww/2+24} 0 0 1 {wx+ww+24},{wy+ww/2} L{wx+ww+24},{wy+wh+24} Z", shade(wall, 0.8)),
          path(f"M{wx},{wy+wh} L{wx},{wy+ww/2} A{ww/2},{ww/2} 0 0 1 {wx+ww},{wy+ww/2} L{wx+ww},{wy+wh} Z", sky),
          rect(wx, wy + wh - 120, ww, 120, mix(warm, stone, 0.4)),
          path(f"M{wx+260},{wy+wh-110} Q{wx+250},{wy+300} {wx+290},{wy+190} L{wx+306},{wy+192} Q{wx+272},{wy+300} {wx+284},{wy+wh-110} Z", wood)]
    for a in (-60, -20, 20, 60, 110, 160):
        o.append(g(ellipse(0, -70, 30, 90, pine), f"translate({wx+298},{wy+190}) rotate({a})"))
    o.append(rect(wx + ww / 2 - 8, wy + 60, 16, wh - 60, shade(wall, 0.8)))
    # barômetro grande (anchor = centro do mostrador)
    bx, by = 1330, 330
    o += [rect(bx - 30, by + 150, 60, 360, wood, rx=30), circle(bx, by, 190, wood), circle(bx, by, 160, mix(C["card"], hl, 0.12)),
          circle(bx, by, 14, coal)]
    for k in range(13):
        import math as _m
        a = _m.radians(-225 + k * 22.5)
        o.append(g(rect(-3, -150, 6, 24, coal, rx=3), f"translate({bx},{by}) rotate({_m.degrees(a)+90})"))
    o += [circle(bx, by + 420, 40, shade(wood, 0.8)), rect(bx - 6, by + 180, 12, 230, mix(berry, "#ffffff", 0.2))]
    # quadro de papel na parede (blank) e mesa com mapas
    px, py, pw, ph = 660, 170, 480, 330
    o += [rect(px - 16, py - 16, pw + 32, ph + 32, wood, rx=10), rect(px, py, pw, ph, mix(C["card"], hl, 0.1), rx=4)]
    o += [rect(620, 660, 620, 36, wood, rx=8), rect(650, 696, 36, 150, shade(wood, 0.8)), rect(1170, 696, 36, 150, shade(wood, 0.8)),
          rect(700, 630, 260, 34, mix(C["card"], hl, 0.15), rx=4, extra='transform="rotate(-3 830 647)"'),
          rect(980, 628, 200, 36, mix(ice, "#ffffff", 0.3), rx=4), circle(1180, 610, 26, hl, 'opacity="0.0"')]
    # ventilador de teto (punkah)
    o += [rect(940, 60, 12, 70, coal), rect(800, 126, 290, 22, mix(stone, "#ffffff", 0.3), rx=11)]
    meta = {"name": "observatory_india_1920", "kind": "hero", "size": [W, H], "floor_y": 930, "light": "hot afternoon daylight",
            "blanks": {"wall_chart": [px + 30, py + 30, pw - 60, ph - 60]},
            "portals": {"window": [wx, wy + 60, ww, wh - 60], "chart": [px, py, pw, ph]},
            "anchors": {"barometer": [bx, by], "desk": [930, 660]},
            "open_floor": [300, 1600]}
    return svg(W, H, o), meta


PLATES["observatory_india_1920"] = observatory_india_1920


def lab_1969_day():
    """Sala de meteorologia de uma universidade, 1969: quadro-negro grande em branco,
    computador de gabinete com fitas, mesa com papéis perfurados, janela com céu claro."""
    stone, ice, pine, coal, berry = (ROLE["stone"], ROLE["ice"], ROLE["pine"],
                                     ROLE["coal"], ROLE["berry"])
    hl, warm = C["highlight"], C["warm"]
    wall = mix(ice, stone, 0.45); floor = mix(stone, ice, 0.3)
    o = [rect(0, 0, W, 840, wall), rect(0, 0, W, 54, shade(wall, 0.85)), rect(0, 820, W, 20, shade(wall, 0.8)),
         rect(0, 840, W, 240, floor)]
    for i, x in enumerate(range(0, W, 110)):
        for j, y in enumerate(range(840, H, 80)):
            if (i + j) % 2:
                o.append(rect(x, y, 110, 80, shade(floor, 0.9)))
    # janela à esquerda
    wx, wy, ww, wh = 60, 170, 330, 420
    o += [rect(wx - 18, wy - 18, ww + 36, wh + 36, shade(wall, 0.8), rx=6), rect(wx, wy, ww, wh, mix(ice, "#ffffff", 0.4)),
          rect(wx, wy + wh - 130, ww, 130, mix(pine, ice, 0.35)), rect(wx + ww / 2 - 7, wy, 14, wh, shade(wall, 0.8))]
    # quadro-negro (blank)
    bx, by, bw, bh = 560, 130, 800, 430
    o += [rect(bx - 22, by - 22, bw + 44, bh + 44, mix(stone, coal, 0.2), rx=10), rect(bx, by, bw, bh, mix(pine, coal, 0.55), rx=6),
          rect(bx + 40, by + bh + 4, bw - 80, 14, mix(stone, coal, 0.3), rx=7)]
    # computador de gabinete com duas fitas
    cx = 1480
    o += [rect(cx, 330, 300, 500, mix(stone, coal, 0.15), rx=12), rect(cx + 20, 350, 260, 220, mix(stone, coal, 0.35), rx=10)]
    for k in (0, 1):
        o += [circle(cx + 85 + k * 130, 430, 52, coal), circle(cx + 85 + k * 130, 430, 18, mix(stone, "#ffffff", 0.3))]
    for r_ in range(3):
        for c_ in range(6):
            o.append(circle(cx + 50 + c_ * 40, 610 + r_ * 36, 9, [berry, hl, ice][(r_ + c_) % 3]))
    o += [rect(cx + 40, 730, 220, 70, shade(mix(stone, coal, 0.15), 0.85), rx=8)]
    # mesa com papel contínuo
    o += [rect(300, 660, 500, 34, mix(berry, coal, 0.5), rx=8), rect(330, 694, 30, 150, mix(berry, coal, 0.4)),
          rect(740, 694, 30, 150, mix(berry, coal, 0.4)), rect(420, 610, 240, 50, mix(C["card"], ice, 0.2), rx=4)]
    for k in range(4):
        o.append(rect(440, 622 + k * 9, 200, 3, mix(ice, coal, 0.2)))
    meta = {"name": "lab_1969_day", "kind": "hero", "size": [W, H], "floor_y": 930, "light": "cool fluorescent daylight",
            "blanks": {"blackboard": [bx + 40, by + 40, bw - 80, bh - 80]},
            "portals": {"blackboard": [bx, by, bw, bh], "window": [wx, wy, ww, wh]},
            "anchors": {"computer": [cx + 150, 430], "desk": [550, 660]},
            "open_floor": [300, 1600]}
    return svg(W, H, o), meta


PLATES["lab_1969_day"] = lab_1969_day
