#!/usr/bin/env python3
"""voice.py — narração com Kokoro (grátis) + tempos de palavra pelo faster-whisper.

- Voz escolhida a partir do narrador do DNA (tabela NARRATOR_VOICES), velocidade 1.0-1.1
  pela própria voz (nunca atempo).
- Corta pausas > 0.24 s para 0.16 s, deixa 0.5 s nas quebras de capítulo, põe 0.3 s de lead-in.
- faster-whisper sobre o áudio final → alinha com o roteiro → words.js (palavras do ROTEIRO
  com os tempos do áudio, para S('palavras exatas') achar tudo).
- Imprime o diff roteiro × transcrição.

Roteiro: texto puro; uma linha só com "##" marca quebra de capítulo.
Uso: voice.py videos/<nome> [--lang pt|en] [--voice pm_alex] [--speed 1.05]
     voice.py videos/<nome> --wav gravacao.wav     # QUALQUER voz (sua, ElevenLabs, Chatterbox…): só corta e alinha
     --pausa-max 0.24 --pausa-manter 0.16           # corte de pausas; 0.35/0.28 soa mais humano (menos "metralhadora")
"""
import argparse, difflib, json, pathlib, re, unicodedata
import numpy as np
import soundfile as sf

SR = 24000
NARRATOR_VOICES = {  # narrador do DNA → (voz en, voz pt)
    "deep warm US documentary": ("am_michael", "pm_santa"),
    "crisp British documentary": ("bm_george", "pm_alex"),
    "calm warm female documentary": ("af_heart", "pf_dora"),
    "energetic younger US explainer": ("am_puck", "pm_alex"),
    "dry deadpan storyteller": ("bm_lewis", "pm_alex"),
    "gravelly older storyteller": ("am_fenrir", "pm_santa"),
}


def norm(w):
    w = unicodedata.normalize("NFKD", w.lower())
    w = "".join(c for c in w if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", w)


def tokens(text):
    return [w for w in re.findall(r"[\wÀ-ÿ'’-]+", text) if norm(w)]


def synth(chunks, voice, lang, speed):
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="p" if lang == "pt" else "a", repo_id="hexgrad/Kokoro-82M")
    out = []
    for i, text in enumerate(chunks):
        parts = [a.numpy() if hasattr(a, "numpy") else np.asarray(a) for _, _, a in pipe(text, voice=voice, speed=speed)]
        out.append(np.concatenate(parts))
    return out


def trim_pauses(x, max_gap=0.24, keep=0.16):
    hop = int(0.01 * SR)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    thr = max(rms.max() * 0.03, 1e-4)
    silent = rms < thr
    segs, i = [], 0
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            segs.append((i, j))
            i = j
        else:
            i += 1
    keep_mask = np.ones(len(x), bool)
    for a, b in segs:
        if a == 0 or b == n:
            continue  # bordas tratadas no lead-in
        if (b - a) * 0.01 > max_gap:
            cut0 = a * hop + int(keep / 2 * SR)
            cut1 = b * hop - int(keep / 2 * SR)
            keep_mask[cut0:cut1] = False
    y = x[keep_mask]
    # apara silêncio das pontas
    nz = np.nonzero(np.abs(y) > thr)[0]
    return y[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.08 * SR)] if len(nz) else y


def align(script_words, heard):
    """heard: [(palavra, ini, fim)]. Devolve tempos para cada palavra do roteiro."""
    a = [norm(w) for w in script_words]
    b = [norm(w) for w, _, _ in heard]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(a)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k][1], heard[j1 + k][2])
        elif tag == "replace" and j2 > j1:
            # espalha as palavras do roteiro sobre o trecho ouvido (ex.: "1950" → "mil novecentos e cinquenta")
            t0, t1 = heard[j1][1], heard[j2 - 1][2]
            for k in range(i2 - i1):
                times[i1 + k] = (t0 + (t1 - t0) * k / (i2 - i1), t0 + (t1 - t0) * (k + 1) / (i2 - i1))
            diffs.append(f"roteiro {' '.join(script_words[i1:i2])!r} ≠ ouvido {' '.join(w for w,_,_ in heard[j1:j2])!r}")
        elif tag == "delete":
            diffs.append(f"não ouvido: {' '.join(script_words[i1:i2])!r}")
        elif tag == "insert":
            diffs.append(f"ouvido a mais: {' '.join(w for w,_,_ in heard[j1:j2])!r}")
    # interpola o que sobrou
    for i in range(len(times)):
        if times[i] is None:
            prev = next((times[k][1] for k in range(i - 1, -1, -1) if times[k]), 0.0)
            nxt = next((times[k][0] for k in range(i + 1, len(times)) if times[k]), prev + 0.3)
            times[i] = (prev, max(prev + 0.05, nxt))
    return times, diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--voice")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--whisper", default="small")
    ap.add_argument("--wav", help="áudio pronto (o roteiro tem de ser o mesmo texto falado)")
    ap.add_argument("--pausa-max", type=float, default=0.24); ap.add_argument("--pausa-manter", type=float, default=0.16)
    a = ap.parse_args()
    vd = pathlib.Path(a.video_dir)
    dna = json.loads((pathlib.Path(__file__).resolve().parents[1] / "dna.json").read_text())
    en, pt = NARRATOR_VOICES[dna["traits"]["narrator"]]
    voice = a.voice or (pt if a.lang == "pt" else en)
    raw = (vd / "script.txt").read_text().strip()
    chunks = [c.strip() for c in re.split(r"^\s*##.*$", raw, flags=re.M) if c.strip()]
    if a.wav:  # voz externa: um bloco só, reamostrado para 24 kHz mono
        import subprocess, tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.wav, "-ac", "1", "-ar", str(SR), tmp], check=True)
        audio = [sf.read(tmp)[0]]; print(f"voz externa: {a.wav}")
    else:
        print(f"voz: {voice} ({dna['traits']['narrator']}), velocidade {a.speed}, {len(chunks)} bloco(s)")
        audio = synth(chunks, voice, a.lang, a.speed)
    pieces = [np.zeros(int(0.3 * SR), np.float32)]
    for i, x in enumerate(audio):
        pieces.append(trim_pauses(x.astype(np.float32), a.pausa_max, a.pausa_manter))
        pieces.append(np.zeros(int((0.5 if i < len(audio) - 1 else 0.4) * SR), np.float32))
    voice_wav = np.concatenate(pieces)
    (vd / "audio").mkdir(exist_ok=True)
    sf.write(vd / "audio" / "voice.wav", voice_wav, SR)
    dur = len(voice_wav) / SR

    from faster_whisper import WhisperModel
    model = WhisperModel(a.whisper, device="cpu", compute_type="int8")
    # sem initial_prompt: com o roteiro como contexto o whisper "pula" trechos e alucina
    segs, _ = model.transcribe(str(vd / "audio" / "voice.wav"), language=a.lang, word_timestamps=True,
                               condition_on_previous_text=False, beam_size=5)
    heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    script_words = tokens(" ".join(chunks))
    times, diffs = align(script_words, heard)
    # quebras de capítulo: índice da primeira palavra de cada bloco
    starts, k = [], 0
    for c in chunks:
        starts.append(k); k += len(tokens(c))
    words = [{"w": w, "n": norm(w), "s": round(t[0], 3), "e": round(t[1], 3)} for w, t in zip(script_words, times)]
    chapters = [words[i]["s"] for i in starts]
    (vd / "words.js").write_text("window.WORDS=" + json.dumps(words, ensure_ascii=False) +
                                 f";\nwindow.CHAPTERS={json.dumps(chapters)};\nwindow.VOICE_DUR={dur:.3f};\n")
    missing = sum(len(tokens(d.split("'")[1])) for d in diffs if d.startswith("não ouvido"))
    if missing > 0.05 * len(script_words):
        raise SystemExit(f"FALHA: {missing} de {len(script_words)} palavras do roteiro não foram ouvidas; refaça a voz")
    print(f"duração {dur:.2f} s, {len(words)} palavras, {len(script_words)/dur*60:.0f} palavras/min")
    print("diff roteiro × whisper:", "nenhum" if not diffs else "")
    for d in diffs:
        print("  -", d)


if __name__ == "__main__":
    main()
