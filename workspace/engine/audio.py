#!/usr/bin/env python3
"""audio.py — trilha, efeitos, ducking, gate de inteligibilidade, loudnorm e mux final.

TRILHA: o prompt pede 2-3 beds do Pixabay na família do DNA. Sem download automático,
este módulo SINTETIZA um bed na família do DNA (light lo-fi beats etc.) como substituto;
para usar beds reais, ponha .mp3/.wav em library/music/<família>/ e eles têm prioridade.
SFX: idem — library/sfx/<nome>.wav tem prioridade sobre o sintetizado.

Mix: voz por cima; música com ducking (ataque 30 ms, hold 0.3 s, release 0.45 s);
SFX alinhados pelo PICO no instante do evento, 6 dB mais baixos durante a fala.
Gate: na fala, voz >= 15 dB acima de música+SFX (mediana de frames de 100 ms) e
fundo mais alto que a voz em < 1% dos frames. Se falhar, baixa o fundo e refaz.
Loudnorm em duas passadas: -14 LUFS, true peak -1 dB.

Uso: audio.py videos/<nome>   (precisa de audio/voice.wav, build/ev.json, build/video.mp4)
"""
import json, pathlib, re, subprocess, sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

SR = 48000
ROOT = pathlib.Path(__file__).resolve().parents[1]
rng = np.random.default_rng(7)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-9))


def lp(x, f, o=4):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=4):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def bp(x, f0, f1, o=2):
    return sosfilt(butter(o, [f0, f1], "band", fs=SR, output="sos"), x)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


# ───────────────────────── SFX sintetizados ─────────────────────────
def sfx_bank(personality):
    n = lambda s: int(s * SR)
    t = lambda s: np.arange(n(s)) / SR
    snap = {"snappy": 0.8, "floaty": 1.3, "punchy": 0.9}.get(personality, 1.0)
    b = {}
    tt = t(0.09 * snap); f = 950 * np.exp(-tt * 28) + 300
    b["pop"] = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.002, 0.03 * snap)
    x = rng.standard_normal(n(0.32)); sweep = np.linspace(300, 3200, len(x))
    w = np.zeros_like(x)
    for i in range(0, len(x), 512):  # varredura de banda em blocos
        seg = x[i:i + 512]; c = sweep[min(i, len(x) - 1)]
        w[i:i + 512] = bp(seg, c * 0.7, min(c * 1.4, 20000))
    shape = np.sin(np.pi * np.linspace(0, 1, len(x))) ** 2
    b["whoosh"] = w * shape * 2.2
    b["tick"] = hp(rng.standard_normal(n(0.012)), 3000) * env(n(0.012), 0.0005, 0.003) * 0.5
    tt = t(0.35); b["thud"] = (np.sin(2 * np.pi * 70 * tt) * env(len(tt), 0.002, 0.09) + lp(rng.standard_normal(len(tt)), 400) * env(len(tt), 0.001, 0.03) * 0.6)
    tt = t(0.2); b["hit"] = (lp(rng.standard_normal(len(tt)), 2500) * env(len(tt), 0.001, 0.04) + np.sin(2 * np.pi * 180 * tt) * env(len(tt), 0.001, 0.06)) * 0.8
    tt = t(0.8); b["ding"] = (np.sin(2 * np.pi * 1320 * tt) + 0.4 * np.sin(2 * np.pi * 2640 * tt)) * env(len(tt), 0.002, 0.25) * 0.5
    tt = t(0.25); b["splat"] = lp(rng.standard_normal(len(tt)), 900) * env(len(tt), 0.004, 0.06)
    tt = t(0.3); b["puff"] = bp(rng.standard_normal(len(tt)), 400, 2500) * env(len(tt), 0.02, 0.08) * 0.6
    for k, v in b.items():
        p = ROOT / "library" / "sfx" / f"{k}.wav"
        if p.exists():
            y, sr = sf.read(p, always_2d=True); y = y.mean(1)
            b[k] = resample_poly(y, SR, sr) if sr != SR else y
        b[k] = b[k] / (np.abs(b[k]).max() + 1e-9)
    return b


# ───────────────────────── trilha ─────────────────────────
def place(buf, s, y):
    """Soma y em buf a partir da amostra s, cortando o que cair fora."""
    if s >= len(buf) or s + len(y) <= 0:
        return
    a, b = max(0, s), min(len(buf), s + len(y))
    buf[a:b] += y[a - s:b - s]


def rhodes(freq, dur, vel=0.3):
    tt = np.arange(int(dur * SR)) / SR
    mod = np.sin(2 * np.pi * freq * 2 * tt) * 1.2 * np.exp(-tt * 3)
    return vel * np.sin(2 * np.pi * freq * tt + mod) * np.exp(-tt * 1.6) * np.minimum(1, tt / 0.005)


def synth_lofi(dur, bpm=78):
    """light lo-fi beats: acordes de piano elétrico, kick, snare abafado, hats, chiado de vinil."""
    N = int(dur * SR); out = np.zeros(N + SR * 4)
    beat = 60 / bpm
    chords = [[48, 55, 59, 64], [45, 52, 55, 60], [50, 57, 60, 65], [43, 50, 53, 59]]  # Cmaj7 Am7 Dm7 G7(ish)
    mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
    swing = 0.06 * beat
    bar = 0
    while bar * 4 * beat < dur + 2:
        t0 = bar * 4 * beat; ch = chords[bar % 4]
        for k, m in enumerate(ch):
            s = int((t0 + k * 0.012) * SR); y = rhodes(mtof(m + 12), 4 * beat, 0.11)
            place(out, s, y)
        for b4 in range(4):
            tb = t0 + b4 * beat
            if b4 in (0, 2) or (b4 == 3 and bar % 2):
                s = int((tb + (0.5 * beat if b4 == 3 else 0)) * SR); tt = np.arange(int(0.25 * SR)) / SR
                k_ = np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14) * 0.5
                place(out, s, k_)
            if b4 in (1, 3):
                s = int(tb * SR); n_ = lp(bp(rng.standard_normal(int(0.2 * SR)), 900, 5000), 3500) * env(int(0.2 * SR), 0.001, 0.05) * 0.22
                place(out, s, n_)
            for h in (0, 1):
                s = int((tb + h * (beat / 2 + swing)) * SR); n_ = hp(rng.standard_normal(int(0.05 * SR)), 7000) * env(int(0.05 * SR), 0.0005, 0.012) * 0.07
                place(out, s, n_)
        bar += 1
    out = out[:N]
    crackle = (rng.random(N) > 0.9993) * rng.standard_normal(N) * 0.08 + lp(rng.standard_normal(N), 3000) * 0.004
    out = lp(out, 5200) + crackle
    fade = int(1.2 * SR); out[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR)); out[-fade:] *= np.linspace(1, 0, fade)
    return out / (np.abs(out).max() + 1e-9)


def music_bed(dna, dur):
    fam = dna["traits"]["music"]
    lib = ROOT / "library" / "music" / re.sub(r"\W+", "_", fam)
    files = sorted(list(lib.glob("*.wav")) + list(lib.glob("*.mp3"))) if lib.exists() else []
    if files:
        y, sr = sf.read(files[0], always_2d=True); y = y.mean(1)
        y = resample_poly(y, SR, sr) if sr != SR else y
        reps = int(np.ceil(dur * SR / len(y))); return np.tile(y, reps)[: int(dur * SR)], f"biblioteca: {files[0].name}"
    return synth_lofi(dur), f"sintetizado ({fam})"


# ───────────────────────── mix ─────────────────────────
def voice_activity(v, win=0.02):
    hop = int(win * SR); n = len(v) // hop
    r = np.sqrt(np.mean(v[: n * hop].reshape(n, hop) ** 2, 1))
    act = r > max(r.max() * 0.04, 1e-4)
    a = np.repeat(act, hop).astype(float)
    return np.pad(a, (0, len(v) - len(a)), mode='edge')[: len(v)], hop


def duck_env(act, depth_db=-15, attack=0.03, hold=0.3, release=0.45):
    """1 = música cheia; cai depth_db sob a voz."""
    n = len(act); g = np.ones(n); target_low = 10 ** (depth_db / 20)
    # hold: estende a atividade
    h = int(hold * SR); idx = np.nonzero(act > 0)[0]
    held = np.zeros(n)
    if len(idx):
        held[idx] = 1
        last = -10 ** 9
        for i in range(n):  # simples e determinístico
            if held[i]:
                last = i
            elif i - last < h:
                held[i] = 1
    a_c = np.exp(-1 / (attack * SR)); r_c = np.exp(-1 / (release * SR))
    cur = 1.0
    for i in range(n):
        tgt = target_low if held[i] else 1.0
        c = a_c if tgt < cur else r_c
        cur = tgt + (cur - tgt) * c
        g[i] = cur
    return g


def frames_db(x, win=0.1):
    hop = int(win * SR); n = len(x) // hop
    return db(np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, 1) + 1e-12))


def main(vd, bd="build"):  # bd = build | build_vertical
    vd = pathlib.Path(vd)
    dna = json.loads((ROOT / "dna.json").read_text())
    tl = json.loads((vd / bd / "timeline.json").read_text())
    ev = json.loads((vd / bd / "ev.json").read_text())
    v, sr = sf.read(vd / "audio" / "voice.wav")
    v = resample_poly(v, SR, sr) if sr != SR else v
    dur = tl["END"]; N = int(dur * SR) + 1
    off = int(tl.get("VOICE_OFFSET", 0) * SR)
    voice = np.zeros(N); n_ = min(N - off, len(v)); voice[off:off + n_] = v[:n_]
    voice /= np.abs(voice).max() + 1e-9
    act, _ = voice_activity(voice)
    music, src = music_bed(dna, dur)
    music = music[:N] if len(music) >= N else np.pad(music, (0, N - len(music)))
    bank = sfx_bank(dna["traits"]["motion"])
    sfx = np.zeros(N)
    for e in ev:
        y = bank.get(e["name"]);
        if y is None: continue
        peak = int(np.argmax(np.abs(y)))
        s = int(e["t"] * SR) - peak
        g = 10 ** ((e.get("gain", 0) - (6 if act[min(max(0, int(e['t'] * SR)), N - 1)] else 0)) / 20)
        a0, b0 = max(0, s), min(N, s + len(y))
        if b0 > a0: sfx[a0:b0] += y[a0 - s:b0 - s] * g
    duck = duck_env(act)
    m_gain, s_gain = 10 ** (-10 / 20), 10 ** (-12 / 20)
    hop = int(0.1 * SR)
    ok = False
    for attempt in range(10):
        bg = music * duck * m_gain + sfx * s_gain
        vf, bf = frames_db(voice), frames_db(bg)
        # frame de fala = VAD ativo em mais da metade do frame (micro-pausas entre palavras não contam)
        nf = len(vf); speech = act[: nf * hop].reshape(nf, hop).mean(1) > 0.5
        margin = float(np.median(vf[speech] - bf[speech]))
        bad = np.nonzero(speech & (bf > vf))[0]
        louder = len(bad) / max(1, speech.sum()) * 100
        print(f"gate: voz {margin:.1f} dB acima do fundo (mín 15), fundo mais alto em {louder:.2f}% dos frames de fala (máx 1%)")
        if margin >= 15 and louder < 1:
            ok = True; break
        if margin < 15:
            m_gain *= 10 ** (-2 / 20); s_gain *= 10 ** (-2 / 20); print("  → fundo inteiro -2 dB")
        for f in bad:  # só o trecho culpado: SFX daquele frame -3 dB
            a0, b0 = max(0, (f - 1) * hop), min(N, (f + 2) * hop); sfx[a0:b0] *= 0.7
        if len(bad): print(f"  → SFX -3 dB em {len(bad)} frame(s) de fala")
    if not ok:
        print("AVISO: o gate de inteligibilidade NÃO passou; revise o mix antes de publicar")
    mix = voice + bg
    mix /= np.abs(mix).max() + 1e-9
    out = vd / bd; sf.write(out / "mix_raw.wav", mix * 0.9, SR, subtype="PCM_24")

    def measure(path):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "loudnorm=I=-14:TP=-1:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
        return json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    # 2 passadas: mede → ganho + limitador (TP -1 dB) → mede; corrige uma vez se o limitador comeu loudness
    m = measure(out / "mix_raw.wav"); gain = -14 - float(m["input_i"])
    for _ in range(3):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "mix_raw.wav"), "-af",
                        f"volume={gain:.2f}dB,alimiter=limit={10 ** (-1.9 / 20):.4f}:attack=3:release=60:level=false",
                        "-ar", str(SR), str(out / "mix.wav")], check=True)
        m2 = measure(out / "mix.wav")
        err = -14 - float(m2["input_i"])
        if abs(err) < 0.3 and float(m2["input_tp"]) <= -1.0:
            break
        gain += err
    final = vd / (f"{vd.name}_vertical.mp4" if bd == "build_vertical" else f"{vd.name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "video.mp4"), "-i", str(out / "mix.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)], check=True)
    print(f"trilha: {src}; {len(ev)} efeitos; final {m2['input_i']} LUFS, true peak {m2['input_tp']} dB")
    print("final:", final)


if __name__ == "__main__":
    main(sys.argv[1], *(sys.argv[2:3]))
