# Notas do motor (entram no SKILL.md na etapa 8)

Correções feitas no motor durante o look test (2026-11-13). Cada uma vale para todo vídeo futuro.

## Arte
- **Sem Gemini:** `engine/art/` desenha plates e sheets em SVG chapado e rasteriza pelo Chromium
  (`rasterize.py`). A saída tem o mesmo formato que a de um modelo de imagem (PNG + chroma), então
  cutout/rig/runtime não mudam quando o Gemini entrar.
- Sombra semitransparente perto da borda da figura mistura com o chroma e vira franja → sempre
  recortar sombras pela forma (clipPath).
- **Portais do zoom-through ≥ ~400 px de largura.** O zoom é `max(W/pw, H/ph)`; uma escotilha de
  100 px dá ~19x em 0.25 s e borra tudo.
- Plate que reaparece: reescreva os blanks já preenchidos com `t0 = sh.start - 5` (continuidade).
- Nada de luminária/halo sobre um blank: suja o texto que o código escreve depois.

## Recorte e rig
- Chroma só a partir da borda deixa **buracos fechados** (entre braço e corpo) magenta → 2ª passada
  só para componentes internos com chroma quase puro (dominância > 120, distância < 45, área > 60 px).
- Despill do magenta = espelho do verde: limitar `min(R,B)` a `G+6` na faixa de 2 px.
- Rig: pescoço = mediana das linhas mais estreitas entre 25% e 65% da altura; olhos = par de
  componentes escuros quase redondos (razão 0.55–1.6) abaixo de 30% da cabeça.

## Runtime
- `Puppet`: nunca `Object.assign(this, opts)` — a opção `pose` sobrescrevia o método `pose()`.
- Motion blur: 4 subframes no normal, **14 nas janelas de transição** (4 amostras viram cópias-fantasma
  num zoom rápido). A média é feita no canvas (um screenshot por frame).
- Render: ~3 fps com blur numa máquina de 12 núcleos sem GPU → 1 min ≈ 10 min de render em 1 página;
  use `--parts 4` acima de 3 min.

## Áudio
- Sem Pixabay/Mixkit automáticos: `audio.py` sintetiza o bed na família do DNA e os SFX.
  Arquivos em `library/music/<família>/` e `library/sfx/<nome>.wav` têm prioridade.
- Frame de fala = VAD ativo em > 50% do frame (micro-pausas entre palavras não contam).
- Ducking -15 dB com música base -10 dB → voz ~28 dB acima do fundo na fala.
- loudnorm linear não alcança -14 LUFS com voz de pico alto → ganho + `alimiter` (-1.6 dB) e mede de
  novo (até 3x). Resultado típico: -14.1 a -14.3 LUFS, TP -1.3 dB.
- Kokoro pt-BR: ritmo real medido no vídeo 1 (ver abaixo): ~205 palavras/min já em 1.0.

## Vídeo 1 — "primeiro-cartao" (2026-11-13)
- **whisper:** nunca passar o roteiro como `initial_prompt` — o modelo "pula" trechos e alucina.
  `voice.py` agora FALHA se > 5% das palavras do roteiro não forem ouvidas (antes interpolava calado).
- **Kokoro pt-BR fala rápido:** `pm_alex` a 1.0 dá ~205 palavras/min. O piso do prompt é 1.0, então um
  roteiro de "1 min" (175 palavras) vira ~52 s de voz. Para fechar 60 s, escreva ~200 palavras.
- **Rig genérico:** pele = moda de uma faixa central das bochechas; olhos = escuro RELATIVO à pele
  (lum < 0.62 × pele). Limiares fixos quebravam com pele escura e com olho atrás de lente de óculos.
- **Destaque do episódio:** precisa de 4.5:1 com caixa-alta branca; o sorteio re-sorteia até 2x.
- **Contador do motivo:** passe `from:` com o valor do shot anterior, senão ele rola do zero.
- **Quads:** o divisor acha calhas de 24 px + 6 px de aparo; metadados dos tiles são convertidos
  desenho → quad → tile pelo próprio `make_art.py`.
- **Thumbnail:** figura com ~65% da altura para o quarto superior ficar livre; "depois" em plate de dia.

## Formato vertical 9:16 (Reels/TikTok/Shorts) — 2026-11-13
- `build_page.py --format vertical` → `index_vertical.html`; `render.py --format vertical` → `build_vertical/`.
  Mesmos shots: o motor separa MUNDO (plate 1920x1080) de TELA (SW x SH). O áudio é o mesmo do 16:9
  (os eventos de som são idênticos) → só muxar `build/mix.wav` no vídeo vertical.
- Cobrir 1080x1920 com um plate 16:9 mostra só ~600 px de mundo. Por shot: `sh.vert({ vw, vf, vy })`
  — `vw` = largura de mundo visível (1000 é o padrão bom para close-ups); a 1ª/última linha do plate é
  esticada em cima/embaixo (fundo chapado continua). `vf` = [[t, x]] para onde a câmera olha; sem `vf`
  ela segue a média dos personagens visíveis.
- Posições dos elementos com `v(paisagem, vertical)`; bandeiras perto da borda viram `dir: -1`.
- Tiles agora saem em 3840x2160 (quads rasterizados em 2x): o vertical amplia ~1.8x e o teto é 1.33x
  sobre o pixel de origem.
- Zonas seguras: HUD à esquerda a partir de y=250; contador do motivo vira elemento de tela no canto
  superior direito (y=330); legendas em 74% da altura, 1–3 palavras, palavra atual no tom de alerta.
- Legendas queimadas SÓ no vertical (decisão do usuário); o 16:9 segue a regra do canal.

## Vídeo 2 — "el-nino" (vertical primeiro, 2026-11-13)
- **Retenção no vertical:** sem intro e sem outro de canal — a voz entra no frame 0 com o número do gancho
  JÁ na tela (`t0 = sh.start - 0.5`); um frame 0 vazio é o pior frame possível. `video.json` sem `title`
  e sem `outro_plate` desliga as vinhetas.
- **Ganchos em camadas:** número chocante (0 s) → paradoxo (4 s) → open loop "nome de um bebê" (7 s,
  pago aos 28 s) → os 3 mitos numa lousa (9 s, o espectador espera o 3º) → "faltava uma peça" (29 s).
  Banners "MITO 1/2/3" em `y: 0.3` com `out` para sair antes de cobrir a cena.
- **Chamada final (pedido do usuário):** comentar/curtir/compartilhar falados com um MOTIVO cada
  (pergunta para comentar; "manda pra quem ainda acha que…" retoma o mito 1), e cada personagem entrega
  um ícone na palavra. Vai depois da frase-loop, então o loop deixa de ser perfeito — trade-off aceito.
- **Ritmo:** 21 shots em 63 s (~3 s cada); corte seco nos socos (paradoxo, rede vazia, Austrália).
- **Mapas chapados:** contornos à mão em lon/lat projetados (equiretangular) bastam para Brasil/Pacífico.
- `audio.py videos/<v> build_vertical` mixa direto do build vertical (sai `<v>_vertical.mp4`).
- **Capa vertical:** layout `faceoff` em `thumbnail.py` (1080x1920); `focus` é coordenada do MUNDO.
- **Bug corrigido (câmera vertical):** sem `vf`, a câmera segue os personagens; quem tinha `enter:` passava a
  contar de uma vez e a câmera PULAVA na entrada (o QC pegou aos 18,6 s). Agora o peso de quem entra
  sobe de 0 a 1 em 0,6 s, misturado com o x da câmera do shot.
- **Abertura com a frase-tese ("quase tudo… está errado")** + lousa com os 3 mitos já escritos no frame 0
  (`write` com `t0 = sh.start - 0.4`); o número chocante vira o 2º gancho, aos ~3 s.
