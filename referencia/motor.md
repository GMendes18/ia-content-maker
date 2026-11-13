# Motor — API dos shots (`videos/<slug>/shots/*.js`)

O vídeo é uma página canvas (`engine/runtime/engine.js`) renderizada frame a frame pelo Playwright.
O mundo tem sempre 1920x1080; no vertical a tela é 1080x1920 e a câmera recorta o mundo.
Arquivos de shots são lidos em ordem alfabética; `words.js` (gerado pela voz) dá o tempo de cada palavra.

## Shot
```js
S('três ou quatro palavras do roteiro', sh => { ... }, { transition: 'cut' })  // opções opcionais
```
O shot começa 0,08 s antes da frase e termina quando o próximo começa.
`sh.start`, `sh.end`, `sh.at('palavra', n=1)`, `sh.atEnd('palavra')` → segundos absolutos.
Transições: padrão = a do DNA; `'cut'` = corte seco (use ~1 em 6, no "soco" da fala).

## Cenário e câmera
| chamada | o que faz |
|---|---|
| `sh.plate(nome, { cam: [[zoom, fx, fy], [zoom, fx, fy]], portal })` | fundo (plate ou tile); `cam` = início→fim, fx/fy 0–1; `portal` = retângulo do meta para o zoom da transição |
| `sh.vert({ vw, vf, vy })` | só vale no vertical: `vw` largura de mundo visível (800–1150), `vf` `[[t, x], …]` alvo da câmera em x de mundo, `vy` deslocamento vertical |

Sem `vf`, a câmera segue os personagens (quem tem `enter` entra no cálculo aos poucos, 0,6 s).

## Elementos (todos têm `t0` = quando entram, com mola)
| chamada | uso |
|---|---|
| `sh.write(blank, linhas[], t0, { color })` | texto escrito num *blank* do plate (lousa, placa) |
| `sh.board(x, y, w, h, linhas[], t0, o)` | quadro/cartão com linhas |
| `sh.number(x, y, rótulo, valor, t0, o)` | número grande com rótulo pequeno |
| `sh.tag(x, y, texto, t0, { fill, pole })` | etiqueta no estilo de tag do DNA, presa a um ponto |
| `sh.hud(kind, valor, t0)` | `date` / `place` — HUD no canto do DNA |
| `sh.banner(texto, t0, { y, out })` | faixa de capítulo/bloco; `y` 0–1 na tela; `out` = quando sai |
| `sh.stamp(texto, x, y, t0)` | carimbo |
| `sh.x(x, y, tamanho, t0)` | X vermelho sobre ideia errada |
| `sh.bubble(x, y, texto, t0, o)` | balão de fala/pensamento |
| `sh.puff(x, y, t0, tamanho)` | nuvenzinha de entrada/saída |
| `sh.counter(x, y, rótulo, chaves[], { from })` | contador do motivo (sobe nas palavras-chave) |
| `sh.icon(kind, x, y, t0, { scale, screen })` | CTA: `like`, `comment`, `share`, `follow` |
| `sh.custom((c, t) => { … }, { z, screen: true })` | desenho livre em canvas; `screen: true` ignora a câmera |
| `sh.sfx(t, nome, ganho)` | efeito sonoro extra (os de entrada já são automáticos) |

Use `ENGINE.C.<cor>` (ink, alert, warm, highlight, success, dark, headline_a, headline_b, label_grey,
card, transition_fill), `ENGINE.font(px)` e `ENGINE.rgba(hex, alfa)`. Nada de hex ou fonte fixos.
`ENGINE.VERT`, `ENGINE.SW`, `ENGINE.SH` dizem o formato da tela atual.

## Personagens
```js
const p = sh.char('nome', { x, y, h, pose: 'rest', enter: t, hop: true });
p.walk(t0, x1)          // devolve o instante em que chega
p.pose(t, 'present')    // down rest hips point present shrug up head chin hold wave stop cheer
p.talk(t0, t1)          // boca acompanha a fala
p.emote(t, 'shocked')   // troca a cabeça (alt_emotion do art.json)
p.surprise(t) / p.puzzled(t0, t1) / p.fear(t0, t1) / p.sweat(t0, t1) / p.slide(t0, t1, x1)
```
Todos encadeiam (`p.pose(...).talk(...)`). Respiração, piscada e balanço são automáticos.

## Arte em código (`engine/art/`)
- `plates.py`: `def nome(): return svg, meta` — 1920x1080, meta com `floor_y`, `blanks`, `portals`, `anchors`.
- `tiles.py`: close-ups 1920x1080 cada; `make_art.py` junta 4 por quad.
- Cores: `ROLE["ice"|"stone"|"pine"|"coal"|"berry"]` (papéis de qualquer paleta) e `C[...]` (cores de código).
- Helpers: `rect circle ellipse path poly g svg shade tint mix` em `svgkit.py`.
