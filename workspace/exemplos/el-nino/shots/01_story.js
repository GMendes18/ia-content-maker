// Como surgiu o El Niño — ~56 s, VERTICAL primeiro (Reels/TikTok/Shorts).
// Forma: mito × realidade. Gancho: número chocante ("meio grau"). Motivo: o termômetro em todo bloco.
// Retenção: corte a cada ~3 s; abre com os 3 mitos (0 s), número chocante (2,5 s), paradoxo, bebê, "falta uma peça".

const K = ENGINE.C;
const ease = p => (p <= 0 ? 0 : p >= 1 ? 1 : p * p * (3 - 2 * p));
const springIn = d => (d <= 0 ? 0 : Math.min(1.12, 1 - Math.exp(-6.5 * d) * Math.cos(13 * d)));
function keyAt(keys, t, dur = 0.6) { // [[t, valor], ...] com transição suave
  let v = keys[0][1];
  for (let i = 1; i < keys.length; i++) { const [tk, vk] = keys[i]; if (t >= tk) v = v + (vk - v) * ease((t - tk) / dur); }
  return v;
}
const WARM = ENGINE.rgba(K.warm, 0.62);

// ── objetos desenhados pelo código (todos chapados, sem contorno) ──
function thermo(c, x, y, s, lvl) { // o MOTIVO: termômetro de vidro com escala em °C
  c.save(); c.translate(x, y); c.scale(s, s);
  c.fillStyle = K.dark; c.beginPath(); c.roundRect(-34, -300, 68, 330, 34); c.fill(); c.beginPath(); c.arc(0, 50, 58, 0, 7); c.fill();
  c.fillStyle = K.card; c.beginPath(); c.roundRect(-22, -288, 44, 320, 22); c.fill(); c.beginPath(); c.arc(0, 50, 46, 0, 7); c.fill();
  c.fillStyle = K.alert; c.beginPath(); c.arc(0, 50, 34, 0, 7); c.fill();
  const top = 20 - 290 * Math.max(0.04, Math.min(1, lvl)); c.beginPath(); c.roundRect(-10, top, 20, 50 - top, 10); c.fill();
  c.fillStyle = K.ink; for (let i = 0; i < 7; i++) c.fillRect(22, -250 + i * 40, i % 2 ? 10 : 18, 5);
  c.font = ENGINE.font(26); c.textAlign = 'center'; c.fillStyle = K.ink; c.fillText('°C', 0, -250);
  c.restore();
}
function thermoItem(sh, x, y, s, keys, t0) { // entra com mola em t0
  sh.custom((c, t) => { const d = t - t0; if (d < 0) return; thermo(c, x, y + 30 * (1 - Math.min(1, springIn(d))), s * Math.min(1, springIn(d) + 0.0001), keyAt(keys, t, 0.8)); }, { z: 22 });
}
function sun(c, x, y, s, t) {
  c.save(); c.translate(x, y); c.scale(s, s); c.rotate(t * 0.4); c.fillStyle = K.highlight;
  for (let i = 0; i < 10; i++) { c.rotate(Math.PI / 5); c.beginPath(); c.roundRect(-10, -150, 20, 50, 10); c.fill(); }
  c.beginPath(); c.arc(0, 0, 80, 0, 7); c.fill(); c.restore();
}
function rainCloud(c, x, y, s, t, storm) {
  c.save(); c.translate(x, y); c.scale(s, s);
  c.fillStyle = storm ? K.dark : K.label_grey;
  for (const [dx, dy, r] of [[-110, 10, 70], [-30, -30, 95], [70, -5, 80], [140, 25, 55]]) { c.beginPath(); c.arc(dx, dy, r, 0, 7); c.fill(); }
  c.beginPath(); c.roundRect(-180, 10, 360, 80, 40); c.fill();
  c.fillStyle = storm ? K.highlight : K.headline_b;
  if (storm) { c.beginPath(); c.moveTo(10, 80); c.lineTo(-30, 190); c.lineTo(10, 180); c.lineTo(-20, 290); c.lineTo(60, 160); c.lineTo(20, 168); c.lineTo(50, 80); c.fill(); }
  c.fillStyle = K.headline_b;
  for (let i = 0; i < 9; i++) { const ph = (t * 1.6 + i * 0.37) % 1; c.beginPath(); c.roundRect(-150 + i * 36, 100 + ph * 180, 10, 34, 5); c.fill(); }
  c.restore();
}
function piece(c, x, y, s, col, label, rot) { // peça de quebra-cabeça
  c.save(); c.translate(x, y); c.rotate(rot || 0); c.scale(s, s); c.fillStyle = col;
  c.beginPath(); c.roundRect(-90, -90, 180, 180, 16); c.fill();
  c.beginPath(); c.arc(90, 0, 36, 0, 7); c.fill(); c.beginPath(); c.arc(0, -90, 36, 0, 7); c.fill();
  c.fillStyle = '#ffffff'; c.font = ENGINE.font(54); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(label, 0, 6);
  c.restore();
}
function cradle(c, x, y, s, t) { // berço de balanço
  c.save(); c.translate(x, y); c.rotate(Math.sin(t * 3.2) * 0.12); c.scale(s, s);
  c.fillStyle = K.dark; c.beginPath(); c.ellipse(0, 40, 210, 60, 0, 0, Math.PI); c.fill();
  c.fillStyle = K.headline_a; c.beginPath(); c.roundRect(-170, -130, 340, 170, 24); c.fill();
  c.fillStyle = K.transition_fill; c.beginPath(); c.roundRect(-150, -150, 300, 70, 30); c.fill();
  c.fillStyle = K.card; c.beginPath(); c.arc(-90, -150, 46, 0, 7); c.fill();
  c.fillStyle = '#e3a983'; c.beginPath(); c.arc(-90, -168, 30, 0, 7); c.fill();
  c.restore();
}
function warmBlob(c, x0, x1, y, h, p) { // água quente chapada (translúcida) crescendo de x0 para x1
  if (p <= 0) return; const x = x0 + (x1 - x0) * p, n = Math.max(2, Math.round(Math.abs(x - x0) / 70));
  c.save(); c.fillStyle = WARM; c.beginPath();
  for (let i = 0; i <= n; i++) { const xi = x0 + (x - x0) * i / n, k = 0.7 + 0.3 * Math.sin(i * 1.9 + x0 * 0.01) * Math.sin(i * 0.7);
    c.moveTo(xi + 80, y); c.ellipse(xi, y + 10 * Math.sin(i * 2.3), 80, h / 2 * k + 12, 0, 0, 7); }
  c.fill(); c.restore();
}

// 0 ─ ABERTURA: "quase tudo está errado" — os 3 mitos já na lousa no frame 0 (o espectador espera os 3)
S('Quase tudo que se fala', sh => {
  sh.plate('lab_1969_day', { cam: [[1.02, 0.5, 0.4], [1.12, 0.5, 0.36]], portal: 'blackboard' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  sh.write('blackboard', ['TEMPESTADE?', 'COISA NOVA?', 'SÓ NO PERU?'], sh.start - 0.4, { color: 'card' });  // frame 0 já com texto
  sh.x(960, 345, 420, sh.at('errado'));
  thermoItem(sh, 470, 610, 0.5, [[0, 0.35]], sh.start + 0.1);
});

// 1 ─ GANCHO: número chocante
S('Meio grau É só isso', sh => {
  const T = window.PLATES.pacific_map;
  sh.plate('pacific_map', { cam: [[1.0, 0.6, 0.5], [1.14, 0.62, 0.5]], portal: 'ocean' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1320]] });
  sh.number(1340, 250, 'MEIO GRAU', '+0,5 °C', sh.start - 0.5);  // já cheio no frame 0: o gancho não pode começar vazio
  const tw = sh.at('esquentar');
  sh.custom((c, t) => warmBlob(c, 1000, 1640, 541, 120, 0.25 + 0.75 * ease((t - tw) / 0.9)), { z: 8 });
  sh.tag(1150, 660, 'PACÍFICO', sh.at('Pacífico'), { fill: 'highlight', pole: 150 });
  thermoItem(sh, 1130, 830, 0.75, [[0, 0.2], [tw, 0.55]], sh.start - 0.5);
});

// 2 ─ o paradoxo: sem chuva E debaixo d'água
S('Brasil sem chuva', sh => {
  const T = window.PLATES.brazil_map, A = T.anchors;
  sh.plate('brazil_map', { cam: [[1.06, 0.55, 0.5], [1.14, 0.55, 0.52]], portal: 'brazil' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1060]] });
  const tc = sh.at('chuva'), td = sh.at("d'água");
  sh.custom((c, t) => { const d = t - tc; if (d > 0) sun(c, A.northeast[0] - 40, A.northeast[1] - 40, 0.9 * Math.min(1, springIn(d)), t); }, { z: 20 });
  sh.tag(A.northeast[0] - 60, A.northeast[1] + 110, 'SECA', tc + 0.15, { fill: 'warm', pole: 130 });
  sh.custom((c, t) => { const d = t - td; if (d > 0) rainCloud(c, A.south[0], A.south[1] - 120, 0.8 * Math.min(1, springIn(d)), t, false); }, { z: 20 });
  sh.tag(A.south[0] - 220, A.south[1] + 30, 'ENCHENTE', td + 0.15, { fill: 'alert', pole: 130, dir: -1 });
  sh.stamp('AO MESMO TEMPO', 1060, 600, sh.at('mesmo'));
}, { transition: 'cut' });

// 3 ─ open loop: "vem de um bebê"
S('E o nome disso', sh => {
  const T = window.PLATES.globe, A = T.anchors;
  sh.plate('globe', { cam: [[1.05, 0.5, 0.5], [1.16, 0.5, 0.55]], portal: 'globe' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  const tb = sh.at('bebê');
  sh.custom((c, t) => { const d = t - tb + 0.25; if (d > 0) cradle(c, 960, 860 + 40 * (1 - Math.min(1, springIn(d))), 1.25 * Math.min(1, springIn(d)), t); }, { z: 24 });
  sh.bubble(1160, 300, '?', sh.at('nome'), { thought: true });
});

// 5 ─ MITO 1: tempestade? não: água quente
S('Mito número um', sh => {
  const T = window.PLATES.sea_cutaway, A = T.anchors;
  sh.plate('sea_cutaway', { cam: [[1.04, 0.5, 0.45], [1.12, 0.5, 0.5]], portal: 'water' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  sh.banner('MITO 1', sh.start, { y: 0.3, out: sh.at('tempestade') + 0.2 });
  const ts = sh.at('tempestade');
  sh.custom((c, t) => { const d = t - ts; if (d > 0) rainCloud(c, A.cloud[0], A.cloud[1], Math.min(1, springIn(d)), t, true); }, { z: 20 });
  sh.sfx(ts + 0.1, 'thud');
  sh.x(A.cloud[0], A.cloud[1] + 60, 360, sh.at('Não'));
  const tq = sh.at('água');
  sh.custom((c, t) => { const p = ease((t - tq) / 0.7); if (p > 0) { c.save(); c.fillStyle = WARM; c.fillRect(960 - 520 * p, 470, 1040 * p, 110); c.restore(); } }, { z: 9 });
  sh.tag(1240, 640, 'ÁGUA QUENTE', tq + 0.1, { fill: 'warm', pole: 150 });
  thermoItem(sh, 660, 820, 0.6, [[0, 0.25], [tq, 0.7]], tq - 0.2);
});

// 6 ─ a faixa enorme que se espalha
S('Uma faixa enorme', sh => {
  const T = window.PLATES.pacific_map, A = T.anchors;
  sh.plate('pacific_map', { cam: [[1.08, 0.3, 0.5], [1.08, 0.7, 0.5]], portal: 'ocean' });
  const te = sh.at('espalha');
  sh.vert({ vw: 1100, vf: [[sh.start, 560], [sh.at('oceano'), 1370]] });
  sh.custom((c, t) => warmBlob(c, A.band_w[0], A.band_e[0], 541, 130, ease((t - sh.start - 0.1) / 2.0)), { z: 8 });
  sh.custom((c, t) => { const d = t - te; if (d <= 0) return; c.save(); c.fillStyle = WARM; c.beginPath(); c.ellipse(1600, 560, 110 + 60 * ease(d / 0.5), 140 + 90 * ease(d / 0.5), 0, 0, 7); c.fill(); c.restore(); }, { z: 8 });
  sh.tag(A.peru[0] - 150, A.peru[1] + 160, 'PERU', sh.at('esquenta'), { fill: 'highlight', pole: 140, dir: -1 });
});

// 7 ─ MITO 2: coisa moderna? Paita, século XIX
S('Mito número dois', sh => {
  sh.plate('harbor_paita_1890_day', { cam: [[1.04, 0.5, 0.6], [1.1, 0.5, 0.62]], portal: 'sea' });
  sh.vert({ vw: 1000 });
  sh.banner('MITO 2', sh.start, { y: 0.3, out: sh.at('moderna') + 0.25 });
  sh.hud('date', 'SÉCULO XIX', sh.at('dezenove'));
  sh.hud('place', 'PAITA, PERU', sh.at('Peru'));
  const f = sh.char('pescador', { x: 560, y: 900, h: 520, pose: 'rest', enter: sh.at('No') - 0.1 });
  const te = f.walk(sh.at('No') + 0.1, 960);
  f.pose(te + 0.05, 'present'); f.talk(sh.at('conheciam'), sh.atEnd('conheciam'));
  thermoItem(sh, 1260, 900, 0.5, [[0, 0.3]], sh.at('pescadores'));
});

// 8 ─ de tempos em tempos o mar esquentava
S('De tempos em tempos', sh => {
  const T = window.PLATES.sea_cutaway;
  sh.plate('sea_cutaway', { cam: [[1.1, 0.5, 0.55], [1.2, 0.5, 0.6]], portal: 'water' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  const tq = sh.at('esquentava');
  sh.custom((c, t) => { const p = ease((t - tq + 0.3) / 0.6); if (p > 0) { c.save(); c.fillStyle = WARM; c.fillRect(0, 470, 1920, 120 + 140 * p); c.restore(); } }, { z: 9 });
  thermoItem(sh, 1240, 780, 0.6, [[0, 0.3], [tq - 0.2, 0.85]], sh.start + 0.05);
}, { transition: 'cut' });

// 9 ─ os peixes sumiam, redes vazias
S('os peixes sumiam', sh => {
  const T = window.PLATES.fishing_net, A = T.anchors;
  sh.plate('fishing_net', { cam: [[1.05, 0.45, 0.52], [1.15, 0.45, 0.55]], portal: 'net' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1050]] });
  sh.tag(A.net[0] + 40, A.net[1] + 230, 'VAZIA', sh.at('vazias'), { fill: 'alert', pole: 130 });
  sh.puff(A.basket[0], A.basket[1] - 40, sh.at('sumiam'));
}, { transition: 'cut' });

// 10 ─ sempre perto do Natal
S('Sempre perto do Natal', sh => {
  const T = window.PLATES.calendar;
  sh.plate('calendar', { cam: [[1.08, 0.5, 0.5], [1.16, 0.5, 0.6]], portal: 'sheet' });
  sh.vert({ vw: 1000, vf: [[sh.start, 940]] });
  sh.write('month', ['DEZEMBRO'], sh.start + 0.02, { color: 'card' });
  const tn = sh.at('Natal'), cx = 937.6, cy = 749.6;
  sh.custom((c, t) => { const d = t - tn; if (d < 0) return; const p = Math.min(1, d / 0.35);
    c.save(); c.strokeStyle = K.alert; c.lineWidth = 12; c.lineCap = 'round';
    c.beginPath(); c.ellipse(cx, cy, 66, 60, -0.2, -1.4, -1.4 + p * Math.PI * 2.1); c.stroke(); c.restore(); }, { z: 21 });
  sh.sfx(tn, 'tick');
  sh.tag(cx + 70, cy + 80, 'NATAL', tn + 0.1, { fill: 'alert', pole: 150 });
});

// 11 ─ o nome: El Niño, o Menino Jesus (paga o gancho do bebê)
S('Por isso o nome', sh => {
  sh.plate('harbor_paita_1890_day', { cam: [[1.1, 0.42, 0.68], [1.16, 0.42, 0.7]], portal: 'sea' });
  sh.vert({ vw: 1000, vf: [[sh.start, 800]] });
  const tn = sh.at('El');
  sh.write('boat_name', ['EL NIÑO'], tn, { color: 'card' });
  const f = sh.char('pescador', { x: 1120, y: 900, h: 520, pose: 'rest' });
  f.pose(tn - 0.1, 'point', 'left'); f.talk(tn, sh.atEnd('Jesus'));
  const tj = sh.at('Menino');
  sh.custom((c, t) => { const d = t - tj; if (d < 0) return; const s = Math.min(1, springIn(d));
    c.save(); c.translate(500, 600); c.rotate(t * 0.5); c.scale(s, s); c.fillStyle = K.highlight; c.beginPath();
    for (let i = 0; i < 10; i++) { const r = i % 2 ? 26 : 64, a = i * Math.PI / 5; c.lineTo(Math.sin(a) * r, -Math.cos(a) * r); } c.fill(); c.restore(); }, { z: 20 });
  sh.custom((c, t) => { const d = t - tj; if (d > 0) cradle(c, 500, 860, 0.6 * Math.min(1, springIn(d)), t); }, { z: 19 });
});

// 12 ─ re-gancho: faltava uma peça… no céu
S('Só que faltava', sh => {
  sh.plate('pacific_horizon', { cam: [[1.05, 0.5, 0.5], [1.12, 0.5, 0.42]], portal: 'sky' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  const tp = sh.at('peça'), tc = sh.at('céu');
  sh.custom((c, t) => { const d = t - tp + 0.2; if (d > 0) piece(c, 760, 820, Math.min(1, springIn(d)), K.headline_b, 'MAR', -0.08); }, { z: 20 });
  sh.custom((c, t) => { if (t < tp) return; c.save(); c.fillStyle = ENGINE.rgba(K.dark, 0.18); c.beginPath(); c.roundRect(1030, 730, 180, 180, 16); c.fill(); c.restore(); }, { z: 19 });
  sh.custom((c, t) => { const d = t - tc; if (d > 0) piece(c, 1160, 260 + 20 * Math.sin(t * 2), Math.min(1, springIn(d)), K.headline_a, 'AR', 0.12 + 0.05 * Math.sin(t * 1.5)); }, { z: 20 });
  sh.sfx(tc, 'pop');
});

// 13 ─ Gilbert Walker, Índia, anos 1920
S('Nos anos vinte', sh => {
  const T = window.PLATES.observatory_india_1920, A = T.anchors;
  sh.plate('observatory_india_1920', { cam: [[1.04, 0.55, 0.55], [1.1, 0.58, 0.5]], portal: 'window' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1000]] });
  sh.hud('date', 'ANOS 1920', sh.at('vinte'));
  sh.hud('place', 'ÍNDIA', sh.at('Índia'));
  const w = sh.char('walker', { x: 900, y: 930, h: 500, pose: 'rest', enter: sh.at('Gilbert') - 0.1, hop: true });
  w.pose(sh.at('achou'), 'point'); w.talk(sh.at('achou'), sh.atEnd('ar'));
  w.emote(sh.at('gangorra'), 'shocked').surprise(sh.at('gangorra'));
  sh.write('wall_chart', ['SOBE', 'DESCE'], sh.at('gangorra'), { color: 'ink' });
  const tg = sh.at('gangorra');
  sh.custom((c, t) => { // ponteiro do barômetro balançando
    const a = -0.6 + (t > tg ? Math.sin((t - tg) * 4) * 1.1 * Math.exp(-(t - tg) * 0.4) : 0);
    c.save(); c.translate(A.barometer[0], A.barometer[1]); c.rotate(a); c.fillStyle = K.alert;
    c.beginPath(); c.moveTo(-8, 0); c.lineTo(0, -130); c.lineTo(8, 0); c.fill(); c.restore(); }, { z: 6 });
  thermoItem(sh, 1250, 640, 0.42, [[0, 0.6]], sh.start + 0.1);
});

// 14 ─ a gangorra do ar
S('quando a pressão', sh => {
  const T = window.PLATES.pacific_horizon, A = T.anchors;
  sh.plate('pacific_horizon', { cam: [[1.02, 0.5, 0.5], [1.08, 0.5, 0.5]], portal: 'sky' });
  sh.vert({ vw: 1150, vf: [[sh.start, 960]] });
  const ts = sh.at('sobe'), td = sh.at('desce');
  sh.custom((c, t) => {
    const ang = keyAt([[0, 0], [ts, -0.2], [td, 0.2]], t, 0.45);
    const px = A.pivot[0], py = 560;
    c.save(); c.fillStyle = K.dark; c.beginPath(); c.moveTo(px - 70, A.pivot[1] + 10); c.lineTo(px, py); c.lineTo(px + 70, A.pivot[1] + 10); c.fill();
    c.translate(px, py); c.rotate(ang);
    c.fillStyle = K.headline_a; c.beginPath(); c.roundRect(-520, -18, 1040, 36, 18); c.fill();
    const hi = ang < 0; // esquerda subiu?
    [[-460, hi ? 'ALTA' : 'BAIXA'], [460, hi ? 'BAIXA' : 'ALTA']].forEach(([x, lab]) => {
      c.fillStyle = lab === 'ALTA' ? K.alert : K.headline_b; c.beginPath(); c.roundRect(x - 110, -130, 220, 112, 18); c.fill();
      c.fillStyle = '#ffffff'; c.font = ENGINE.font(46); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(lab, x, -72);
    });
    c.restore(); }, { z: 20 });
  sh.sfx(ts, 'whoosh', -6); sh.sfx(td, 'whoosh', -6);
});

// 15 ─ 50 anos sem juntar as peças
S('Ninguém juntou', sh => {
  sh.plate('pacific_map', { cam: [[1.06, 0.5, 0.5], [1.12, 0.5, 0.5]], portal: 'ocean' });
  sh.vert({ vw: 1100, vf: [[sh.start, 1000]] });
  sh.custom((c, t) => { piece(c, 760, 760 + 10 * Math.sin(t * 2), 1, K.headline_b, 'MAR', -0.1); piece(c, 1260, 300 + 10 * Math.sin(t * 2 + 1), 1, K.headline_a, 'AR', 0.12); }, { z: 20 });
  sh.number(1000, 530, 'SEM JUNTAR', 50, sh.at('cinquenta') - 0.3, { suffix: ' ANOS', roll: 0.6 });
});

// 16 ─ Bjerknes, 1969: o ciclo que se alimenta sozinho
S('Até que Jacob', sh => {
  sh.plate('lab_1969_day', { cam: [[1.04, 0.5, 0.45], [1.1, 0.52, 0.42]], portal: 'blackboard' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1050]] });
  sh.hud('date', '1969', sh.at('Jacob'));
  const b = sh.char('bjerknes', { x: 1390, y: 930, h: 500, pose: 'rest', enter: sh.at('Jacob') - 0.05, hop: true });
  b.pose(sh.at('mostrou'), 'point', 'left'); b.talk(sh.at('mostrou'), sh.atEnd('mais'));
  const tm = sh.at('mostrou');
  sh.custom((c, t) => { const d = t - tm; if (d < 0) return; const p = ease(d / 0.4); // as peças se encaixam
    piece(c, 860 + 60 * (1 - p), 345, 0.55, K.headline_b, 'MAR', -0.1 * (1 - p)); piece(c, 1055 - 60 * (1 - p), 345, 0.55, K.headline_a, 'AR', 0.12 * (1 - p)); }, { z: 7 });
  const tq = sh.at('água'), tv = sh.at('vento'), te = sh.at('esquenta');
  const chalk = (c, txt, x, y, t0, t) => { if (t < t0) return; const n = Math.ceil(txt.length * Math.min(1, (t - t0) / 0.35));
    c.save(); c.fillStyle = K.card; c.font = ENGINE.font(46); c.textAlign = 'center'; c.fillText(txt.slice(0, n), x, y); c.restore(); };
  sh.custom((c, t) => {
    if (t > tq) c.globalAlpha = 1;
    chalk(c, 'ÁGUA QUENTE', 960, 230, tq, t); chalk(c, 'VENTO FRACO', 960, 500, sh.at('fraco') - 0.2, t);
    const arc = (t0, a0, a1) => { const p = ease((t - t0) / 0.5); if (p <= 0) return; c.save(); c.strokeStyle = K.card; c.lineWidth = 10; c.lineCap = 'round';
      c.beginPath(); c.arc(960, 365, 175, a0, a0 + (a1 - a0) * p); c.stroke(); c.restore(); };
    arc(sh.at('enfraquece'), -1.2, 1.2); arc(te, 1.95, 4.35);
    if (t > te + 0.5) { const a = (t - te) * 4; c.save(); c.fillStyle = K.highlight; c.beginPath(); c.arc(960 + Math.cos(a) * 175, 365 + Math.sin(a) * 175, 16, 0, 7); c.fill(); c.restore(); }
  }, { z: 8 });
  thermoItem(sh, 560, 600, 0.45, [[0, 0.4], [te, 0.9]], sh.at('água'));
});

// 17 ─ MITO 3: problema só do Peru?
S('Mito número três', sh => {
  const T = window.PLATES.pacific_map, A = T.anchors;
  sh.plate('pacific_map', { cam: [[1.08, 0.8, 0.55], [1.16, 0.85, 0.55]], portal: 'ocean' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1500]] });
  sh.banner('MITO 3', sh.start, { y: 0.3, out: sh.at('isso') + 0.15 });
  sh.custom((c, t) => warmBlob(c, A.band_w[0], A.band_e[0], 541, 130, 1), { z: 8 });
  sh.tag(A.peru[0] - 120, A.peru[1] + 170, 'SÓ O PERU?', sh.at('problema'), { fill: 'highlight', pole: 150, dir: -1 });
  sh.x(A.peru[0] - 180, A.peru[1] + 130, 260, sh.at('Não'));
});

// 18 ─ o Brasil sente (volta ao paradoxo do começo)
S('Seca no Norte', sh => {
  const T = window.PLATES.brazil_map, A = T.anchors;
  sh.plate('brazil_map', { cam: [[1.1, 0.55, 0.45], [1.06, 0.55, 0.55]], portal: 'brazil' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1060]] });
  const tn = sh.at('Norte'), tne = sh.at('Nordeste'), ts = sh.at('Sul');
  sh.custom((c, t) => { const d = t - tn; if (d > 0) sun(c, A.north[0] + 40, A.north[1] - 20, 0.75 * Math.min(1, springIn(d)), t); }, { z: 20 });
  sh.custom((c, t) => { const d = t - tne; if (d > 0) sun(c, A.northeast[0] - 40, A.northeast[1] - 20, 0.75 * Math.min(1, springIn(d)), t); }, { z: 20 });
  sh.custom((c, t) => { const d = t - sh.at('chuva'); if (d > 0) rainCloud(c, A.south[0], A.south[1] - 120, 0.8 * Math.min(1, springIn(d)), t, false); }, { z: 20 });
  sh.tag(A.south[0] - 220, A.south[1] + 30, 'SUL', ts, { fill: 'alert', pole: 130, dir: -1 });
}, { transition: 'cut' });

// 19 ─ incêndios na Austrália
S('incêndios na Austrália', sh => {
  sh.plate('bushfire', { cam: [[1.04, 0.5, 0.5], [1.14, 0.5, 0.45]], portal: 'sky' });
  sh.vert({ vw: 1000, vf: [[sh.start, 960]] });
  sh.custom((c, t) => { // chamas extras tremendo na frente
    c.save(); for (let i = 0; i < 7; i++) { const x = 520 + i * 150, h = 140 + 50 * Math.sin(t * 9 + i * 1.7);
      c.fillStyle = K.alert; c.beginPath(); c.moveTo(x - 50, 820); c.quadraticCurveTo(x - 20, 820 - h, x, 820 - h * 1.25); c.quadraticCurveTo(x + 30, 820 - h * 0.7, x + 50, 820); c.fill();
      c.fillStyle = K.highlight; c.beginPath(); c.moveTo(x - 24, 820); c.quadraticCurveTo(x, 820 - h * 0.6, x + 4, 820 - h * 0.8); c.quadraticCurveTo(x + 20, 820 - h * 0.4, x + 24, 820); c.fill(); }
    c.restore(); }, { z: 20 });
  sh.tag(1200, 560, 'AUSTRÁLIA', sh.at('Austrália'), { fill: 'highlight', pole: 160 });
}, { transition: 'cut' });

// 20 ─ fecha o loop: "meio grau" (o vídeo recomeça no mesmo mapa e no mesmo número)
S('Tudo por causa', sh => {
  const T = window.PLATES.pacific_map, A = T.anchors;
  sh.plate('pacific_map', { cam: [[1.14, 0.62, 0.5], [1.0, 0.6, 0.5]], portal: 'ocean' });
  sh.vert({ vw: 1000, vf: [[sh.start, 1320]] });
  sh.custom((c, t) => warmBlob(c, 1000, 1640, 541, 120, 1), { z: 8 });
  sh.number(1340, 250, 'MEIO GRAU', '+0,5 °C', sh.at('meio'));
  thermoItem(sh, 1130, 830, 0.75, [[0, 0.55]], sh.start + 0.05);
});

// 21 ─ CHAMADA: comentar / curtir / compartilhar — os 3 personagens juntos, cada um "entrega" um ícone na palavra
function iconHeart(c, x, y, s) {
  c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = K.alert;
  c.beginPath(); c.arc(-42, -20, 50, 0, 7); c.arc(42, -20, 50, 0, 7); c.fill();
  c.beginPath(); c.moveTo(-90, 0); c.lineTo(0, 100); c.lineTo(90, 0); c.lineTo(0, -10); c.fill(); c.restore();
}
function iconComment(c, x, y, s) {
  c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = '#ffffff';
  c.beginPath(); c.roundRect(-110, -80, 220, 150, 40); c.fill();
  c.beginPath(); c.moveTo(-60, 60); c.lineTo(-90, 120); c.lineTo(-10, 66); c.fill();
  c.fillStyle = K.ink; for (let i = -1; i <= 1; i++) { c.beginPath(); c.arc(i * 52, -5, 15, 0, 7); c.fill(); } c.restore();
}
function iconShare(c, x, y, s) { // seta curva de compartilhar
  c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = K.highlight;
  c.beginPath(); c.moveTo(-100, 90); c.quadraticCurveTo(-90, -40, 30, -40); c.lineTo(30, -100); c.lineTo(120, -10); c.lineTo(30, 80);
  c.lineTo(30, 20); c.quadraticCurveTo(-50, 20, -100, 90); c.fill(); c.restore();
}
S('Comenta aí', sh => {
  sh.plate('harbor_paita_1890_day', { cam: [[1.02, 0.5, 0.6], [1.08, 0.5, 0.62]], portal: 'sea' });
  sh.vert({ vw: 1150, vf: [[sh.start, 960]] });
  const tc = sh.at('Comenta'), tl = sh.at('Curte'), tm = sh.at('manda');
  const p = sh.char('pescador', { x: 640, y: 900, h: 430, pose: 'rest', enter: sh.start + 0.05, hop: true });
  const w = sh.char('walker', { x: 960, y: 900, h: 430, pose: 'rest', enter: sh.start + 0.15, hop: true });
  const b = sh.char('bjerknes', { x: 1280, y: 900, h: 430, pose: 'rest', enter: sh.start + 0.25, hop: true });
  p.pose(tc, 'up'); p.talk(tc, sh.atEnd('cidade'));
  w.pose(tl, 'cheer'); w.talk(tl, sh.atEnd('hoje'));
  b.pose(tm, 'point'); b.talk(tm, sh.atEnd('tempestade'));
  p.pose(tl, 'rest'); w.pose(tm, 'rest');
  const pop = (t0, fn, x, y, s0) => sh.custom((c, t) => { const d = t - t0; if (d < 0) return;
    fn(c, x, y - 12 * Math.sin(t * 3), s0 * Math.min(1, springIn(d)) * (1 + 0.06 * Math.sin(t * 5))); }, { z: 30 });
  pop(tc, iconComment, 640, 330, 0.9); pop(tl, iconHeart, 960, 320, 0.95); pop(tm, iconShare, 1280, 320, 0.95);
  sh.sfx(tc, 'pop'); sh.sfx(tl, 'pop'); sh.sfx(tm, 'pop');
  thermoItem(sh, 1460, 900, 0.42, [[0, 0.55]], sh.start + 0.1);
});
