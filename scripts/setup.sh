#!/usr/bin/env bash
# setup.sh — cria (ou atualiza) um workspace da máquina de vídeos.
#   bash scripts/setup.sh [PASTA_DO_WORKSPACE]      (padrão: ~/ia-content-workspace)
# Novo workspace: copia engine/, templates/, exemplos/, library/ e cria .venv com tudo instalado.
# Workspace existente: ATUALIZA só engine/ e templates/ (nunca toca em dna.json, videos/ ou library/).
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
WS="${1:-$HOME/ia-content-workspace}"
mkdir -p "$WS"
if [ -f "$WS/dna.json" ] || [ -d "$WS/engine" ]; then
  echo "workspace existente: atualizando engine/ e templates/ em $WS"
  rsync -a --exclude __pycache__ --exclude '*.ttf' "$SKILL/workspace/engine" "$SKILL/workspace/templates" "$WS/"
else
  echo "novo workspace em $WS"
  rsync -a "$SKILL/workspace/" "$WS/"
  mkdir -p "$WS/videos"
fi
command -v ffmpeg >/dev/null || { echo "FALTA ffmpeg (ex.: sudo apt install ffmpeg / brew install ffmpeg)"; exit 1; }
PY="${PYTHON:-python3}"
if [ ! -x "$WS/.venv/bin/python" ]; then
  if ! "$PY" -m venv "$WS/.venv" 2>/dev/null; then
    echo "python3-venv ausente: criando venv sem pip e instalando o pip à parte"
    "$PY" -m venv --without-pip "$WS/.venv"
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$WS/.venv/bin/python"
  fi
fi
V="$WS/.venv/bin/python"
"$V" -m pip install -q --upgrade pip
"$V" -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
"$V" -m pip install -q -r "$SKILL/scripts/requirements.txt"
"$V" -m playwright install chromium
[ -f "$WS/dna.json" ] && "$V" "$WS/engine/fonts.py" || true
echo
echo "pronto. Workspace: $WS"
echo "próximo passo (uma vez por canal):  cd \"$WS\" && .venv/bin/python engine/mv.py dna"
