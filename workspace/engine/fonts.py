#!/usr/bin/env python3
"""fonts.py — garante o .ttf da fonte do DNA em engine/fonts/ (baixa do Google Fonts se faltar).
Uso: fonts.py            (lê dna.json)      |   fonts.py "Anton" 400
A API css2 devolve links .ttf para clientes simples; o arquivo vira engine/fonts/<NomeSemEspaços>.ttf
(é o caminho que build_page.py procura). Fontes do Google Fonts são OFL: podem ser redistribuídas.
"""
import json, pathlib, re, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIR = ROOT / "engine" / "fonts"


def ensure(family, weight):
    out = DIR / (family.replace(" ", "") + ".ttf")
    if out.exists() and out.stat().st_size > 10000:
        return out
    DIR.mkdir(parents=True, exist_ok=True)
    q = urllib.parse.quote(family) + f":wght@{weight}"
    req = urllib.request.Request(f"https://fonts.googleapis.com/css2?family={q}", headers={"User-Agent": "curl/8"})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    url = re.search(r"url\((https://[^)]+\.ttf)\)", css)
    if not url:
        raise SystemExit(f"não achei .ttf para {family} {weight} no Google Fonts")
    out.write_bytes(urllib.request.urlopen(url.group(1), timeout=60).read())
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fam, w = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 800
    else:
        fam, w = json.loads((ROOT / "dna.json").read_text())["traits"]["font"]
    print("fonte:", ensure(fam, w))
