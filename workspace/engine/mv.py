#!/usr/bin/env python3
"""mv.py — a máquina de vídeos em um comando por etapa (qualquer IA ou pessoa consegue operar).

  python engine/mv.py dna [--lock build=3 ...]      # canal: sorteia o DNA (uma vez) + baixa a fonte
  python engine/mv.py cartao                         # mostra o cartão do DNA
  python engine/mv.py novo <slug>                    # vídeo: pasta + modelos + sorteio por vídeo (picks.json)
  python engine/mv.py arte <slug>                    # plates/tiles/sheets → recorte → rig (lê art.json)
  python engine/mv.py voz <slug> [--wav x.wav] [--pausa-max .35 --pausa-manter .28]
  python engine/mv.py contato <slug> [--formato vertical|paisagem]
  python engine/mv.py stills <slug> 0,3.5,10 [--formato ...]
  python engine/mv.py render <slug> [--formato ...] [--partes 4]   # vídeo + áudio + QC
  python engine/mv.py capa <slug>                    # thumbnail/capa pelo thumb.json
  python engine/mv.py log <slug>                     # registra em library/log.json

Formato padrão: vertical (Reels/TikTok/Shorts). "paisagem" = 1920x1080 (YouTube).
"""
import json, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = ROOT / "engine"
PY = sys.executable
FMT = {"vertical": ("vertical", "build_vertical"), "paisagem": ("landscape", "build")}


def run(*args):
    print("→", " ".join(str(a) for a in args[1:]))
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT)


def opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return v
    return default


def vdir(slug):
    d = ROOT / "videos" / slug
    if not d.exists():
        raise SystemExit(f"não existe {d} — rode: mv.py novo {slug}")
    return d


def main(argv):
    if not argv:
        print(__doc__); return
    cmd, argv = argv[0], argv[1:]
    if cmd == "dna":
        if (ROOT / "dna.json").exists() and "--forcar" not in argv:
            raise SystemExit("dna.json já existe (o canal é congelado). Use --forcar para sortear outro, ou "
                             "'python engine/roll_dna.py --reroll <traço>' para trocar um traço só.")
        argv = [a for a in argv if a != "--forcar"]
        run(PY, E / "roll_dna.py", *argv); run(PY, E / "fonts.py"); return
    if cmd == "cartao":
        run(PY, E / "roll_dna.py", "--card"); return
    if not (ROOT / "dna.json").exists():
        raise SystemExit("sem dna.json: rode primeiro  python engine/mv.py dna")
    slug = argv.pop(0) if argv else None
    if not slug:
        raise SystemExit("falta o <slug> do vídeo")
    fmt, bd = FMT[opt(argv, "--formato", "vertical")]

    if cmd == "novo":
        d = ROOT / "videos" / slug
        if d.exists():
            raise SystemExit(f"{d} já existe")
        (d / "shots").mkdir(parents=True)
        T = ROOT / "templates"
        shutil.copy(T / "video.json", d / "video.json"); shutil.copy(T / "art.json", d / "art.json")
        shutil.copy(T / "thumb.json", d / "thumb.json"); shutil.copy(T / "shots_modelo.js", d / "shots" / "01_story.js")
        out = subprocess.run([PY, E / "roll_dna.py", "--video"], capture_output=True, text=True, check=True, cwd=ROOT).stdout
        r = json.loads(out)
        picks = {"seed": r["seed"], **r["picks"], "notes": r.get("notes", [])}
        (d / "picks.json").write_text(json.dumps(picks, indent=1, ensure_ascii=False))
        print(json.dumps(picks, indent=1, ensure_ascii=False))
        print(f"\npronto: {d}\nescreva {d/'script.txt'} (ver templates/roteiro_modelo.md), depois art.json e os shots.")
        return
    d = vdir(slug)
    if cmd == "arte":
        run(PY, E / "art" / "make_art.py", d)
        chars = json.loads((d / "art.json").read_text()).get("characters", {})
        for c in chars:
            run(PY, E / "cutout.py", d / "art" / f"{c}_base.png", d / "sprites", "--names",
                ",".join(f"{c}_{v}" for v in ("front", "front_alt", "side", "back", "pose_pockets", "pose_sitting")))
            run(PY, E / "rig.py", d / "sprites", c, "--front", f"{c}_front", "--alt", f"shocked={c}_front_alt",
                "--extra", f"side={c}_side", "--extra", f"back={c}_back", "--extra", f"pockets={c}_pose_pockets",
                "--extra", f"sitting={c}_pose_sitting")
        print(f"confira: {d/'art'/'contact_art.png'} e {d/'sprites'}/contact_*.png"); return
    if cmd == "voz":
        run(PY, E / "voice.py", d, *argv); return
    if cmd in ("contato", "stills", "render"):
        run(PY, E / "build_page.py", d, "--format", fmt)
        if cmd == "contato":
            run(PY, E / "render.py", d, "--format", fmt, "--contact"); return
        if cmd == "stills":
            run(PY, E / "render.py", d, "--format", fmt, "--stills", argv[0]); return
        run(PY, E / "render.py", d, "--format", fmt, "--parts", opt(argv, "--partes", "4"))
        run(PY, E / "audio.py", d, bd)
        run(PY, E / "qc.py", d, bd); return
    if cmd == "capa":
        run(PY, E / "thumbnail.py", d, d / "thumb.json"); return
    if cmd == "log":
        log = ROOT / "library" / "log.json"; L = json.loads(log.read_text()) if log.exists() else []
        p = json.loads((d / "picks.json").read_text())
        vids = sorted(d.glob("*.mp4"))
        dur = None
        if vids:
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", vids[-1]],
                                       capture_output=True, text=True).stdout or 0)
        topic = json.loads((d / "video.json").read_text()).get("topic", slug)
        import datetime
        L.append({"topic": topic, "slug": slug, "length_s": round(dur or 0, 1), "date": datetime.date.today().isoformat(),
                  "format": fmt, "seed": p.get("seed"),
                  "picks": {k: p.get(k) for k in ("script_shape", "hook", "motif", "thumbnail")} | {"accent": (p.get("accent") or {}).get("name")},
                  "files": [str(v.relative_to(ROOT)) for v in vids]})
        log.write_text(json.dumps(L, indent=2, ensure_ascii=False)); print(f"{len(L)} vídeo(s) no log"); return
    raise SystemExit(f"comando desconhecido: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv[1:])
