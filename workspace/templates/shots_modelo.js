// MODELO DE SHOTS — vertical primeiro. Troque os NOMES_EM_MAIÚSCULAS e as frases de S('...').
// Exemplo completo e testado: exemplos/el-nino/shots/01_story.js (e exemplos/primeiro-cartao para paisagem).
//
// Regras que fazem funcionar:
//  - S('palavras exatas do roteiro', fn) começa o shot 0,08 s antes da frase. Use 3-4 palavras únicas.
//  - sh.at('palavra') = instante da palavra DENTRO do shot (sh.at('palavra', 2) = 2ª ocorrência).
//  - Tudo é função do tempo t; nada fica parado mais de 1 s; todo personagem se mexe.
//  - Texto só em objetos do mundo (lousa, placa, casco, cartão) — sh.write no "blank" do plate.
//  - No vertical, cada shot chama sh.vert({ vw, vf }): vw = largura de mundo visível (1000 é bom),
//    vf = [[t, x], ...] para onde a câmera olha. Sem vf ela segue os personagens.
//  - Corte a cada ~3 s; ~1 em 6 transições é corte seco ({ transition: 'cut' }) num "soco" da fala.

const K = ENGINE.C;
const springIn = d => (d <= 0 ? 0 : Math.min(1.12, 1 - Math.exp(-6.5 * d) * Math.cos(13 * d)));
const ease = p => (p <= 0 ? 0 : p >= 1 ? 1 : p * p * (3 - 2 * p));

// MOTIVO sorteado ("um objeto em todo capítulo", "um contador que sobe"…): desenhe-o UMA vez aqui e
// reaproveite em quase todo shot. Ex.: o termômetro do El Niño, o contador "CARTÕES" do primeiro cartão.
function motif(c, x, y, s, level) {
  c.save(); c.translate(x, y); c.scale(s, s);
  c.fillStyle = K.dark; c.beginPath(); c.roundRect(-30, -200, 60, 230, 30); c.fill();
  c.fillStyle = K.alert; c.beginPath(); c.roundRect(-14, 16 - 200 * level, 28, 200 * level, 14); c.fill();
  c.restore();
}

// 0 ─ ABERTURA: a frase-tese JÁ visível no frame 0 (t0 = sh.start - 0.4). Frame 0 vazio = pessoa rola o feed.
S('PRIMEIRAS PALAVRAS DO ROTEIRO', sh => {
  sh.plate('PLATE_COM_LOUSA', { cam: [[1.02, 0.5, 0.4], [1.12, 0.5, 0.36]], portal: 'blackboard' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  sh.write('blackboard', ['MITO 1?', 'MITO 2?', 'MITO 3?'], sh.start - 0.4, { color: 'card' });
  sh.x(960, 345, 420, sh.at('errado'));
});

// 1 ─ GANCHO sorteado (aqui: número chocante), também já cheio quando o shot aparece
S('FRASE DO NÚMERO', sh => {
  sh.plate('TILE_DO_GANCHO', { cam: [[1.0, 0.6, 0.5], [1.14, 0.62, 0.5]] });
  sh.vert({ vw: 1000, vf: [[sh.start, 1200]] });
  sh.number(1200, 250, 'RÓTULO CURTO', '+0,5 °C', sh.start - 0.5);
  sh.custom((c, t) => motif(c, 1000, 820, 0.8, 0.3 + 0.4 * ease((t - sh.at('PALAVRA')) / 0.8)), { z: 22 });
});

// 2 ─ BLOCO numerado: banner alto (y 0.3) que sai antes de cobrir a ação
S('Mito número um', sh => {
  sh.plate('TILE_DO_MITO', { cam: [[1.04, 0.5, 0.45], [1.12, 0.5, 0.5]] });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  sh.banner('MITO 1', sh.start, { y: 0.3, out: sh.at('PALAVRA_DO_MITO') + 0.2 });
  sh.x(960, 300, 360, sh.at('Não'));
  sh.tag(1240, 640, 'A VERDADE', sh.at('PALAVRA_DA_VERDADE'), { fill: 'warm', pole: 150 });
}, { transition: 'cut' });

// 3 ─ CENA COM PERSONAGEM: entra, anda, aponta, fala, reage
S('FRASE DA CENA', sh => {
  sh.plate('PLATE_DA_CENA', { cam: [[1.04, 0.5, 0.6], [1.1, 0.5, 0.62]] });
  sh.vert({ vw: 1000 });
  sh.hud('date', 'ANO', sh.at('ANO'));
  sh.hud('place', 'LUGAR', sh.at('LUGAR'));
  const p = sh.char('PERSONAGEM', { x: 560, y: 900, h: 520, pose: 'rest', enter: sh.start + 0.1 });
  const tEnd = p.walk(sh.start + 0.3, 960);
  p.pose(tEnd + 0.05, 'present'); p.talk(sh.at('PALAVRA'), sh.atEnd('OUTRA'));
  p.emote(sh.at('SUSTO'), 'shocked').surprise(sh.at('SUSTO'));
});

// N ─ CHAMADA FINAL: comentar / curtir / compartilhar, cada ícone na palavra que o pede
S('Comenta aí', sh => {
  sh.plate('PLATE_FINAL', { cam: [[1.02, 0.5, 0.6], [1.08, 0.5, 0.62]] });
  sh.vert({ vw: 1150, vf: [[sh.start, 960]] });
  const a = sh.char('PERSONAGEM_A', { x: 640, y: 900, h: 430, pose: 'rest', enter: sh.start + 0.05, hop: true });
  const b = sh.char('PERSONAGEM_B', { x: 1280, y: 900, h: 430, pose: 'rest', enter: sh.start + 0.2, hop: true });
  a.pose(sh.at('Comenta'), 'up'); b.pose(sh.at('manda'), 'point');
  sh.icon('comment', 640, 330, sh.at('Comenta'));
  sh.icon('like', 960, 320, sh.at('Curte'));
  sh.icon('share', 1280, 320, sh.at('manda'));
});
