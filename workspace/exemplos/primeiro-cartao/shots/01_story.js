// O primeiro cartão de crédito — 1 min, história cronológica, sem capítulos (batidas a cada 15-20 s).
// Motivo: um contador "CARTÕES" que sobe nos cenários: 1 → 200 → 20.000 → BILHÕES.

const K = ENGINE.C;
// vertical (Reels/TikTok/Shorts): mesma história, câmera e posições trocadas por v(paisagem, vertical)
const V = ENGINE.VERT, v = (a, b) => (V ? b : a);
// cartãozinho de papelão de 1950 (objeto do mundo, texto nele mesmo)
function paperCard(c, x, y, s, rot) {
  c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s);
  c.fillStyle = ENGINE.rgba(K.label_grey, 1); c.beginPath(); c.roundRect(-92, -56, 190, 118, 12); c.fill();
  c.fillStyle = K.transition_fill; c.beginPath(); c.roundRect(-95, -60, 190, 118, 12); c.fill();
  c.fillStyle = K.ink; c.font = ENGINE.font(24); c.textAlign = 'center'; c.fillText('DINERS CLUB', 0, -16);
  c.fillStyle = K.alert; c.fillRect(-60, 6, 120, 8); c.fillStyle = K.label_grey; c.fillRect(-60, 24, 80, 8);
  c.restore();
}
const springIn = d => (d <= 0 ? 0 : Math.min(1.12, 1 - Math.exp(-6.5 * d) * Math.cos(13 * d)));

// 1 ─ gancho: um detalhe minúsculo
S('Um pedaço de papelão', sh => {
  const T = window.PLATES.card_closeup;
  sh.plate('card_closeup', { cam: [[1.04, 0.42, 0.52], [1.26, 0.43, 0.53]], portal: 'card' });
  sh.vert({ vf: [[sh.start, T.anchors.card[0]]], vw: 1000 });
  sh.write('card_face', ['DINERS CLUB', 'MEMBRO Nº 1'], sh.at('papelão'), { color: 'ink' });
  sh.tag(v(T.anchors.card[0] - 260, T.anchors.card[0] - 150), T.anchors.card[1] + v(150, 240), 'PAPELÃO', sh.at('menor'), { fill: 'highlight', dir: v(-1, 1), pole: 170 });
  sh.counter(1540, 820, 'CARTÕES', [[sh.at('palma'), 1]]);
  sh.custom((c, t) => { // palma da mão: uma silhueta de mão chapada que entra por baixo
    const d = t - sh.at('palma'); if (d < 0) return;
    c.save(); c.translate(v(1180, 1250), 1150 - 260 * springIn(d)); c.fillStyle = '#e3a983';
    c.beginPath(); c.ellipse(0, 0, 210, 170, 0, 0, 7); c.fill();
    for (let i = 0; i < 4; i++) { c.beginPath(); c.roundRect(-150 + i * 78, -330 + Math.abs(i - 1.5) * 30, 62, 200, 31); c.fill(); }
    c.restore();
  }, { z: 5 });
});

// 2 ─ Nova York, 1949
S('Nova York', sh => {
  sh.plate('street_1950_night', { cam: [[1.06, 0.4, 0.6], [1.12, 0.45, 0.6]], night: 0.12, portal: 'left_window' });
  sh.write('shop_sign', ["MAJOR'S CABIN GRILL"], sh.start - 5, { color: 'highlight' });
  sh.vert({ vw: 760 });
  sh.hud('place', 'NOVA YORK', sh.at('York'));
  sh.hud('date', '1949', sh.at('1949'));
  const f = sh.char('frank', { x: 330, y: 872, h: 400, enter: sh.start + 0.05 });
  f.walk(sh.start + 0.25, 900);
});

// 3 ─ o jantar e a conta
S('Frank McNamara', sh => {
  sh.plate('restaurant_1950_night', { cam: [[1.05, 0.45, 0.58], [1.12, 0.52, 0.56]], portal: 'window' });
  sh.vert({ vw: 900, vf: [[sh.start, 600], [sh.at('Grill') - 0.2, 970], [sh.at('pede a conta'), 1130], [sh.at('percebe') - 0.3, 900]] });
  sh.hud('place', "MAJOR'S CABIN GRILL", sh.at("Major's"), { slot: 0 });
  const f = sh.char('frank', { x: 760, y: 905, h: 540, pose: 'rest' });
  f.pose(sh.at('termina'), 'present', 'left');
  sh.tag(310, 696, 'JANTAR', sh.at('jantar'), { fill: 'highlight', pole: 150 });
  const w = sh.char('waiter', { x: 1700, y: 905, h: 520, pose: 'hold' });
  w.walk(sh.at('Grill') - 0.2, 1180);
  f.pose(sh.at('pede a conta'), 'point');
  f.talk(sh.at('pede a conta'), sh.atEnd('pede a conta') + 0.3);
  sh.write('menu_board', ['SUA CONTA', '$ 4,85'], sh.at('pede a conta') + 0.2, { color: 'card' });
  f.emote(sh.at('percebe'), 'shocked').surprise(sh.at('percebe'));
  f.pose(sh.at('percebe') + 0.05, 'head');
});

// 4 ─ a carteira ficou em casa (corte seco no tempo forte)
S('esqueceu a carteira', sh => {
  const T = window.PLATES.dresser_wallet;
  sh.plate('dresser_wallet', { cam: [[1.2, 0.5, 0.46], [1.3, 0.51, 0.46]], portal: 'window' });
  sh.vert({ vw: 1000, vf: [[sh.start, T.anchors.wallet[0]]] });
  sh.tag(T.anchors.wallet[0] + v(140, -120), T.anchors.wallet[1] + 6, 'CARTEIRA', sh.at('carteira'), { fill: 'alert', pole: 160, dir: v(1, -1) });
  sh.x(T.anchors.wallet[0], T.anchors.wallet[1] - 150, 90, sh.at('carteira') + 0.35);
}, { transition: 'cut' });

// 5 ─ a esposa vem salvar a noite
S('A esposa', sh => {
  const T = window.PLATES.telephone;
  sh.plate('telephone', { cam: [[1.08, 0.5, 0.45], [1.18, 0.53, 0.42]], portal: 'dial' });
  sh.vert({ vw: 1000, vf: [[sh.start, T.anchors.phone[0]], [sh.at('casa') - 0.4, 700]] });
  sh.bubble(v(T.anchors.handset[0] + 60, 1050), v(T.anchors.handset[1] - 40, 160), 'AMOR, ME SALVA!', sh.at('esposa'), { dir: -1 });
  sh.write('notepad', ['$ 4,85', 'CASA →', 'JANTAR'], sh.at('casa') - 0.2, { color: 'ink' });
  sh.stamp('SALVO', v(1450, 820), 760, sh.at('noite'));
});

// 6 ─ a pergunta: e se cobrassem depois?
S('Frank sai', sh => {
  sh.plate('street_1950_night', { cam: [[1.1, 0.48, 0.6], [1.18, 0.42, 0.6]], night: 0.12, portal: 'left_window' });
  sh.write('shop_sign', ["MAJOR'S CABIN GRILL"], sh.start - 5, { color: 'highlight' });
  const f = sh.char('frank', { x: 910, y: 872, h: 420, pose: 'rest' });
  const tEnd = f.walk(sh.start + 0.1, 560);
  f.puzzled(sh.at('pergunta'), sh.at('confiasse'));
  f.pose(tEnd + 0.05, 'chin');
  sh.vert({ vw: 800 });
  sh.bubble(v(330, 470), v(430, 380), 'PAGAR DEPOIS?', sh.at('confiasse') - 0.1, { thought: true });
  f.pose(sh.at('cobrasse'), 'stop');
});

// 7 ─ o sócio e a ideia: um clube
S('Ele chama', sh => {
  sh.plate('office_1950_day', { cam: [[1.04, 0.47, 0.55], [1.1, 0.52, 0.53]], portal: 'blackboard' });
  sh.vert({ vw: 1000, vf: [[sh.start, 600], [sh.at('Ralph') - 0.3, 1330], [sh.at('ideia'), 1040], [sh.at('clube') + 0.1, 800]] });
  const f = sh.char('frank', { x: 470, y: 915, h: 520, pose: 'rest' });
  const r = sh.char('ralph', { x: 1330, y: 915, h: 510, pose: 'rest', enter: sh.at('Ralph') - 0.05, hop: true });
  f.pose(sh.at('chama'), 'wave');
  sh.tag(1490, 915, 'SÓCIO', sh.at('Schneider'), { fill: 'highlight', pole: 230 });
  f.pose(sh.at('montam'), 'present');
  r.pose(sh.at('ideia'), 'point', 'left');
  r.talk(sh.at('ideia'), sh.atEnd('um clube'));
  sh.write('blackboard', ['UM CLUBE'], sh.at('um clube'), { color: 'card' });
  f.pose(sh.at('clube') + 0.2, 'cheer');
});

// 8 ─ como funciona: mostra, come, paga no fim do mês
S('Quem é membro', sh => {
  const T = window.PLATES.calendar;
  sh.plate('calendar', { cam: [[1.06, 0.5, 0.48], [1.16, 0.47, 0.55]], portal: 'sheet' });
  sh.vert({ vw: 1000, vf: [[sh.start, 800]] });
  sh.write('month', ['TODO MÊS'], sh.start + 0.05, { color: 'card' });
  const tc = sh.at('cartão');
  sh.custom((c, t) => paperCard(c, v(300, 480), v(560, 600), 1.3 * springIn(t - tc), -0.12 + 0.03 * Math.sin(t * 2)), { z: 20 });
  sh.sfx(tc, 'pop');
  sh.tag(v(300, 480), 800, 'COME', sh.at('come'), { fill: 'warm', pole: 140 });
  const tf = sh.at('fim do mês');
  sh.custom((c, t) => { // círculo desenhado no dia do fechamento
    const d = t - tf; if (d < 0) return; const p = Math.min(1, d / 0.35);
    c.save(); c.strokeStyle = K.alert; c.lineWidth = 12; c.lineCap = 'round';
    c.beginPath(); c.ellipse(T.anchors.day30[0], T.anchors.day30[1], 70, 62, -0.2, -1.4, -1.4 + p * Math.PI * 2.1); c.stroke(); c.restore();
  }, { z: 21 });
  sh.sfx(tf, 'tick');
  sh.tag(T.anchors.day30[0] + 80, T.anchors.day30[1] + 70, 'PAGA TUDO', sh.at('mês') + 0.1, { fill: 'alert', pole: 200 });
});

// 9 ─ quem ganha o quê: 7% de cada conta
S('O restaurante ganha', sh => {
  const T = window.PLATES.cash_register;
  sh.plate('cash_register', { cam: [[1.05, 0.5, 0.5], [1.2, 0.5, 0.4]], portal: 'display' });
  sh.vert({ vw: 1000, vf: [[sh.start, 720], [sh.at('sete') - 0.3, 960]] });
  sh.tag(T.anchors.coins[0], T.anchors.coins[1], 'CLIENTE', sh.at('cliente'), { fill: 'highlight', pole: 180 });
  sh.write('display', ['7%'], sh.at('sete'), { color: 'highlight' });
  sh.number(v(1500, 960), v(300, -90), 'DE CADA CONTA', 7, sh.at('sete') + 0.15, { suffix: '%', roll: 0.6 });
});

// 10 ─ fevereiro de 1950: a volta
S('Em fevereiro', sh => {
  sh.plate('street_1950_night', { cam: [[1.14, 0.52, 0.6], [1.08, 0.47, 0.6]], night: 0.12, portal: 'door' });
  sh.write('shop_sign', ["MAJOR'S CABIN GRILL"], sh.start - 5, { color: 'highlight' });
  sh.vert({ vw: 800 });
  sh.hud('date', 'FEV 1950', sh.at('fevereiro'));
  const f = sh.char('frank', { x: 300, y: 872, h: 420, pose: 'rest' });
  f.walk(sh.start + 0.2, 880);
});

// 11 ─ a Primeira Ceia: paga com o cartão
S('Janta', sh => {
  sh.plate('restaurant_1950_night', { cam: [[1.12, 0.5, 0.58], [1.05, 0.5, 0.56]], portal: 'window' });
  sh.write('menu_board', ['SUA CONTA', '$ 4,85'], sh.start - 5, { color: 'card' });
  const f = sh.char('frank', { x: 760, y: 905, h: 540, pose: 'rest' });
  const w = sh.char('waiter', { x: 1180, y: 905, h: 520, pose: 'hold' });
  sh.vert({ vw: 900, vf: [[sh.start, 1050]] });
  f.pose(sh.at('entrega'), 'present');
  const tc = sh.at('cartãozinho');
  sh.custom((c, t) => paperCard(c, 1000, 690, springIn(t - tc), -0.2 + 0.03 * Math.sin(t * 2)), { z: 30 });
  sh.sfx(tc, 'pop');
  w.emote(tc + 0.3, 'shocked').surprise(tc + 0.3);
  sh.counter(1560, 520, 'CARTÕES', [[tc + 0.2, 1]]);
});

// 12 ─ manchete
S('O momento', sh => {
  sh.plate('newspaper', { cam: [[1.04, 0.5, 0.4], [1.2, 0.5, 0.3]], portal: 'photo' });
  sh.vert({ vw: 1150, vf: [[sh.start, 950]] });
  sh.write('masthead', ['JORNAL DA CIDADE'], sh.start + 0.05, { color: 'ink' });
  sh.write('headline', ['A PRIMEIRA CEIA'], sh.at('Primeira') - 0.15, { color: 'alert' });
});

// 13 ─ começa pequeno: 200 membros, 14 restaurantes
S('O Diners Club', sh => {
  const T = window.PLATES.nyc_map;
  sh.plate('nyc_map', { cam: [[1.05, 0.5, 0.5], [1.22, 0.48, 0.5]], portal: 'island' });
  sh.vert({ vw: 1000, vf: [[sh.start, 745]] });
  sh.write('title', ['DINERS CLUB'], sh.at('Diners'), { color: 'ink' });
  sh.counter(1450, 820, 'CARTÕES', [[sh.at('duzentos'), 200]]);
  const t14 = sh.at('catorze') - 0.25;
  T.anchors.pins.forEach((p, i) => {
    const ti = t14 + i * 0.07;
    sh.sfx(ti, 'pop', -10);
    sh.custom((c, t) => {
      const d = t - ti; if (d < 0) return; const s = springIn(d);
      c.save(); c.translate(p[0], p[1]); c.scale(s, s); c.fillStyle = K.alert;
      c.beginPath(); c.arc(0, -34, 20, Math.PI * 0.85, Math.PI * 0.15); c.lineTo(0, 0); c.closePath(); c.fill();
      c.fillStyle = K.card; c.beginPath(); c.arc(0, -34, 8, 0, 7); c.fill(); c.restore();
    }, { z: 22 });
  });
  sh.tag(v(1300, 1080), v(560, 860), '14 RESTAURANTES', sh.at('restaurantes') + 0.2, { fill: 'highlight', pole: 170 });
});

// 14 ─ em um ano: 20 mil
S('Em um ano', sh => {
  sh.plate('office_1950_day', { cam: [[1.12, 0.6, 0.45], [1.04, 0.55, 0.5]], portal: 'window' });
  sh.write('blackboard', ['UM CLUBE'], sh.start - 5, { color: 'card' });
  sh.vert({ vw: 1000, vf: [[sh.start, 850]] });
  const f = sh.char('frank', { x: 520, y: 915, h: 520, pose: 'present' });
  const r = sh.char('ralph', { x: 1180, y: 915, h: 510, pose: 'rest' });
  sh.counter(1505, 300, 'CARTÕES', [[sh.start, 200], [sh.at('vinte'), 20000]], { roll: 1.0, from: 200 });
  f.pose(sh.at('vinte'), 'cheer'); r.pose(sh.at('vinte') + 0.1, 'cheer');
  r.emote(sh.at('mil'), 'shocked');
});

// 15 ─ hoje: bilhões
S('Hoje existem', sh => {
  const T = window.PLATES.globe;
  sh.plate('globe', { cam: [[1.05, 0.5, 0.46], [1.15, 0.5, 0.44]], portal: 'globe' });
  sh.vert({ vw: 1000, vf: [[sh.start, T.anchors.globe[0]]] });
  const tb = sh.at('bilhões');
  sh.counter(1500, 230, 'CARTÕES', [[sh.start + 0.1, 20000], [tb, 'BILHÕES']], { from: 20000 });
  for (let i = 0; i < 18; i++) {
    const ti = tb + 0.05 + i * 0.05, a0 = i * 2.39996, R0 = 330 + (i % 3) * 45;
    sh.custom((c, t) => {
      const d = t - ti; if (d < 0) return; const a = a0 + d * 0.9, s = 0.42 * springIn(d);
      paperCard(c, T.anchors.globe[0] + Math.cos(a) * R0 * 1.25, T.anchors.globe[1] + Math.sin(a) * R0 * 0.75, s, a * 0.3);
    }, { z: 20 + (i % 2) });
  }
  sh.sfx(tb + 0.1, 'whoosh', -6);
});

// 16 ─ volta ao começo: a carteira esquecida
S('E tudo começou', sh => {
  const T = window.PLATES.dresser_wallet;
  sh.plate('dresser_wallet', { cam: [[1.08, 0.5, 0.48], [1.3, 0.51, 0.45]], portal: 'window' });
  sh.vert({ vw: 1000, vf: [[sh.start, T.anchors.wallet[0]]] });
  sh.tag(T.anchors.wallet[0] + v(140, -120), T.anchors.wallet[1] + 6, 'ESQUECIDA', sh.at('esquecida'), { fill: 'alert', pole: 160, dir: v(1, -1) });
  sh.counter(1560, 860, 'CARTÕES', [[sh.start, 'BILHÕES']], { scale: 0.8, always: true });
  sh.stamp('1949', v(520, 760), 760, sh.at('carteira', 2));
});
