#!/usr/bin/env python3
"""roll_dna.py — sorteia o DNA do canal (uma vez) e os traços por vídeo (a cada vídeo).

Uso:
  python3 roll_dna.py                      # sorteia um DNA novo do canal
  python3 roll_dna.py --seed 123           # reproduz um sorteio
  python3 roll_dna.py --lock font=3        # trava um traço (índice 1-based da lista)
  python3 roll_dna.py --reroll music       # re-sorteia só um traço do dna.json existente
  python3 roll_dna.py --video              # sorteia os traços por vídeo (checa library/log.json)
  python3 roll_dna.py --card               # só mostra o card do dna.json atual

Nunca escolha traços à mão: o modelo tende à primeira opção. O sorteio é código.
"""
import argparse, colorsys, datetime, json, os, pathlib, random, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DNA_PATH = ROOT / "dna.json"
LOG_PATH = ROOT / "library" / "log.json"
BACKUP_DIR = ROOT / "library" / "backups"

# ───────────────────────── cores ─────────────────────────

def hx(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v * 255))) for v in (r, g, b))

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def hsl(h, s, l):
    return hx(*colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100))

def lum(h):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def hue(h):
    return colorsys.rgb_to_hls(*rgb(h))[0] * 360

def sat(h):
    return colorsys.rgb_to_hls(*rgb(h))[2]

def hue_dist(a, b):
    d = abs(hue(a) - hue(b)) % 360
    return min(d, 360 - d)

def darken_until(spec, against, ratio):
    """Baixa só a luminosidade (mantém matiz e saturação) até o contraste passar."""
    h, s, l = spec
    while l > 3:
        c = hsl(h, s, l)
        if contrast(c, against) >= ratio:
            return c
        l -= 0.5
    return hsl(h, s, l)

# Cada paleta: as 5 cores do prompt de arte + specs HSL das 11 cores de código.
# Specs são (matiz°, saturação%, luminosidade%); o derive() corrige a luminosidade.
PALETTES = {
    "Dusty Dawn": {
        "colors": [("dusty blue-grey", "#8a9bb0"), ("slate teal", "#4f7c82"), ("warm beige", "#e8d9c4"),
                   ("navy", "#1f2a48"), ("soft purple", "#9a86c2")],
        # conjunto original, mantido literalmente como o prompt manda
        "fixed": {"ink": "#2b2d42", "alert": "#d62828", "warm": "#f4a261", "highlight": "#f6b93b",
                  "success": "#2fb37a", "dark": "#1f2a48", "headline_a": "#e2552f", "headline_b": "#5b3fa6",
                  "label_grey": "#8a8c9c", "card": "#ffffff", "transition_fill": "#f4f1fb"},
    },
    "Desert Clay": {
        "colors": [("terracotta", "#c2603f"), ("sand", "#e3cfa8"), ("sage green", "#9aab89"),
                   ("deep cocoa", "#4a3328"), ("mustard", "#d4a23a")],
        "spec": {"ink": (20, 30, 16), "alert": (347, 62, 42), "warm": (20, 62, 50), "highlight": (52, 72, 50),
                 "success": (120, 28, 40), "dark": (20, 30, 18), "headline_a": (15, 52, 42),
                 "headline_b": (95, 18, 32), "label_grey": (30, 10, 50), "card": (40, 45, 97),
                 "transition_fill": (38, 48, 88)},
    },
    "Nordic Frost": {
        "colors": [("ice blue", "#bcd8e6"), ("pale stone grey", "#c9cbc8"), ("pine green", "#2f5d4a"),
                   ("charcoal", "#2e3236"), ("berry red", "#a3324f")],
        "spec": {"ink": (210, 12, 18), "alert": (345, 60, 42), "warm": (20, 65, 52), "highlight": (52, 75, 55),
                 "success": (155, 35, 35), "dark": (210, 10, 20), "headline_a": (345, 55, 40),
                 "headline_b": (155, 33, 30), "label_grey": (210, 6, 50), "card": (200, 30, 97),
                 "transition_fill": (200, 45, 90)},
    },
    "Retro Mint": {
        "colors": [("mint", "#a8dcc5"), ("cream", "#f5ecd7"), ("coral", "#ef7d63"),
                   ("deep teal", "#1f5c5c"), ("burgundy", "#7a2335")],
        "spec": {"ink": (180, 45, 15), "alert": (340, 62, 40), "warm": (12, 80, 62), "highlight": (45, 80, 55),
                 "success": (160, 45, 38), "dark": (180, 50, 16), "headline_a": (350, 55, 32),
                 "headline_b": (180, 50, 25), "label_grey": (180, 8, 48), "card": (42, 60, 97),
                 "transition_fill": (155, 45, 90)},
    },
    "Ink and Ochre": {
        "colors": [("ochre", "#c8902f"), ("warm off-white", "#f3ede0"), ("indigo", "#2f3a6b"),
                   ("rust", "#a84a2a"), ("olive", "#6f7436")],
        "spec": {"ink": (230, 40, 18), "alert": (347, 65, 42), "warm": (18, 60, 42), "highlight": (50, 70, 52),
                 "success": (85, 38, 36), "dark": (230, 35, 18), "headline_a": (18, 58, 38),
                 "headline_b": (230, 38, 30), "label_grey": (35, 8, 48), "card": (42, 40, 97),
                 "transition_fill": (40, 38, 90)},
    },
    "Dusk Arcade": {
        "colors": [("deep plum", "#4a2545"), ("muted cyan", "#6fb3b8"), ("dusty magenta", "#b8577f"),
                   ("midnight blue", "#1c2541"), ("warm butter yellow", "#f2d58a")],
        "spec": {"ink": (228, 40, 15), "alert": (350, 68, 45), "warm": (22, 72, 55), "highlight": (54, 80, 58),
                 "success": (165, 40, 38), "dark": (228, 40, 16), "headline_a": (330, 40, 40),
                 "headline_b": (305, 32, 22), "label_grey": (260, 8, 50), "card": (300, 25, 97),
                 "transition_fill": (45, 75, 88)},
    },
    "Forest Paper": {
        "colors": [("moss", "#8a9a4b"), ("kraft beige", "#d8c3a0"), ("forest green", "#2e4a33"),
                   ("plum", "#5e3150"), ("cream", "#f4eedd")],
        "spec": {"ink": (135, 25, 14), "alert": (350, 62, 42), "warm": (22, 60, 50), "highlight": (54, 70, 50),
                 "success": (130, 35, 35), "dark": (135, 25, 15), "headline_a": (318, 30, 30),
                 "headline_b": (135, 25, 28), "label_grey": (40, 8, 46), "card": (45, 55, 97),
                 "transition_fill": (36, 40, 85)},
    },
    "Candy Slate": {
        "colors": [("slate grey", "#5f6b7a"), ("peach", "#f3b49a"), ("lilac", "#b9a6d6"),
                   ("butter yellow", "#f5df8a"), ("sea teal", "#3f9c96")],
        "spec": {"ink": (215, 22, 16), "alert": (347, 65, 45), "warm": (18, 82, 65), "highlight": (50, 85, 62),
                 "success": (176, 42, 36), "dark": (215, 20, 20), "headline_a": (215, 18, 35),
                 "headline_b": (265, 35, 45), "label_grey": (215, 8, 50), "card": (30, 50, 98),
                 "transition_fill": (265, 45, 92)},
    },
    "Harbour": {
        "colors": [("navy", "#1d2f4f"), ("sail white", "#f6f3ec"), ("brick red", "#a8432f"),
                   ("sea-glass green", "#8fc3ac"), ("rope tan", "#c9a273")],
        "spec": {"ink": (218, 45, 15), "alert": (343, 62, 42), "warm": (15, 58, 45), "highlight": (48, 80, 55),
                 "success": (152, 35, 38), "dark": (218, 45, 16), "headline_a": (12, 56, 40),
                 "headline_b": (218, 45, 28), "label_grey": (215, 8, 50), "card": (40, 40, 98),
                 "transition_fill": (40, 35, 92)},
    },
    "Citrus Concrete": {
        "colors": [("concrete grey", "#a5a7a4"), ("lime", "#b5d33d"), ("tangerine", "#f08a24"),
                   ("graphite", "#33363a"), ("sky blue", "#6fb7e3")],
        "spec": {"ink": (215, 8, 15), "alert": (352, 72, 46), "warm": (28, 86, 52), "highlight": (203, 65, 55),
                 "success": (78, 60, 42), "dark": (215, 8, 18), "headline_a": (28, 85, 40),
                 "headline_b": (203, 60, 35), "label_grey": (210, 4, 48), "card": (90, 10, 98),
                 "transition_fill": (75, 55, 88)},
    },
}

def derive_code_colours(name):
    p = PALETTES[name]
    if "fixed" in p:
        return dict(p["fixed"])
    s = p["spec"]
    card = hsl(*s["card"])
    out = {"card": card}
    out["ink"] = darken_until(s["ink"], card, 7.0)
    out["alert"] = darken_until(s["alert"], card, 4.5)
    out["headline_a"] = darken_until(s["headline_a"], "#ffffff", 4.5)
    out["headline_b"] = darken_until(s["headline_b"], "#ffffff", 4.5)
    out["label_grey"] = darken_until(s["label_grey"], card, 3.0)  # regra extra: legível no card
    for k in ("warm", "highlight", "success", "dark", "transition_fill"):
        out[k] = hsl(*s[k])
    order = ["ink", "alert", "warm", "highlight", "success", "dark", "headline_a", "headline_b",
             "label_grey", "card", "transition_fill"]
    return {k: out[k] for k in order}

def validate_colours(c):
    """Devolve a lista de regras que falham (vazia = tudo certo)."""
    fails = []
    if contrast(c["ink"], c["card"]) < 7: fails.append("ink/card < 7:1 (%.2f)" % contrast(c["ink"], c["card"]))
    if contrast(c["alert"], c["card"]) < 4.5: fails.append("alert/card < 4.5:1 (%.2f)" % contrast(c["alert"], c["card"]))
    for k in ("headline_a", "headline_b"):
        if contrast("#ffffff", c[k]) < 4.5: fails.append("branco/%s < 4.5:1 (%.2f)" % (k, contrast("#ffffff", c[k])))
    sig = ["alert", "warm", "highlight", "success"]
    for i, a in enumerate(sig):
        for b in sig[i + 1:]:
            if hue_dist(c[a], c[b]) < 30:
                fails.append("matiz %s↔%s só %.0f° (< 30°)" % (a, b, hue_dist(c[a], c[b])))
    return fails

def chroma_key(palette_name):
    """Verde #00B140 por padrão; magenta se a paleta tiver um verde perto dele."""
    for _, h in PALETTES[palette_name]["colors"]:
        if hue_dist(h, "#00b140") < 40 and sat(h) > 0.25:
            return {"name": "magenta", "hex": "#FF00FF", "reason": "a paleta tem um verde perto de #00B140"}
    return {"name": "green", "hex": "#00B140", "reason": "nenhum verde da paleta perto de #00B140"}

# ───────────────────────── traços ─────────────────────────

CHANNEL_TRAITS = {  # ordem fixa: a mesma seed sempre dá o mesmo DNA
    "palette": list(PALETTES.keys()),
    "character_build": [
        "Big round heads, dot eyes, small bodies",
        "Tall pill-shaped bodies, oval heads, solid-shape eyebrows that carry the emotion",
        "Chunky rounded-square heads, stubby legs, wide shoulders",
        "Long thin limbs, small heads, oversized hands and shoes",
        "Egg-shaped heads with no nose, big blocky hair shapes, tiny feet",
        "Bean bodies where head and torso are one shape, dot eyes set wide",
    ],
    "font": [["Montserrat", 900], ["Poppins", 800], ["Archivo Black", 400], ["Anton", 400],
             ["Bebas Neue", 400], ["Rubik", 800], ["Barlow Condensed", 800], ["Lexend", 800],
             ["Outfit", 800], ["Fredoka", 700], ["Unbounded", 800], ["Sora", 800]],
    "card_style": ["rounded_soft_shadow", "square_hard_offset", "pill_accent_strip", "paper_note_tape",
                   "die_cut_sticker"],
    "hud": ["top_left", "top_right", "bottom_left", "top_strip"],
    "tag_style": ["line_dot_pill", "curved_arrow", "bracket", "flag_pole", "triangle_pointer"],
    "text_entry": ["typing", "word_pop", "mask_slide_up", "drop_bounce"],
    "motion": ["bouncy", "snappy", "floaty", "punchy"],
    "camera": ["slow_push_pan", "handheld_drift", "snap_zoom", "parallax"],
    "shot_transition": ["push_horizontal", "push_vertical", "circle_iris", "diagonal_slats", "zoom_through"],
    "chapter_transition": ["blob_splat", "paint_swipe", "shutter_5_bars", "ink_drop", "page_curl"],
    "narrator": ["deep warm US documentary", "crisp British documentary", "calm warm female documentary",
                 "energetic younger US explainer", "dry deadpan storyteller", "gravelly older storyteller"],
    "music": ["soft piano and pulses", "light lo-fi beats", "warm orchestral strings", "minimal electronic",
              "acoustic plucks", "synthwave pads"],
    "host": ["none", "recurring_host", "mascot_animal", "mascot_object"],
    "intro_sting": ["name_on_board", "host_presents_title", "chapter_transition_banner"],
    "outro_sting": ["host_waves", "name_board_swings", "motif_final_state"],
}

VIDEO_TRAITS = {
    "script_shape": ["chronological story", "countdown of reasons", "mystery that opens on the ending",
                     "myth vs reality", "one day in the life", "what if escalation", "follow the money"],
    "hook": ["a shocking number", "a direct question to the viewer", "a scene already mid-action",
             "a common belief to break", "a tiny detail that turns out huge"],
    "motif": ["a map the story keeps returning to", "a counter that keeps climbing in the plates",
              "one prop that appears in every chapter", "a big chapter number stamped on each chapter's first plate",
              "a side character who reacts to every twist"],
    "thumbnail": ["face left with object right", "two characters facing off", "one huge object with a tiny character",
                  "before and after split"],
}
NO_REPEAT = ["script_shape", "hook", "motif", "thumbnail"]

MOTION = {
    "bouncy": {"spring": {"decay": 6.5, "freq": 13}, "pop": {"dur": 0.30, "c3": 2.9, "c2": 1.9},
               "kick": 0.10, "exit": 0.25, "squash": None, "camera_speed": 1.0, "sway": False},
    "snappy": {"spring": {"decay": 10, "freq": 9}, "pop": {"dur": 0.20, "c3": 2.2, "c2": 1.2},
               "kick": 0.07, "exit": 0.18, "squash": None, "camera_speed": 1.15, "sway": False},
    "floaty": {"spring": {"decay": 4.5, "freq": 8}, "pop": {"dur": 0.40, "c3": 2.5, "c2": 1.5},
               "kick": 0.08, "exit": 0.25, "squash": None, "camera_speed": 0.7, "sway": True},
    "punchy": {"spring": {"decay": 8, "freq": 14}, "pop": {"dur": 0.25, "c3": 2.9, "c2": 1.9},
               "kick": 0.16, "exit": 0.25, "squash": {"x": 1.25, "y": 0.8, "settle": 0.2},
               "camera_speed": 1.0, "sway": False},
}

def clashes(d):
    """Pares de traços que brigam. Devolve [(traço_a_re-sortear, motivo)]."""
    out = []
    host = d["host"]
    if host == "none" and d["intro_sting"] == "host_presents_title":
        out.append(("intro_sting", "sem host, ninguém pode entrar apresentando o título"))
    if host == "none" and d["outro_sting"] == "host_waves":
        out.append(("outro_sting", "sem host, ninguém pode acenar no fim"))
    if d["motion"] == "floaty" and d["camera"] == "snap_zoom":
        out.append(("camera", "Floaty com snap zoom briga: a câmera dá tranco enquanto tudo flutua"))
    if d["motion"] == "punchy" and d["music"] == "soft piano and pulses":
        out.append(("music", "squash-and-stretch pesado pede trilha com batida, não piano suave"))
    if d["font"][0] == "Fredoka" and d["narrator"] == "gravelly older storyteller":
        out.append(("font", "fonte arredondada infantil contra narrador grave e envelhecido"))
    if d["text_entry"] == "mask_slide_up" and d["shot_transition"] == "push_vertical" and d["chapter_transition"] == "shutter_5_bars":
        out.append(("shot_transition", "tudo sobe ou desce na vertical: o canal fica monótono"))
    return out

def draw_ranges(rng, d):
    m = d["motion"]
    blend = {"snappy": (0.30, 0.36), "floaty": (0.42, 0.50)}.get(m, (0.34, 0.44))
    return {
        "places_per_minute": round(rng.uniform(8, 12), 1),
        "new_thing_interval_s": round(rng.uniform(1.6, 2.4), 2),
        "shot_transition_s": round(rng.uniform(0.22, 0.28), 3),
        "card_radius": rng.randint(18, 20),
        "paper_tilt_max_rad": 0.04,
        "arm": {"L1": round(rng.uniform(0.11, 0.15), 3), "L2": round(rng.uniform(0.10, 0.14), 3),
                "thickness": round(rng.uniform(0.03, 0.05), 3)},
        "pose_blend_s": round(rng.uniform(*blend), 2),
    }

def roll_channel(seed, locks, base=None, reroll=None):
    rng = random.Random(seed)
    d = dict(base or {})
    for key, opts in CHANNEL_TRAITS.items():
        pick = rng.choice(opts)  # sempre consome o rng, para a seed continuar reproduzível
        if key in locks:
            d[key] = opts[locks[key] - 1]
        elif base is None or key == reroll:
            d[key] = pick
    notes = []
    for _ in range(2):  # no máximo 2 re-sorteios por choque
        cl = [c for c in clashes(d) if c[0] not in locks]
        if not cl:
            break
        for key, why in cl:
            old = d[key]
            d[key] = rng.choice([o for o in CHANNEL_TRAITS[key] if o != old])
            notes.append(f"re-sorteei {key}: {old!r} → {d[key]!r} ({why})")
    for key, why in clashes(d):
        notes.append(f"AVISO: o choque em {key} continua ({why}); travado ou sem saída após 2 tentativas")
    return d, notes, rng

def build_dna(seed, locks, base=None, reroll=None):
    d, notes, rng = roll_channel(seed, locks, base, reroll)
    pal = d["palette"]
    code = derive_code_colours(pal)
    dna = {
        "version": 1,
        "seed": seed,
        "rolled_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "channel": {"name": None, "slug": "canal-teste", "provisional": True},
        "traits": d,
        "palette": {"name": pal, "colors": [{"name": n, "hex": h} for n, h in PALETTES[pal]["colors"]]},
        "code_colours": code,
        "colour_check": validate_colours(code) or "ok",
        "chroma_key": chroma_key(pal),
        "motion_params": MOTION[d["motion"]],
        "ranges": draw_ranges(rng, d),
        "clash_notes": notes,
        "locks": {k: v for k, v in locks.items()},
    }
    if "fixed" in PALETTES[pal] and dna["colour_check"] != "ok":
        dna["clash_notes"].append("Dusty Dawn mantém o conjunto original por ordem do prompt, mesmo violando: "
                                  + "; ".join(dna["colour_check"]))
    return dna

# ───────────────────────── por vídeo ─────────────────────────

def roll_video(dna, seed):
    rng = random.Random(seed)
    log = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else []
    recent = log[-5:]
    picks = {}
    for key, opts in VIDEO_TRAITS.items():
        used = [v["picks"][key] for v in recent if key in v.get("picks", {})]
        # com menos de 6 opções não dá para evitar as 5 últimas: evita as len-1 mais recentes
        avoid = set(used[-(len(opts) - 1):]) if used else set()
        pool = [o for o in opts if o not in avoid] or opts
        picks[key] = rng.choice(pool)
    picks["accent"] = rng.choice(dna["palette"]["colors"])
    notes = []
    for _ in range(2):  # o destaque carrega caixa-alta branca nos banners: precisa de 4.5:1
        if contrast("#ffffff", picks["accent"]["hex"]) >= 4.5:
            break
        old = picks["accent"]["name"]
        picks["accent"] = rng.choice([c for c in dna["palette"]["colors"] if c["name"] != old])
        notes.append(f"re-sorteei accent: {old} → {picks['accent']['name']} (branco sobre {old} fica abaixo de 4.5:1)")
    if contrast("#ffffff", picks["accent"]["hex"]) < 4.5:
        picks["accent"]["banner_hex"] = darken_until((hue(picks["accent"]["hex"]), sat(picks["accent"]["hex"]) * 100, 50), "#ffffff", 4.5)
        notes.append("accent ainda claro após 2 re-sorteios: banner usa a versão escurecida")
    else:
        picks["accent"]["banner_hex"] = picks["accent"]["hex"]
    return {"seed": seed, "picks": picks, "notes": notes}

# ───────────────────────── card ─────────────────────────

def card(dna):
    t, r, c = dna["traits"], dna["ranges"], dna["code_colours"]
    w = 100
    L = ["┌" + "─" * w + "┐"]
    def row(k, v):
        s = f" {k:<20}{v}"
        L.append("│" + s[:w].ljust(w) + "│")
    row("DNA CARD", f"seed {dna['seed']}")
    L.append("├" + "─" * w + "┤")
    row("Paleta", f"{t['palette']}: " + ", ".join(x["name"] for x in dna["palette"]["colors"]))
    row("Personagens", t["character_build"])
    row("Fonte", f"{t['font'][0]} {t['font'][1]}")
    row("Cards", t["card_style"] + (f" (raio {r['card_radius']})" if t["card_style"] == "rounded_soft_shadow" else ""))
    row("HUD", t["hud"])
    row("Tag", t["tag_style"])
    row("Entrada de texto", t["text_entry"])
    row("Movimento", t["motion"])
    row("Câmera", t["camera"])
    row("Transição de shot", f"{t['shot_transition']} ({r['shot_transition_s']} s)")
    row("Transição capítulo", t["chapter_transition"])
    row("Narrador", t["narrator"])
    row("Música", t["music"])
    row("Host", t["host"])
    row("Stings", f"intro {t['intro_sting']} / outro {t['outro_sting']}")
    row("Ritmo", f"{r['places_per_minute']} lugares/min, algo novo a cada {r['new_thing_interval_s']} s")
    row("Braços", f"L1 {r['arm']['L1']}  L2 {r['arm']['L2']}  esp. {r['arm']['thickness']}  blend {r['pose_blend_s']} s")
    row("Chroma", f"{dna['chroma_key']['name']} {dna['chroma_key']['hex']}")
    L.append("├" + "─" * w + "┤")
    keys = list(c.keys())
    for i in range(0, len(keys), 3):
        row("", "   ".join(f"{k} {c[k]}" for k in keys[i:i + 3]))
    row("Checagem de cor", dna["colour_check"] if dna["colour_check"] == "ok" else "FALHA")
    L.append("└" + "─" * w + "┘")
    out = "\n".join(L)
    for n in dna["clash_notes"]:
        out += "\n  • " + n
    if dna["colour_check"] != "ok":
        out += "\n  • cor: " + "; ".join(dna["colour_check"])
    return out

def save(dna):
    DNA_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    DNA_PATH.write_text(json.dumps(dna, indent=2, ensure_ascii=False))
    bk = BACKUP_DIR / f"dna-{dna['seed']}-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"
    shutil.copy(DNA_PATH, bk)
    return bk

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int)
    ap.add_argument("--lock", action="append", default=[], help="traço=índice (1-based)")
    ap.add_argument("--reroll", help="re-sorteia só este traço do dna.json")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--card", action="store_true")
    ap.add_argument("--check-all", action="store_true", help="valida as cores das 10 paletas")
    a = ap.parse_args()
    seed = a.seed if a.seed is not None else int.from_bytes(os.urandom(8), "big")

    if a.check_all:
        bad = 0
        for name in PALETTES:
            f = validate_colours(derive_code_colours(name))
            print(f"{name:16} {'ok' if not f else f}")
            bad += bool(f) and "fixed" not in PALETTES[name]
        sys.exit(1 if bad else 0)
    if a.card:
        print(card(json.loads(DNA_PATH.read_text()))); return
    if a.video:
        dna = json.loads(DNA_PATH.read_text())
        print(json.dumps(roll_video(dna, seed), indent=2, ensure_ascii=False)); return

    locks = {}
    for item in a.lock:
        k, v = item.split("=")
        assert k in CHANNEL_TRAITS, f"traço desconhecido: {k}"
        locks[k] = int(v)
    base = None
    if a.reroll:
        assert a.reroll in CHANNEL_TRAITS, f"traço desconhecido: {a.reroll}"
        old = json.loads(DNA_PATH.read_text())
        base = old["traits"]
        locks.update(old.get("locks", {}))
    print(f"seed: {seed}")
    dna = build_dna(seed, locks, base, a.reroll)
    bk = save(dna)
    print(card(dna))
    print(f"\ndna.json: {DNA_PATH}\nbackup:   {bk}")

if __name__ == "__main__":
    main()
