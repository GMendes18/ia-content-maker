# ia-content-maker

Skill white label que transforma um agente de IA com terminal numa máquina de vídeos explicativos
animados (flat vector 2D, 1–10 min, vertical 9:16 ou 16:9), do roteiro ao MP4 — sem vídeo gerado por
IA: todo movimento é código. A identidade visual de cada canal é sorteada (DNA), então cada canal sai
diferente, para qualquer tema.

## O que sai
- Vídeo MP4 com narração (Kokoro grátis ou qualquer voz gravada), trilha, efeitos, legendas no vertical.
- Capa/thumbnail, legenda do post com hashtags, log do canal para não repetir fórmulas.

## Requisitos
Linux ou macOS, Python ≥ 3.10, ffmpeg, ~3 GB livres (torch CPU + Chromium). Sem GPU.

## Instalar
```bash
git clone <este repositório> ia-content-maker
bash ia-content-maker/scripts/setup.sh ~/ia-content-workspace
```

## Usar em cada IA
| Ferramenta | Como |
|---|---|
| Claude Code | `ln -s "$PWD/ia-content-maker" ~/.claude/skills/ia-content-maker` → peça "faz um vídeo: …" |
| Codex CLI | `ln -s "$PWD/ia-content-maker" ~/.codex/skills/ia-content-maker` (ou abra o repo: `AGENTS.md`) |
| Gemini CLI | abra o repo como pasta de trabalho (`GEMINI.md`) |
| Cursor / outras | anexe `SKILL.md` ao contexto e peça para seguir |

Precisa ser um agente que **executa comandos** (o pipeline roda Python, Chromium e ffmpeg).
Chat sem terminal só consegue fazer roteiro e plano.

## Primeiro canal
```
faz o setup do canal          → sorteia o DNA (paleta, fonte, traço, transições, narrador…)
faz um vídeo: [tema], 60s     → roteiro (para aprovação) → arte → voz → animação → render → capa
```

## Estrutura
```
SKILL.md                  playbook (o agente segue isto)
referencia/               API do motor, retenção, lições, especificação original
scripts/setup.sh          instala/atualiza um workspace
workspace/engine/         motor (Python + JS)       workspace/templates/  modelos por vídeo
workspace/exemplos/       dois vídeos completos      workspace/library/    trilhas, efeitos, log
```

## Licenças de terceiros
Kokoro-82M (Apache-2.0), faster-whisper (MIT), Playwright (Apache-2.0), fontes do Google Fonts (OFL).
Para vozes clonadas/comerciais, confira a licença do modelo escolhido.
