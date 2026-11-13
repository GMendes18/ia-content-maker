#!/usr/bin/env python3
"""qc.py — varre o vídeo final atrás de saltos de um frame e confere se cada um é um corte planejado.
Uso: qc.py videos/<nome>
"""
import json, pathlib, subprocess, sys
import numpy as np

vd = pathlib.Path(sys.argv[1]); FPS = 30
BD = sys.argv[2] if len(sys.argv) > 2 else "build"  # build | build_vertical
tl = json.loads((vd / BD / "timeline.json").read_text())
planned = [s["start"] for s in tl["SHOTS"][1:]]  # todo início de shot (corte, transição ou capítulo)
w, h = 192, 108
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(vd / BD / "video.mp4"), "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
med = np.median(d) + 1e-3
# salto = pico ISOLADO: muito maior que os dois vizinhos (movimento rápido contínuo não conta)
big = (d > 6 * med) & (d > 8)
iso = [i for i in np.nonzero(big)[0] if d[i] > 3 * max(d[i - 1] if i > 0 else 0, d[i + 1] if i + 1 < len(d) else 0, 1e-3)]
jumps = [(i + 1) / FPS for i in iso]
unplanned = [t for t in jumps if not any(abs(t - p) < 0.3 for p in planned)]


def quiet_stretches(events, shot_starts, end, interval):
    """Trechos em que NADA novo chega por mais de 2x o intervalo do DNA.
    events: [{"t": s, "name": "pop"|"tick"|"whoosh"|...}], shot_starts: [s], end: duração.
    Devolve [(t0, t1), ...] com cada trecho parado longo demais."""
    # TODO(human)
    raise NotImplementedError


dna = json.loads((pathlib.Path(__file__).resolve().parents[1] / "dna.json").read_text())
ev = json.loads((vd / BD / "ev.json").read_text())
try:
    q = quiet_stretches(ev, [s["start"] for s in tl["SHOTS"]], tl["END"], dna["ranges"]["new_thing_interval_s"])
    print(f"trechos parados (> {2 * dna['ranges']['new_thing_interval_s']:.1f} s): {[(round(a, 2), round(b, 2)) for a, b in q] or 'nenhum'}")
except NotImplementedError:
    print("trechos parados: checagem pendente (TODO(human) em engine/qc.py)")
print(f"{len(fr)} frames; saltos: {len(jumps)}; planejados: {len(jumps) - len(unplanned)}; NÃO planejados: {[round(t, 2) for t in unplanned]}")
sys.exit(1 if unplanned else 0)
