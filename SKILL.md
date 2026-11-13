---
name: ia-content-maker
description: Máquina de vídeos explicativos animados (flat vector, 2D, tudo em código) de 1–10 min, do roteiro ao MP4, com identidade de canal sorteada (DNA) e formato vertical para Reels/TikTok/Shorts ou 16:9 para YouTube. Use quando o usuário pedir "faz um vídeo sobre X", "make a video: [tema], [duração]", um short/reel animado, um vídeo explicativo, um novo canal de vídeos com IA, ou quiser criar/ajustar o DNA de um canal.
---

# IA Content Maker — máquina de vídeos white label

Esta skill transforma o agente na equipe inteira de um canal de vídeos explicativos: roteiro,
arte, recorte e rig dos personagens, voz, animação, trilha, render, capa e legenda. Todo movimento é
código (canvas renderizado frame a frame); não há vídeo gerado por IA.

**White label:** a identidade do canal (paleta, fonte, traço, cards, transições, ritmo, narrador)
é SORTEADA por código uma vez por canal e gravada em `dna.json`. Dois canais com a mesma skill saem
diferentes. Nada no motor depende de uma paleta, fonte ou tema específico.

Funciona em qualquer agente que rode comandos de terminal (Claude Code, Codex, Gemini CLI, Cursor…).
A especificação completa original está em `referencia/especificacao-original.md`; este arquivo traz
o fluxo validado e tudo que mudou com a prática. Em conflito, **este arquivo vence**.

## 0. Antes de tudo: achar ou criar o workspace

O código roda num *workspace* (pasta com `engine/`, `dna.json`, `videos/`, `library/`).

1. Procure um workspace existente (um `dna.json` ao lado de `engine/mv.py`; o usuário pode dizer onde).
2. Se não houver: `bash <pasta-da-skill>/scripts/setup.sh [pasta]` (padrão `~/ia-content-workspace`).
   Instala venv, Kokoro, faster-whisper, Playwright/Chromium, OpenCV. Precisa de Python ≥3.10 e ffmpeg.
3. Se houver mas a skill for mais nova: rode o mesmo `setup.sh <workspace>` — ele atualiza só
   `engine/` e `templates/`, nunca `dna.json`, `videos/` ou `library/`.

Todos os comandos abaixo são rodados DENTRO do workspace, com `.venv/bin/python` (aqui: `py`).

## 1. Setup do canal (uma vez)

1. Pergunte: nome do canal (se não tiver, sugira 5 que combinem com o DNA depois do sorteio),
   formato principal (vertical ou 16:9), voz disponível (Kokoro grátis, ElevenLabs/outra, ou a
   própria voz gravada) e se já existe um `dna.json` (se sim, copie para o workspace).
2. `py engine/mv.py dna` — sorteia o DNA com seed de `os.urandom`, resolve combinações que brigam,
   valida contraste das cores, grava `dna.json` + backup e baixa a fonte. Mostre o cartão
   (`py engine/mv.py cartao`). O usuário pode travar (`--lock traço=índice`) ou re-sortear um traço
   (`py engine/roll_dna.py --reroll <traço>`). **Nunca escolha traços na mão.**
3. Grave o nome em `dna.json` → `channel.name`.
4. Rota de arte sem modelo de imagem: só o traço "Chunky rounded-square heads" está desenhado em
   código (`engine/art/characters.py`). Se o sorteio der outro traço, ou trave `--lock build=3`, ou
   implemente o traço novo em `characters.py` seguindo `_head/_torso/_legs`, ou use modelo de imagem.
5. Depois do setup o DNA do canal é congelado. Cada vídeo só re-sorteia os traços por vídeo.

## 2. Cada vídeo — o fluxo

Comando de partida do usuário: **"faz um vídeo: [tema], [duração]"** (ou "make a video: …").

| # | Etapa | Comando | Pare e mostre ao usuário? |
|---|---|---|---|
| 1 | Pasta + sorteio por vídeo (forma do roteiro, gancho, motivo, layout de capa, destaque) | `py engine/mv.py novo <slug>` | — |
| 2 | Roteiro em `videos/<slug>/script.txt` (texto puro) + números do plano (palavras, lugares, personagens) | escrever | **SIM: roteiro + picks, espere OK** |
| 3 | `art.json` + plates/tiles novos em `engine/art/plates.py` e `tiles.py` se o tema pedir | escrever | — |
| 4 | Arte → recorte → rig | `py engine/mv.py arte <slug>` | mostre o contact da arte |
| 5 | Voz + tempos de palavra | `py engine/mv.py voz <slug>` | diga a duração e o diff do whisper |
| 6 | `video.json` + shots em `videos/<slug>/shots/01_story.js` (partir de `templates/shots_modelo.js`) | escrever | — |
| 7 | Contact sheet (1 frame / 2 s) → corrigir → repetir | `py engine/mv.py contato <slug>` | — |
| 8 | Render + áudio + QC | `py engine/mv.py render <slug>` | — |
| 9 | Capa | `py engine/mv.py capa <slug>` | — |
| 10 | Log + entrega (vídeo, capa, legenda com hashtags) | `py engine/mv.py log <slug>` | **SIM: entregue** |

`--formato paisagem` em contato/stills/render gera 1920x1080; o padrão é vertical 1080x1920.
Para conferir momentos exatos: `py engine/mv.py stills <slug> 0,3.2,10.5`.

### 2.1 Tamanho (escala com a duração)
- Palavras: **~205 por minuto** com Kokoro pt-BR (fala rápido mesmo a 1.0); ~175 com vozes mais lentas.
- Lugares: minutos × `pace.places_per_min` do DNA; no vertical, corte a cada ~3 s (≈20 shots/min).
  ~30% plates grandes (com personagens), o resto tiles de close-up (4 por quad).
- Personagens principais: 1–2 abaixo de 3 min, 2–3 acima.
- Capítulos (linha `##` no roteiro): nenhum abaixo de 2 min; 3–4 até 5 min; 5–8 até 10 min.
- Render: `--partes 4` (padrão). Vídeos acima de 3 min: 4–6 partes.

### 2.2 Vertical (Reels/TikTok/Shorts) — padrão validado
- **Sem vinheta de abertura nem de encerramento:** a voz entra no frame 0. `video.json` sem `title`
  e sem `outro_plate`. (16:9 usa as vinhetas do DNA.)
- **Frame 0 nunca vazio:** o gancho já está na tela (`t0 = sh.start - 0.4` em write/number).
- Todo shot chama `sh.vert({ vw, vf })` — ver `referencia/motor.md`.
- Legendas queimadas SÓ no vertical (1–3 palavras, palavra falada destacada). O 16:9 não tem legenda.
- Zonas seguras: nada importante à direita entre 50% e 80% da altura (botões do app) nem nos 15% de
  baixo; HUD à esquerda; contador do motivo no canto superior direito.
- Ganchos e estrutura: siga `referencia/retencao.md` (validado com retenção).

## 3. Regras de estilo (não negociáveis)

- Flat vector, **sem contorno**, no máximo UMA sombra (a mesma cor mais escura), sem gradiente,
  sem textura, sem emoji, sem logo de canal, sem foto de pessoa real.
- Cores: só as 5 da paleta + as 11 cores de código do `dna.json`. Nos shots use `ENGINE.C.<cor>`,
  `ENGINE.font(px)` e `ENGINE.rgba(hex, alfa)` — **nunca hex nem nome de fonte fixos**. Na arte em
  código use `ROLE["ice"|"stone"|"pine"|"coal"|"berry"]` (papéis calculados de qualquer paleta).
- Texto só em objetos do mundo (lousa, placa, casco, cartão, tela) — nunca card solto sobre a arte
  quando o lugar pode carregar a informação. Escreva nos *blanks* do plate.
- Nada parado mais de 1 s; todo personagem respira, pisca e atua na própria fala (aponta, apresenta,
  dá de ombros, comemora). Algo novo a cada `pace.new_thing_every_s` do DNA.
- Nunca o mesmo lugar em dois shots seguidos. Zoom ≤ 1.33x sobre o pixel de origem.
- Entradas com mola/pop/puff, nunca fade simples. Um X vermelho sobre toda ideia errada.

## 4. Arte

**Rota código (padrão, grátis):** plates e tiles são funções SVG em `engine/art/plates.py` e
`tiles.py` que devolvem `(svg, meta)`. Plates: 1920x1080 em coordenadas de mundo, VAZIOS, chão livre no
meio, `meta` com `floor_y`, `blanks` (onde o código escreve), `portals` (≥ 400 px, para o zoom de
transição), `anchors`. Tiles: close-ups de objetos, 4 por quad (`make_art.py` monta o 2x2 com calhas
brancas, corta e converte o meta). Mapas: contornos lon/lat projetados (ver `pacific_map`, `brazil_map`).
Personagens: um dict por personagem em `art.json` (cores da paleta, pele variada entre personagens).

**Rota modelo de imagem (opcional):** gere as imagens com o *style core* de
`referencia/especificacao-original.md` (seção `<art>`), salve em `videos/<slug>/art/` com os mesmos
nomes, escreva o `meta` JSON medindo os retângulos na grade (`*_grid.png`), e o resto do pipeline
(recorte, rig, animação) é idêntico. Sheets em fundo chroma (verde #00B140, ou magenta se a paleta tiver
verde) e frentes SEM braços.

## 5. Voz
- Padrão: Kokoro (`mv.py voz`), voz pela tabela do narrador do DNA, velocidade 1.0–1.1 (nunca atempo).
- Mais natural: qualquer áudio pronto → `py engine/mv.py voz <slug> --wav arquivo.wav` (sua voz,
  ElevenLabs, Chatterbox…). O roteiro tem de ser o texto falado; o whisper realinha tudo.
- Menos "metralhadora": `--pausa-max 0.35 --pausa-manter 0.28`.
- O `voice.py` FALHA se mais de 5% das palavras não forem ouvidas — refaça a voz, não force.

## 6. Checagem antes do render (contact sheet)
Corrija antes de renderizar: placa vazia ou estourada; texto sobre rosto; borda preta; pé flutuando;
mesmo lugar duas vezes seguidas; trecho > 2× o intervalo do DNA sem novidade; frame 0 vazio; texto
cortado pela borda no vertical; algo fora do DNA (fonte, cor, card, transição).
Depois do render, o QC aponta saltos de 1 frame não planejados — investigue cada um (`stills`).
Áudio: o gate exige voz ≥ 15 dB acima de música+efeitos e fundo mais alto em < 1% dos frames; saída
-14 LUFS, pico -1 dB.

## 7. Entrega
- Vídeo: `videos/<slug>/<slug>_vertical.mp4` (ou `<slug>.mp4` no 16:9) e a capa.
- Legenda pronta: 1ª linha = o gancho; 2–3 frases com as palavras-chave do tema (a busca lê a
  legenda); a pergunta da chamada para comentar; **até 5 hashtags** relevantes (o Instagram limita).
- Avise sobre fatos simplificados ou versões populares de histórias.
- `mv.py log <slug>` — o sorteio por vídeo evita repetir forma/gancho/motivo/capa dos últimos 5.

## 8. O motor melhora a cada vídeo
Bug ou limitação? Corrija em `engine/` (nunca só nos arquivos de um vídeo) e registre a lição em
`referencia/licoes.md` da skill. Faça backup dos shots antes de patches grandes. Renders longos: em
partes que dá para refazer.

## Referências
- `referencia/motor.md` — API dos shots (S, sh.*, personagens, poses, câmera vertical).
- `referencia/retencao.md` — estrutura de ganchos, chamada final, ritmo.
- `referencia/licoes.md` — tudo que quebrou e como foi resolvido.
- `referencia/especificacao-original.md` — especificação completa (traços do DNA, rig, animação, som).
- `workspace/exemplos/` — dois vídeos completos: `el-nino` (vertical, mito × realidade) e
  `primeiro-cartao` (16:9, história cronológica). Para estudar ou reconstruir: copie para
  `videos/` e rode `mv.py arte` + `mv.py contato` (o `words.js` já vem pronto).
