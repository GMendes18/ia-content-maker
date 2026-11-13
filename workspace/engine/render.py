#!/usr/bin/env python3
"""render.py — renderiza videos/<nome>/index.html em MP4 (30 fps, 4 subframes de motion blur).

  render.py videos/<nome> --stills 1.0,2.5,4      # PNGs para conferir
  render.py videos/<nome> --contact                # contact sheet, um frame a cada 2 s
  render.py videos/<nome>                          # vídeo (sem áudio) → build/video.mp4
  render.py videos/<nome> --parts 4                # 4 páginas em paralelo, junta no fim
Também grava build/ev.json (eventos de som) e build/timeline.json.
"""
import argparse, functools, http.server, json, math, pathlib, subprocess, sys, threading, time
from concurrent.futures import ProcessPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS = 30
FMT = {"landscape": ("index.html", "build", 1920, 1080), "vertical": ("index_vertical.html", "build_vertical", 1080, 1920)}


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def open_page(p, port, vd, fmt="landscape"):
    page, _, SW, SH = FMT[fmt]
    from playwright.sync_api import sync_playwright  # noqa
    b = p.chromium.launch(args=["--disable-gpu-vsync", "--disable-frame-rate-limit"])
    pg = b.new_page(viewport={"width": SW, "height": SH})
    pg.SIZE = (SW, SH)
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    url = f"http://127.0.0.1:{port}/{vd.relative_to(ROOT)}/{page}?t=0"
    pg.goto(url)
    pg.wait_for_function("window.READY === true || window.BOOT_ERROR", timeout=60000)
    err = pg.evaluate("window.BOOT_ERROR || null")
    if err or errors:
        raise SystemExit(f"erro na página: {err or ''} {errors}")
    return b, pg


def shot(pg, t, blur=True):
    pg.evaluate(f"renderBlur({t})" if blur else f"seek({t})")
    return pg.screenshot(type="png", clip={"x": 0, "y": 0, "width": pg.SIZE[0], "height": pg.SIZE[1]})


def render_part(args):
    vd, port, f0, f1, out, crf, fmt = args
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b, pg = open_page(p, port, pathlib.Path(vd), fmt)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", str(out)],
                              stdin=subprocess.PIPE)
        for f in range(f0, f1):
            ff.stdin.write(shot(pg, f / FPS))
        ff.stdin.close(); ff.wait(); b.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir")
    ap.add_argument("--stills"); ap.add_argument("--contact", action="store_true")
    ap.add_argument("--format", default="landscape", choices=list(FMT))
    ap.add_argument("--parts", type=int, default=1); ap.add_argument("--crf", type=int, default=17)
    a = ap.parse_args()
    vd = pathlib.Path(a.video_dir).resolve()
    build = vd / FMT[a.format][1]; build.mkdir(exist_ok=True)
    srv, port = serve()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b, pg = open_page(p, port, vd, a.format)
        END = pg.evaluate("END")
        (build / "ev.json").write_text(json.dumps(pg.evaluate("EV")))
        (build / "timeline.json").write_text(json.dumps({"END": END, "CUTS": pg.evaluate("CUTS"), "SHOTS": pg.evaluate("SHOTS"), "VOICE_OFFSET": pg.evaluate("VOICE_OFFSET"), "VOICE_END": pg.evaluate("VOICE_END")}, indent=1))
        if a.stills:
            for t in [float(x) for x in a.stills.split(",")]:
                (build / f"still_{t:06.2f}.png").write_bytes(shot(pg, t))
            print("stills em", build); return
        if a.contact:
            from PIL import Image, ImageDraw
            import io
            ts = [i * 2.0 for i in range(int(END // 2) + 1)]
            tw, th = (480, 270) if a.format == "landscape" else (243, 432)
            ims = [Image.open(io.BytesIO(shot(pg, t, blur=False))).resize((tw, th)) for t in ts]
            cols = 4 if a.format == "landscape" else 8; rows = math.ceil(len(ims) / cols)
            sheet = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 30) + 10), (25, 25, 25))
            for i, (im, t) in enumerate(zip(ims, ts)):
                x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 30)
                sheet.paste(im, (x, y)); ImageDraw.Draw(sheet).text((x + 4, y + th + 4), f"{t:.1f}s", fill=(255, 255, 255))
            sheet.save(build / "contact.png"); print("contact:", build / "contact.png"); return
        b.close()
    N = int(math.ceil(END * FPS))
    k = max(1, a.parts)
    bounds = [(round(i * N / k), round((i + 1) * N / k)) for i in range(k)]
    jobs = [(str(vd), port, f0, f1, build / f"part{i}.mp4", a.crf, a.format) for i, (f0, f1) in enumerate(bounds)]
    t0 = time.time()
    if k == 1:
        render_part(jobs[0])
    else:
        with ProcessPoolExecutor(k) as ex:
            list(ex.map(render_part, jobs))
    lst = build / "parts.txt"
    lst.write_text("".join(f"file '{j[4].name}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(build / "video.mp4")], check=True)
    print(f"vídeo: {build/'video.mp4'} ({N} frames, {time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
