/* engine.js — runtime 2D guiado pelo DNA. Cada frame é função pura de t.
 *
 * Contrato da página: window.seek(t), window.READY, window.END, window.EV (eventos de som),
 * window.CUTS (instantes de corte, para o motion blur não atravessar cortes).
 *
 * Shots: S('palavras exatas', sh => {...}, {occ, chapter, transition, portal})
 *   começa 0.08 s antes da frase. A fase de build roda UMA vez; seek(t) só desenha.
 *
 * Tudo lê do DNA: cores, fonte, estilo de card, HUD, tag, entrada de texto, movimento,
 * câmera, transições. Nunca codifique uma cor ou estilo à mão aqui.
 */
(function () {
  'use strict';
  const W = 1920, H = 1080;                       // MUNDO: coordenadas do plate
  const FMT = window.FORMAT || 'landscape', VERT = FMT === 'vertical';
  const SW = VERT ? 1080 : 1920, SH = VERT ? 1920 : 1080; // TELA
  const ZB = Math.max(SW / W, SH / H);              // zoom-base para o plate cobrir a tela
  const DNA = window.DNA, T = DNA.traits, C = DNA.code_colours, R = DNA.ranges, MP = DNA.motion_params;
  const FONT = `"${T.font[0]}"`, FW = T.font[1];
  const LANG = window.LANG || 'pt';
  const STINGS = window.STINGS || {};
  const OFF = STINGS.intro ? STINGS.intro.dur : 0;  // a voz entra depois da intro
  if (OFF) for (const w of window.WORDS) { w.s += OFF; w.e += OFF; }
  window.VOICE_OFFSET = OFF;
  const L10N = { pt: { date: 'DATA:', place: 'LOCAL:' }, en: { date: 'DATE:', place: 'PLACE:' } }[LANG];

  // ───────────────────────── matemática e movimento ─────────────────────────
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const eIO = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const eOut = p => 1 - Math.pow(1 - p, 3);
  const eIn = p => p * p * p;
  function spring(d) { if (d <= 0) return 0; const s = MP.spring; return 1 - Math.exp(-s.decay * d) * Math.cos(s.freq * d); }
  function pop(d) {
    if (d <= 0) return 0; const P = MP.pop; const p = clamp(d / P.dur);
    return p >= 1 ? 1 : 1 + P.c3 * Math.pow(p - 1, 3) + P.c2 * Math.pow(p - 1, 2);
  }
  const kick = d => (d <= 0 ? 0 : MP.kick * Math.exp(-9 * d) * Math.sin(22 * d));
  const shake = (d, A) => (d < 0 ? [0, 0] : [A * Math.exp(-8 * d) * Math.sin(61 * d), A * Math.exp(-8 * d) * Math.cos(47 * d)]);
  const exitS = d => (d <= 0 ? 1 : 1 - eIn(clamp(d / MP.exit)));
  function squash(d) { // Punchy: 1.25x0.8 assentando em 0.2 s; outros: nada
    const S = MP.squash; if (!S || d < 0) return [1, 1];
    const p = clamp(d / S.settle); const k = 1 - eOut(p);
    return [lerp(1, S.x, k), lerp(1, S.y, k)];
  }
  function hash(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
  const noise = (t, k) => 0.6 * Math.sin(2 * Math.PI * 0.3 * t + k * 1.7) + 0.4 * Math.sin(2 * Math.PI * 0.47 * t + k * 4.1);
  const hexA = (hex, a) => { const h = hex.replace('#', ''); return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`; };
  const rgbStr = (c, k = 1) => `rgb(${Math.round(c[0] * k)},${Math.round(c[1] * k)},${Math.round(c[2] * k)})`;

  // ───────────────────────── assets ─────────────────────────
  const IMG = {};
  function loadImg(key, src) {
    return new Promise((ok, bad) => { const im = new Image(); im.onload = () => { IMG[key] = im; ok(); }; im.onerror = () => bad(new Error('img ' + src)); im.src = src; });
  }

  // ───────────────────────── palavras → tempo ─────────────────────────
  const norm = w => w.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
  function phraseTime(phrase, occ = 1, end = false) {
    const ws = window.WORDS, q = phrase.split(/\s+/).map(norm).filter(Boolean);
    let seen = 0;
    for (let i = 0; i + q.length <= ws.length; i++) {
      let ok = true;
      for (let k = 0; k < q.length; k++) if (ws[i + k].n !== q[k]) { ok = false; break; }
      if (ok && ++seen === occ) return end ? ws[i + q.length - 1].e : ws[i].s;
    }
    throw new Error(`frase não encontrada na narração: "${phrase}" (ocorrência ${occ})`);
  }
  const at = (p, occ) => phraseTime(p, occ);
  const atEnd = (p, occ) => phraseTime(p, occ, true);

  // ───────────────────────── texto ─────────────────────────
  const font = (px, w = FW) => `${w} ${px}px ${FONT}`;
  function fitSize(ctx, lines, w, h, max = 140) {
    let s = Math.min(max, h / (lines.length * 1.18));
    ctx.font = font(s);
    const widest = Math.max(...lines.map(l => ctx.measureText(l).width));
    if (widest > w) s *= w / widest;
    return Math.floor(s);
  }
  /* Entrada de texto do DNA. Desenha uma linha a partir de (x, y baseline). t0 = início. */
  function drawEntry(ctx, text, x, y, size, color, t0, t, rate = 28, align = 'left') {
    ctx.font = font(size); ctx.fillStyle = color; ctx.textBaseline = 'alphabetic';
    const full = ctx.measureText(text).width;
    let cx = align === 'center' ? x - full / 2 : x;
    const mode = T.text_entry;
    if (mode === 'mask_slide_up') {
      const d = t - t0; if (d <= 0) return;
      const p = eOut(clamp(d / 0.35));
      ctx.save(); ctx.beginPath(); ctx.rect(cx - 10, y - size * 1.05, full + 20, size * 1.35); ctx.clip();
      ctx.fillText(text, cx, y + (1 - p) * size * 1.2); ctx.restore(); return;
    }
    const words = text.split(' ');
    let ci = 0;
    for (let wi = 0; wi < words.length; wi++) {
      const word = words[wi] + (wi < words.length - 1 ? ' ' : '');
      const ww = ctx.measureText(word).width;
      if (mode === 'word_pop') {
        const d = t - (t0 + ci / rate); ci += word.length;
        if (d > 0) {
          const s = pop(d);
          ctx.save(); ctx.translate(cx + ww / 2, y - size * 0.35); ctx.scale(s, s); ctx.fillText(word, -ww / 2, size * 0.35); ctx.restore();
        }
        cx += ww; continue;
      }
      for (const ch of word) {
        const cw = ctx.measureText(ch).width;
        const d = t - (t0 + ci / rate); ci++;
        if (d > 0 && ch !== ' ') {
          ctx.save();
          if (mode === 'typing') {
            const p = eOut(clamp(d / 0.18)); const s = lerp(1.45, 1, p);
            ctx.translate(cx + cw / 2 + (1 - p) * 0.7 * size, y - size * 0.35); ctx.scale(s, s);
            ctx.fillText(ch, -cw / 2, size * 0.35);
          } else { // drop_bounce: cai de cima e quica na mola do DNA
            const sp = spring(d);
            ctx.globalAlpha = clamp(d / 0.05);
            ctx.fillText(ch, cx, y - (1 - sp) * size * 1.1);
          }
          ctx.restore();
        }
        cx += cw;
      }
    }
  }
  const entryDur = (text, rate = 28) => text.length / rate;

  // ───────────────────────── cards (estilo do DNA) ─────────────────────────
  function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
  function drawCard(ctx, x, y, w, h, opt = {}) {
    const fill = opt.fill || C.card, st = T.card_style;
    ctx.save();
    if (st === 'rounded_soft_shadow') {
      ctx.shadowColor = 'rgba(0,0,0,0.22)'; ctx.shadowBlur = 22; ctx.shadowOffsetY = 8;
      rr(ctx, x, y, w, h, R.card_radius); ctx.fillStyle = fill; ctx.fill();
    } else if (st === 'square_hard_offset') {
      rr(ctx, x + 8, y + 8, w, h, 4); ctx.fillStyle = C.dark; ctx.fill();
      rr(ctx, x, y, w, h, 4); ctx.fillStyle = fill; ctx.fill();
    } else if (st === 'pill_accent_strip') {
      rr(ctx, x, y, w, h, h / 2); ctx.fillStyle = fill; ctx.fill(); ctx.clip();
      ctx.fillStyle = opt.accent || C.headline_a; ctx.fillRect(x, y, Math.min(26, w * 0.1), h);
    } else if (st === 'paper_note_tape') {
      const tilt = ((opt.seed || 1) % 2 ? 1 : -1) * R.paper_tilt_max_rad * hash(opt.seed || 1);
      ctx.translate(x + w / 2, y + h / 2); ctx.rotate(tilt); ctx.translate(-x - w / 2, -y - h / 2);
      ctx.fillStyle = fill; ctx.fillRect(x, y, w, h);
      ctx.fillStyle = hexA(C.highlight, 0.75); ctx.fillRect(x + w / 2 - 50, y - 14, 100, 28);
    } else { // die_cut_sticker
      rr(ctx, x - 8, y - 8, w + 16, h + 16, 22); ctx.fillStyle = C.dark; ctx.fill();
      rr(ctx, x, y, w, h, 16); ctx.fillStyle = fill; ctx.fill();
    }
    ctx.restore();
  }

  // ───────────────────────── ícones ─────────────────────────
  function iconCalendar(ctx, x, y, s) {
    rr(ctx, x, y + s * 0.12, s, s * 0.88, s * 0.16); ctx.fillStyle = C.warm; ctx.fill();
    rr(ctx, x, y + s * 0.12, s, s * 0.3, s * 0.16); ctx.fillStyle = C.alert; ctx.fill();
    ctx.fillStyle = C.card;
    for (const k of [0.28, 0.72]) { rr(ctx, x + s * k - s * 0.06, y, s * 0.12, s * 0.26, s * 0.06); ctx.fillStyle = C.dark; ctx.fill(); }
    ctx.fillStyle = C.card;
    for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) ctx.fillRect(x + s * (0.17 + i * 0.25), y + s * (0.52 + j * 0.2), s * 0.15, s * 0.12);
  }
  function iconPin(ctx, x, y, s) {
    ctx.fillStyle = C.alert; ctx.beginPath();
    ctx.arc(x + s / 2, y + s * 0.38, s * 0.36, Math.PI * 0.85, Math.PI * 0.15);
    ctx.lineTo(x + s / 2, y + s); ctx.closePath(); ctx.fill();
    ctx.fillStyle = C.card; ctx.beginPath(); ctx.arc(x + s / 2, y + s * 0.38, s * 0.14, 0, 7); ctx.fill();
  }

  // ───────────────────────── personagens ─────────────────────────
  const POSES = { // alvo da mão relativo ao ombro, em unidades de L = L1+L2. [esq, dir], mão
    down: [[-0.04, 0.97], [0.04, 0.97], 'mitt', 'mitt'],
    rest: [[0.1, 0.9], [-0.1, 0.9], 'mitt', 'mitt'],
    hips: [[-0.42, 0.55], [0.42, 0.55], 'fist', 'fist'],
    point: [[0.1, 0.9], [0.86, -0.32], 'mitt', 'point'],
    present: [[0.1, 0.9], [0.75, 0.25], 'mitt', 'open'],
    shrug: [[-0.62, 0.12], [0.62, 0.12], 'open', 'open'],
    up: [[-0.32, -0.9], [0.32, -0.9], 'open', 'open'],
    head: [[0.12, -0.86], [-0.12, -0.86], 'open', 'open'],
    chin: [[0.1, 0.9], [-0.72, -0.15], 'mitt', 'fist'],
    hold: [[0.42, 0.45], [-0.42, 0.45], 'mitt', 'mitt'],
    wave: [[0.1, 0.9], [0.5, -0.75], 'mitt', 'open'],
    stop: [[0.1, 0.9], [0.55, -0.1], 'mitt', 'open'],
    cheer: [[-0.55, -0.75], [0.55, -0.75], 'fist', 'fist'],
  };
  function poseTargets(name, side) {
    const p = POSES[name]; if (!p) throw new Error('pose desconhecida: ' + name);
    if (side !== 'left') return { l: p[0], r: p[1], hl: p[2], hr: p[3] };
    // espelha: o braço esquerdo faz o gesto, x invertido
    return { l: [-p[1][0], p[1][1]], r: [-p[0][0], p[0][1]], hl: p[3], hr: p[2] };
  }
  function ik(sx, sy, tx, ty, a, b, outward) {
    let dx = tx - sx, dy = ty - sy, d = Math.hypot(dx, dy);
    const maxd = (a + b) * 0.999; if (d > maxd) { dx *= maxd / d; dy *= maxd / d; d = maxd; }
    const base = Math.atan2(dy, dx);
    const off = Math.acos(clamp((a * a + d * d - b * b) / (2 * a * d), -1, 1));
    const cand = [base + off, base - off].map(ang => [sx + a * Math.cos(ang), sy + a * Math.sin(ang)]);
    // cotovelo mais baixo e para fora do corpo
    const score = e => e[1] + 0.6 * outward * (e[0] - sx);
    const e = score(cand[0]) > score(cand[1]) ? cand[0] : cand[1];
    return { e, h: [sx + dx, sy + dy] };
  }
  function drawHand(ctx, x, y, ang, r, shape, skin) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.fillStyle = skin;
    if (shape === 'fist') { ctx.beginPath(); ctx.arc(0, 0, r * 1.05, 0, 7); ctx.fill(); }
    else if (shape === 'open') {
      ctx.beginPath(); ctx.ellipse(r * 0.35, 0, r * 1.3, r * 1.0, 0, 0, 7); ctx.fill();
      ctx.beginPath(); ctx.ellipse(r * 0.1, -r * 0.95, r * 0.5, r * 0.36, -0.6, 0, 7); ctx.fill();
    } else if (shape === 'point') {
      ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill();
      rr(ctx, 0, -r * 0.32, r * 2.3, r * 0.64, r * 0.32); ctx.fill();
    } else { ctx.beginPath(); ctx.ellipse(r * 0.25, 0, r * 1.2, r * 0.95, 0, 0, 7); ctx.fill(); }
    ctx.restore();
  }

  class Puppet {
    constructor(name, o) {
      this.name = name; this.rig = window.RIG[name];
      if (!this.rig) throw new Error('sem rig para ' + name);
      const cfg = Object.assign({ x: 960, y: 900, h: 600, flip: false, night: 0 }, o);
      for (const k of ['x', 'y', 'h', 'flip', 'night']) this[k] = cfg[k];
      this.poses = [{ t: -1e9, name: o.pose || 'rest', side: o.side }];
      this.emotes = [{ t: -1e9, e: 'neutral' }];
      this.talks = []; this.moves = []; this.extras = [];
      this.enterT = o.enter != null ? o.enter : null; this.enterHop = !!o.hop; this.exitT = o.exit != null ? o.exit : null;
      this.seed = [...name].reduce((s, c) => s + c.charCodeAt(0), 0) + (o.seed || 0);
      this.blinks = []; let bt = 0.6 + hash(this.seed) * 1.2, i = 0;
      while (bt < 600) { this.blinks.push(bt); bt += 2.7 + 1.5 * hash(this.seed * 7 + i++); }
      this.view = 'front'; this.views = [];
    }
    pose(t, name, side) { this.poses.push({ t, name, side }); this.poses.sort((a, b) => a.t - b.t); return this; }
    emote(t, e) { this.emotes.push({ t, e }); this.emotes.sort((a, b) => a.t - b.t); return this; }
    talk(t0, t1) { this.talks.push([t0, t1]); return this; }
    walk(t0, x1, o = {}) { // anda de lado (sprite side) até x1; duração vem do passo
      const legLen = 0.14 * this.h, stepDur = 0.42, speed = 1.5 * legLen / stepDur;
      const from = this._xAt(t0); const dur = Math.abs(x1 - from) / speed;
      this.moves.push({ t0, t1: t0 + dur, x0: from, x1, walk: true, stepDur });
      return t0 + dur;
    }
    slide(t0, t1, x1) { this.moves.push({ t0, t1, x0: this._xAt(t0), x1, walk: false }); return this; }
    surprise(t) { this.extras.push({ k: 'bang', t }); return this; }
    puzzled(t0, t1) { this.extras.push({ k: 'q', t: t0, t1 }); return this; }
    fear(t0, t1) { this.extras.push({ k: 'fear', t: t0, t1 }); return this; }
    sweat(t0, t1) { this.extras.push({ k: 'sweat', t: t0, t1 }); return this; }
    _xAt(t) {
      let x = this.x;
      for (const m of this.moves) { if (t >= m.t1) x = m.x1; else if (t > m.t0) x = lerp(m.x0, m.x1, m.walk ? (t - m.t0) / (m.t1 - m.t0) : eIO((t - m.t0) / (m.t1 - m.t0))); }
      return x;
    }
    _walking(t) { return this.moves.find(m => m.walk && t > m.t0 && t < m.t1); }
    _talking(t) { return this.talks.some(([a, b]) => t >= a && t <= b); }
    _arm(t) {
      let k = 0; for (let i = 0; i < this.poses.length; i++) if (this.poses[i].t <= t) k = i;
      const cur = poseTargets(this.poses[k].name, this.poses[k].side);
      const prev = k > 0 ? poseTargets(this.poses[k - 1].name, this.poses[k - 1].side) : cur;
      const p = eIO(clamp((t - this.poses[k].t) / R.pose_blend_s));
      const mixv = (a, b) => [lerp(a[0], b[0], p), lerp(a[1], b[1], p)];
      const out = { l: mixv(prev.l, cur.l), r: mixv(prev.r, cur.r), hl: p > 0.5 ? cur.hl : prev.hl, hr: p > 0.5 ? cur.hr : prev.hr };
      if (this.poses[k].name === 'wave') { const wv = 0.12 * Math.sin(14 * t) * p; if (this.poses[k].side === 'left') out.l[0] += wv; else out.r[0] += wv; }
      return out;
    }
    draw(ctx, t) {
      if (this.enterT != null && t < this.enterT) return;
      if (this.exitT != null && t > this.exitT + MP.exit) return;
      const rig = this.rig, s = this.h / rig.size[1];
      let x = this._xAt(t), y = this.y;
      let sc = 1, rot = 0, yo = 0;
      if (this.enterT != null) {
        const d = t - this.enterT; sc *= this.enterT < 0.01 ? 1 : spring(d);
        if (this.enterHop) yo -= Math.sin(Math.PI * clamp(d / 0.45)) * 0.18 * this.h;
      }
      if (this.exitT != null) sc *= exitS(t - this.exitT);
      if (sc <= 0.001) return;
      const wk = this._walking(t);
      const surprise = this.extras.find(e => e.k === 'bang' && t >= e.t && t < e.t + 0.5);
      if (surprise) yo -= Math.sin(Math.PI * clamp((t - surprise.t) / 0.32)) * 0.12 * this.h;
      const fear = this.extras.find(e => e.k === 'fear' && t >= e.t && t < e.t1);
      if (fear) x += Math.sin(70 * t) * 0.008 * this.h;
      if (wk) { const ph = (t - wk.t0) / wk.stepDur; yo -= Math.abs(Math.sin(Math.PI * ph)) * 0.022 * this.h; rot = 0.035 * Math.sin(Math.PI * ph); }
      // sombra de contato
      ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.beginPath();
      ctx.ellipse(x, y, this.h * 0.24 * sc * (1 + yo / this.h), this.h * 0.035 * sc, 0, 0, 7); ctx.fill(); ctx.restore();
      ctx.save();
      if (this.night) ctx.filter = `brightness(${1 - this.night})`;
      ctx.translate(x, y + yo); ctx.rotate(rot);
      const [qx, qy] = squash(this.enterT != null ? t - this.enterT : -1);
      ctx.scale(sc * qx, sc * qy * (1 + 0.009 * Math.sin(2.3 * t + this.seed)));
      if (wk) { // sprite inteiro de lado
        const im = IMG[rig.whole.side]; const dir = wk.x1 < wk.x0 ? -1 : 1;
        ctx.scale(dir * im.height / rig.size[1] * s, im.height / rig.size[1] * s);
        ctx.drawImage(im, -im.width / 2, -im.height); ctx.restore(); return;
      }
      const whole = this.views.filter(v => v.t <= t).pop();
      if (whole && whole.view !== 'front') {
        const im = IMG[rig.whole[whole.view]]; const k = this.h / im.height * (whole.view === 'sitting' ? 1.0 : 1);
        ctx.scale((this.flip ? -1 : 1) * k, k);
        ctx.drawImage(im, -im.width / 2, -im.height); ctx.restore(); return;
      }
      ctx.scale(this.flip ? -s : s, s);
      ctx.translate(-rig.size[0] / 2, -rig.size[1]);
      // corpo
      ctx.drawImage(IMG[rig.body], 0, 0);
      // cabeça: gira no pescoço
      const em = this.emotes.filter(e => e.t <= t).pop();
      const headKey = rig.heads[em.e] ? rig.heads[em.e] : rig.heads.neutral;
      const talking = this._talking(t);
      const nod = talking ? 0.025 * Math.sin(7 * t) + 0.02 * Math.sin(11.3 * t) : 0.025 * Math.sin(2.1 * t + this.seed);
      const ePop = em.t > -1e8 ? 1 + 0.08 * Math.exp(-10 * (t - em.t)) * Math.sin(20 * (t - em.t)) : 1;
      ctx.save(); ctx.translate(rig.neck[0], rig.neck[1]); ctx.rotate(nod); ctx.scale(ePop, ePop); ctx.translate(-rig.neck[0], -rig.neck[1]);
      ctx.drawImage(IMG[headKey], 0, 0);
      // piscar: pinta as caixas dos olhos com a pele + linha de cílio curva
      const blinking = this.blinks.some(b => t >= b && t < b + 0.14);
      if (blinking) for (const [ex, ey, ew, eh] of rig.eyes) {
        ctx.fillStyle = rgbStr(rig.skin); rr(ctx, ex, ey, ew, eh, ew * 0.3); ctx.fill();
        ctx.strokeStyle = C.ink; ctx.lineWidth = eh * 0.14; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(ex + ew * 0.12, ey + eh * 0.5); ctx.quadraticCurveTo(ex + ew / 2, ey + eh * 0.78, ex + ew * 0.88, ey + eh * 0.5); ctx.stroke();
      }
      ctx.restore();
      // braços por IK de dois ossos
      const arms = this._arm(t);
      const Hs = rig.size[1], L1 = R.arm.L1 * Hs, L2 = R.arm.L2 * Hs, Lt = L1 + L2, th = R.arm.thickness * Hs;
      for (const side of ['l', 'r']) {
        const [sx, sy] = rig.sockets[side]; const tg = arms[side];
        const out = side === 'l' ? -1 : 1;
        const { e, h } = ik(sx, sy, sx + tg[0] * Lt * (this.flip ? 1 : 1), sy + tg[1] * Lt, L1, L2, out);
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.strokeStyle = rgbStr(rig.sleeve); ctx.lineWidth = th;
        ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(e[0], e[1]); ctx.stroke();
        ctx.strokeStyle = rgbStr(rig.skin); ctx.lineWidth = th * 0.9;
        ctx.beginPath(); ctx.moveTo(e[0], e[1]); ctx.lineTo(h[0], h[1]); ctx.stroke();
        ctx.fillStyle = rgbStr(rig.sleeve); ctx.beginPath(); ctx.arc(e[0], e[1], th * 0.5, 0, 7); ctx.fill(); // junta do cotovelo
        drawHand(ctx, h[0], h[1], Math.atan2(h[1] - e[1], h[0] - e[0]), th * 0.75, side === 'l' ? arms.hl : arms.hr, rgbStr(rig.skin));
      }
      ctx.restore();
      // extras sobre a cabeça (em coordenadas do mundo)
      const top = y + yo - this.h * 1.02;
      for (const ex of this.extras) {
        if (ex.k === 'bang' && t >= ex.t && t < ex.t + 1.2) drawBang(ctx, x + this.h * 0.18, top, t - ex.t, this.h);
        if (ex.k === 'q' && t >= ex.t && t < ex.t1) drawQ(ctx, x + this.h * 0.2, top, t - ex.t, this.h);
        if (ex.k === 'sweat' && t >= ex.t && t < ex.t1) drawSweat(ctx, x - this.h * 0.16, top + this.h * 0.2, t - ex.t, this.h);
      }
    }
  }

  // ───────────────────────── kit gráfico ─────────────────────────
  function drawBang(ctx, x, y, d, h) {
    const s = pop(d) * h / 600, a = d > 1.0 ? 1 - (d - 1.0) / 0.2 : 1;
    ctx.save(); ctx.globalAlpha = clamp(a); ctx.translate(x, y); ctx.scale(s, s); ctx.rotate(0.12);
    ctx.fillStyle = C.warm; rr(ctx, -14, -110, 28, 76, 14); ctx.fill(); ctx.beginPath(); ctx.arc(0, -8, 15, 0, 7); ctx.fill(); ctx.restore();
  }
  function drawQ(ctx, x, y, d, h) {
    const s = pop(d) * h / 600;
    ctx.save(); ctx.translate(x, y + Math.sin(d * 4) * 8); ctx.rotate(Math.sin(d * 3) * 0.12); ctx.scale(s, s);
    ctx.font = font(110); ctx.fillStyle = C.warm; ctx.textAlign = 'center'; ctx.fillText('?', 0, 0); ctx.restore();
  }
  function drawSweat(ctx, x, y, d, h) {
    const k = h / 600, fall = (d * 1.6) % 1;
    ctx.save(); ctx.globalAlpha = 1 - fall; ctx.fillStyle = '#9fd3f0'; ctx.translate(x, y + fall * 60 * k); ctx.scale(k, k);
    ctx.beginPath(); ctx.moveTo(0, -18); ctx.quadraticCurveTo(14, 4, 0, 10); ctx.quadraticCurveTo(-14, 4, 0, -18); ctx.fill(); ctx.restore();
  }
  function drawPuff(ctx, x, y, d, size = 120) {
    if (d < 0 || d > 0.5) return;
    const p = eOut(d / 0.5);
    ctx.save(); ctx.fillStyle = C.card; ctx.globalAlpha = 1 - p;
    for (let i = 0; i < 7; i++) {
      const a = i / 7 * Math.PI * 2 + 0.3; const r = size * (0.25 + 0.5 * p);
      ctx.beginPath(); ctx.arc(x + Math.cos(a) * r, y + Math.sin(a) * r * 0.55, size * 0.22 * (1 - p * 0.5), 0, 7); ctx.fill();
    }
    ctx.restore();
  }
  function tagColours(fill) {
    const f = C[fill] || fill;
    const dark = ['ink', 'alert', 'dark', 'headline_a', 'headline_b'].includes(fill);
    return [f, dark ? C.card : C.ink];
  }
  /* Tag no estilo do DNA. (x,y) = o ponto da coisa no mundo. */
  function drawTag(ctx, x, y, label, d, opt = {}) {
    if (d < 0) return;
    const [fill, txt] = tagColours(opt.fill || 'highlight');
    const p = clamp(d / 0.2), e = eOut(p);
    ctx.save(); ctx.font = font(40); const tw = ctx.measureText(label).width; const bw = tw + 44, bh = 64;
    const st = T.tag_style, dir = opt.dir || 1;
    if (st === 'flag_pole') {
      const ph = opt.pole || 190, gx = x + dir * 40;
      const grow = spring(d) ;
      ctx.fillStyle = C.dark; rr(ctx, gx - 5, y - ph * clamp(grow, 0, 1.08), 10, ph * clamp(grow, 0, 1.08), 5); ctx.fill();
      ctx.beginPath(); ctx.ellipse(gx, y, 22, 7, 0, 0, 7); ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fill();
      const fp = eOut(clamp((d - 0.1) / 0.12));
      if (fp > 0) {
        const fy = y - ph * clamp(grow, 0, 1.08); const wave = Math.sin(d * 5) * 0.03;
        ctx.save(); ctx.translate(gx + dir * 5, fy); ctx.transform(1, wave, 0, 1, 0, 0); ctx.scale(dir * fp, 1);
        ctx.fillStyle = fill; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(bw + 24, 0); ctx.lineTo(bw, bh / 2); ctx.lineTo(bw + 24, bh); ctx.lineTo(0, bh); ctx.closePath(); ctx.fill();
        ctx.scale(dir, 1); ctx.fillStyle = txt; ctx.textBaseline = 'middle';
        ctx.fillText(label, dir > 0 ? 20 : -bw + 24, bh / 2 + 2);
        ctx.restore();
      }
    } else if (st === 'line_dot_pill' || st === 'curved_arrow') {
      const ex = x + dir * 170 * e, ey = y - 120 * e;
      ctx.strokeStyle = fill; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x, y);
      if (st === 'curved_arrow') ctx.quadraticCurveTo(x, ey, ex, ey); else ctx.lineTo(ex, ey); ctx.stroke();
      ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(x, y, 11 * e, 0, 7); ctx.fill();
      if (p >= 0.6) { const s = pop(d - 0.12); ctx.translate(ex + dir * bw / 2, ey); ctx.scale(s, s); rr(ctx, -bw / 2, -bh / 2, bw, bh, bh / 2); ctx.fill(); ctx.fillStyle = txt; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, 0, 2); }
    } else if (st === 'bracket') {
      const w = opt.w || 200; ctx.strokeStyle = fill; ctx.lineWidth = 8; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x - w / 2, y - 20); ctx.lineTo(x - w / 2, y - 40); ctx.lineTo(x - w / 2 + w * e, y - 40); ctx.lineTo(x - w / 2 + w * e, y - 20); ctx.stroke();
      if (p >= 0.6) { const s = pop(d - 0.12); ctx.translate(x, y - 40 - bh / 2 - 6); ctx.scale(s, s); ctx.fillStyle = fill; rr(ctx, -bw / 2, -bh / 2, bw, bh, 12); ctx.fill(); ctx.fillStyle = txt; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, 0, 2); }
    } else { // triangle_pointer
      const s = pop(d); ctx.translate(x, y - 20); ctx.scale(s, s); ctx.fillStyle = fill;
      ctx.beginPath(); ctx.moveTo(-16, -22); ctx.lineTo(16, -22); ctx.lineTo(0, 0); ctx.fill();
      rr(ctx, -bw / 2, -22 - bh, bw, bh, 14); ctx.fill(); ctx.fillStyle = txt; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, 0, -22 - bh / 2 + 2);
    }
    ctx.restore();
  }
  function hudBox(slot) { // HUD do DNA
    const pos = T.hud, w = 360, h = 120, m = 40, g = 16;
    if (VERT) return [56, 250 + slot * (h + g), w, h];   // vertical: esquerda, abaixo da barra do app (lado direito = botões)
    if (pos === 'top_strip') return [m + slot * (w + g), 24, w, 92];
    const x = pos.endsWith('right') ? SW - m - w : m;
    const y = pos.startsWith('top') ? m + slot * (h + g) : SH - m - h - (1 - slot) * (h + g);
    return [x, y, w, h];
  }
  function drawHud(ctx, kind, value, slot, d, dOut) {
    if (d < 0) return;
    let [x, y, w, h] = hudBox(slot);
    ctx.save(); ctx.font = font(44); w = Math.max(w, ctx.measureText(value).width + 150);
    if (T.hud.endsWith('right') && !VERT) x = SW - 40 - w;
    const s = eOut(clamp(d / 0.32)) * (1 + 0.06 * Math.sin(clamp(d / 0.32) * Math.PI)) * (dOut != null ? exitS(dOut) : 1);
    if (s <= 0) { ctx.restore(); return; }
    ctx.translate(x + w / 2, y + h / 2); ctx.scale(s, s); ctx.translate(-x - w / 2, -y - h / 2);
    drawCard(ctx, x, y, w, h, { seed: slot + 3 });
    if (kind === 'date') iconCalendar(ctx, x + 26, y + h / 2 - 34, 68); else iconPin(ctx, x + 32, y + h / 2 - 36, 60);
    ctx.fillStyle = C.label_grey; ctx.font = font(26); ctx.textBaseline = 'alphabetic';
    ctx.fillText(kind === 'date' ? L10N.date : L10N.place, x + 118, y + 46);
    drawEntry(ctx, value, x + 118, y + 96, 44, C.ink, 0.12, d, 34);
    ctx.restore();
  }
  function drawStamp(ctx, x, y, text, d) {
    if (d < 0) return;
    const s = (d < 0.14 ? lerp(2.1, 1, eIn(d / 0.14)) : 1) + kick(d - 0.14);
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.12); ctx.scale(s, s); ctx.globalAlpha = clamp(d / 0.06);
    ctx.font = font(84); const tw = ctx.measureText(text).width; const bw = tw + 70, bh = 130;
    ctx.strokeStyle = C.alert; ctx.lineWidth = 9; rr(ctx, -bw / 2, -bh / 2, bw, bh, 20); ctx.stroke();
    ctx.lineWidth = 4; rr(ctx, -bw / 2 + 14, -bh / 2 + 14, bw - 28, bh - 28, 12); ctx.stroke();
    ctx.fillStyle = C.alert; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, 4); ctx.restore();
  }
  function drawX(ctx, x, y, size, d) {
    if (d < 0) return;
    ctx.save(); ctx.strokeStyle = C.alert; ctx.lineWidth = 30; ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(0,0,0,0.25)'; ctx.shadowBlur = 12; ctx.shadowOffsetY = 5;
    const p1 = eOut(clamp(d / 0.11)), p2 = eOut(clamp((d - 0.12) / 0.11)), r = size / 2;
    ctx.beginPath(); ctx.moveTo(x - r, y - r); ctx.lineTo(x - r + 2 * r * p1, y - r + 2 * r * p1); ctx.stroke();
    if (p2 > 0) { ctx.beginPath(); ctx.moveTo(x + r, y - r); ctx.lineTo(x + r - 2 * r * p2, y - r + 2 * r * p2); ctx.stroke(); }
    ctx.restore();
  }
  function drawBanner(ctx, text, d, colour, dOut, yFrac) {
    if (d < 0) return;
    const p = eOut(clamp(d / 0.22)); const out = dOut != null ? exitS(dOut) : 1;
    ctx.save(); ctx.translate(SW / 2 + (1 - p) * -SW * 1.1, SH * (yFrac || 0.5)); ctx.rotate(-0.02); ctx.scale(1, out);
    ctx.fillStyle = colour || C.headline_a; ctx.fillRect(-SW * 0.6, -80, SW * 1.2, 160);
    ctx.font = font(92); const bw = ctx.measureText(text).width; const bs = Math.min(92, 92 * SW * 0.86 / bw); ctx.font = font(bs);
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, 6); ctx.restore();
  }
  function drawNumber(ctx, x, y, label, value, d, opt = {}) {
    if (d < 0) return;
    const s = pop(d); const roll = eOut(clamp((d - 0.1) / (opt.roll || 0.9)));
    const v = typeof value === 'number' ? Math.round(value * roll).toLocaleString(LANG === 'pt' ? 'pt-BR' : 'en-US') : value;
    ctx.save(); ctx.font = font(96); const w = Math.max(320, ctx.measureText(String(opt.prefix || '') + v + (opt.suffix || '')).width + 80), h = 190;
    ctx.translate(x, y); ctx.scale(s, s); drawCard(ctx, -w / 2, -h / 2, w, h, { seed: 7 });
    ctx.fillStyle = C.label_grey; ctx.font = font(28); ctx.textAlign = 'center'; ctx.fillText(label, 0, -h / 2 + 46);
    ctx.fillStyle = C.alert; ctx.font = font(96); ctx.fillText((opt.prefix || '') + v + (opt.suffix || ''), 0, h / 2 - 34); ctx.restore();
  }
  function drawBubble(ctx, x, y, text, d, opt = {}) {
    if (d < 0) return;
    const s = pop(d) * (opt.dOut != null ? exitS(opt.dOut) : 1);
    ctx.save(); ctx.font = font(44); const tw = ctx.measureText(text).width; const w = tw + 60, h = 96;
    ctx.translate(x, y); ctx.scale(s, s);
    if (opt.thought) {
      ctx.fillStyle = C.card; rr(ctx, -w / 2, -h - 50, w, h, h / 2); ctx.fill();
      ctx.beginPath(); ctx.arc(-10, -30, 16, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(-24, -6, 9, 0, 7); ctx.fill();
    } else {
      drawCard(ctx, -w / 2, -h - 40, w, h, { seed: 9 });
      ctx.fillStyle = C.card; ctx.beginPath(); ctx.moveTo(-20, -41); ctx.lineTo(20, -41); ctx.lineTo(-8 * (opt.dir || 1), 0); ctx.fill();
    }
    ctx.fillStyle = C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    drawEntry(ctx, text, 0, opt.thought ? -h / 2 - 50 + 16 : -h / 2 - 40 + 16, 44, C.ink, 0.1, d, 34, 'center');
    ctx.restore();
  }
  /* Board: cai 420 px na mola e balança 0.25 rad até assentar; linhas entram 0.3 s uma da outra. */
  function drawBoard(ctx, x, y, w, h, lines, d, o = {}) {
    if (d < 0) return;
    const drop = -420 * (1 - spring(d)), swing = 0.25 * Math.exp(-3.2 * d) * Math.cos(8.5 * d);
    ctx.save(); ctx.translate(x + w / 2, y - 120 + drop); ctx.rotate(swing);
    ctx.strokeStyle = C.dark; ctx.lineWidth = 6;
    for (const k of [-0.32, 0.32]) { ctx.beginPath(); ctx.moveTo(k * w, -900); ctx.lineTo(k * w, 120); ctx.stroke(); }
    ctx.translate(-w / 2, 120);
    drawCard(ctx, 0, 0, w, h, { seed: 11, accent: o.accent });
    const size = o.size || Math.min(110, h / (lines.length * 1.3));
    lines.forEach((l, i) => drawEntry(ctx, l, w / 2, h / 2 + (i - (lines.length - 1) / 2) * size * 1.18 + size * 0.36, size,
      i === 0 && o.first ? o.first : C.ink, 0.35 + i * (0.3 + entryDur(lines[0])), d, 28, 'center'));
    ctx.restore();
  }
  /* Contador mecânico do motivo: vive no mundo, rola entre os valores-chave. keys = [[t, valor], ...] */
  function fmtNum(v) { return Math.round(v).toLocaleString(LANG === 'pt' ? 'pt-BR' : 'en-US'); }
  function drawCounter(ctx, x, y, label, keys, t, o = {}) {
    let k = -1; for (let i = 0; i < keys.length; i++) if (keys[i][0] <= t) k = i;
    if (k < 0 && !o.always) return;
    const appear = keys[0][0], s = o.always ? 1 : pop(t - appear);
    let txt;
    if (k < 0) txt = typeof keys[0][1] === 'number' ? '0' : '';
    else {
      const [tk, vk] = keys[k], prev = k > 0 ? keys[k - 1][1] : (o.from != null ? o.from : 0);  // from: valor herdado do shot anterior
      if (typeof vk === 'number') { const p = eOut(clamp((t - tk) / (o.roll || 0.9))); txt = fmtNum(lerp(typeof prev === 'number' ? prev : 0, vk, p)); }
      else txt = vk;
    }
    const bump = k >= 0 ? 1 + kick(t - keys[k][0]) * 1.5 : 1;
    ctx.save(); ctx.translate(x, y); ctx.scale(s * bump * (o.scale || 1), s * bump * (o.scale || 1)); ctx.font = font(64);
    const w = Math.max(300, ctx.measureText(txt).width + 70), h = 150;
    rr(ctx, -w / 2, -h / 2, w, h, 22); ctx.fillStyle = C.dark; ctx.fill();
    rr(ctx, -w / 2 + 14, -h / 2 + 50, w - 28, h - 64, 12); ctx.fillStyle = C.card; ctx.fill();
    ctx.fillStyle = C.highlight; ctx.font = font(26); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, 0, -h / 2 + 27);
    ctx.fillStyle = C.alert; ctx.font = font(64); ctx.fillText(txt, 0, h / 2 - 41);
    ctx.restore();
  }

  // ícones da chamada final (CTA): coração = curtir, balão = comentar, seta = compartilhar, sino = seguir
  function drawIcon(c, kind, x, y, s) {
    c.save(); c.translate(x, y); c.scale(s, s);
    if (kind === 'like') {
      c.fillStyle = C.alert; c.beginPath(); c.arc(-42, -20, 50, 0, 7); c.arc(42, -20, 50, 0, 7); c.fill();
      c.beginPath(); c.moveTo(-90, 0); c.lineTo(0, 100); c.lineTo(90, 0); c.lineTo(0, -10); c.fill();
    } else if (kind === 'comment') {
      c.fillStyle = C.card; c.beginPath(); c.roundRect(-110, -80, 220, 150, 40); c.fill();
      c.beginPath(); c.moveTo(-60, 60); c.lineTo(-90, 120); c.lineTo(-10, 66); c.fill();
      c.fillStyle = C.ink; for (let i = -1; i <= 1; i++) { c.beginPath(); c.arc(i * 52, -5, 15, 0, 7); c.fill(); }
    } else if (kind === 'share') {
      c.fillStyle = C.highlight; c.beginPath(); c.moveTo(-100, 90); c.quadraticCurveTo(-90, -40, 30, -40); c.lineTo(30, -100);
      c.lineTo(120, -10); c.lineTo(30, 80); c.lineTo(30, 20); c.quadraticCurveTo(-50, 20, -100, 90); c.fill();
    } else if (kind === 'follow') {
      c.fillStyle = C.warm; c.beginPath(); c.moveTo(-80, 60); c.quadraticCurveTo(-80, -90, 0, -90); c.quadraticCurveTo(80, -90, 80, 60); c.closePath(); c.fill();
      c.beginPath(); c.roundRect(-100, 50, 200, 26, 13); c.fill(); c.beginPath(); c.arc(0, 96, 22, 0, 7); c.fill();
    }
    c.restore();
  }

  function drawVignette(ctx, k = 0.35) {
    // vinheta chapada: 3 molduras arredondadas sobrepostas, sem gradiente
    ctx.save(); ctx.fillStyle = `rgba(10,12,20,${k / 3})`;
    for (let i = 0; i < 3; i++) { const m = 30 + i * 40; ctx.beginPath(); ctx.rect(0, 0, SW, SH); ctx.roundRect(m, m * 0.6, SW - 2 * m, SH - 1.2 * m, 260); ctx.fill('evenodd'); }
    ctx.restore();
  }

  // ───────────────────────── shots, câmera, transições ─────────────────────────
  const SHOTS = []; const EV = [];
  window.S = function (phrase, build, opts = {}) { SHOTS.push({ phrase, build, opts, start: Math.max(0, phraseTime(phrase, opts.occ || 1) - 0.08) }); };

  function camAt(sh, t) {
    const p = eIO(clamp((t - sh.start) / Math.max(0.001, sh.dur) * (MP.camera_speed || 1)));
    const a = sh.cam[0], b = sh.cam[1] || sh.cam[0];
    let z = lerp(a[0], b[0], p), fx = lerp(a[1], b[1], p), fy = lerp(a[2], b[2], p), dx = 0, dy = 0;
    const cam = T.camera;
    if (cam === 'handheld_drift') { z = Math.max(z, 1.016); dx = 6 * noise(t, 1); dy = 6 * noise(t, 2); }
    if (cam === 'snap_zoom') for (const st of sh.snaps) { const d = t - st; if (d > 0 && d < 1.2) z *= 1 + 0.07 * (d < 0.12 ? eOut(d / 0.12) : 1); }
    if (VERT) {
      // vertical: o empurrão da câmera do 16:9 vira 35% (já partimos de ~1.8x); x segue a ação
      fx = focusX(sh, t) / W; const push = 1 + (z - 1) * 0.35;
      // vw = largura de mundo visível; menor que a cobertura → o plate é estendido em cima/embaixo
      z = sh.vw ? Math.min(SW / sh.vw, ZB) * push : ZB * push;
    }
    // teto de zoom pela resolução REAL da imagem: no máximo 1.33x de ampliação sobre o pixel de origem
    const img = IMG['plate:' + sh.plate]; if (img) z = Math.min(z, 1.33 * img.width / W);
    const vw = SW / z, vh = SH / z;
    const cx = clamp(fx * W + dx / z, vw / 2, W - vw / 2);
    const cy = vh >= H ? H / 2 + (sh.vy || 0) + dy / z : clamp(fy * H + dy / z, vh / 2, H - vh / 2);
    return { z, cx, cy };
  }
  function focusX(sh, t) { // vertical: para onde a câmera olha no eixo x do mundo
    if (sh.vf && sh.vf.length) {
      let k = -1; for (let i = 0; i < sh.vf.length; i++) if (sh.vf[i][0] <= t) k = i;
      if (k < 0) return sh.vf[0][1];
      const prev = k > 0 ? sh.vf[k - 1][1] : sh.vf[k][1];
      return lerp(prev, sh.vf[k][1], eIO(clamp((t - sh.vf[k][0]) / 0.6)));
    }
    // segue os personagens; quem ENTRA ganha peso aos poucos (0→1 em 0,6 s) — antes a câmera pulava na entrada
    const base = lerp(sh.cam[0][1], (sh.cam[1] || sh.cam[0])[1], clamp((t - sh.start) / sh.dur)) * W;
    let sw = 0, sx = 0;
    for (const p of sh.chars) {
      const w = p.enterT == null || p.enterT <= sh.start + 0.01 ? 1 : eIO(clamp((t - p.enterT) / 0.6));
      sw += w; sx += w * p._xAt(t);
    }
    if (sw <= 0) return base;
    return sw >= 1 ? sx / sw : sx + base * (1 - sw);
  }
  function applyCam(ctx, c) { ctx.translate(SW / 2, SH / 2); ctx.scale(c.z, c.z); ctx.translate(-c.cx, -c.cy); }

  function drawScene(ctx, sh, t) {
    const c = camAt(sh, t);
    ctx.save(); applyCam(ctx, c);
    const pim = IMG['plate:' + sh.plate]; ctx.drawImage(pim, 0, 0, W, H);
    if (VERT) { // borda estendida: a 1ª e a última linha do plate esticadas (fundo chapado continua)
      const r = pim.height / H, e = 3 * r;
      ctx.drawImage(pim, 0, e, pim.width, 1, 0, -1400, W, 1400 + 1);
      ctx.drawImage(pim, 0, pim.height - e - 1, pim.width, 1, 0, H - 1, W, 1400);
    }
    const items = sh.items.filter(i => i.space === 'world').sort((a, b) => (a.z || 0) - (b.z || 0));
    for (const it of items) it.draw(ctx, t, c);
    ctx.restore();
    if (sh.tint) { ctx.fillStyle = sh.tint; ctx.fillRect(0, 0, SW, SH); }
    if (sh.vignette) drawVignette(ctx, sh.vignette);
    for (const it of sh.items.filter(i => i.space === 'screen')) it.draw(ctx, t, c);
  }

  function shotAt(t) { let k = 0; for (let i = 0; i < SHOTS.length; i++) if (SHOTS[i].start <= t) k = i; return k; }

  function drawZoomThrough(ctx, A, B, t, p) {
    const e = eIO(p), ca = camAt(A, t), P = A.portal;
    const rx = (P[0] - ca.cx) * ca.z + SW / 2, ry = (P[1] - ca.cy) * ca.z + SH / 2, rw = P[2] * ca.z, rh = P[3] * ca.z;
    const kMax = Math.max(SW / rw, SH / rh), k = Math.pow(kMax, e);
    const pcx = rx + rw / 2, pcy = ry + rh / 2, ox = lerp(pcx, SW / 2, e), oy = lerp(pcy, SH / 2, e);
    ctx.save(); ctx.translate(ox, oy); ctx.scale(k, k); ctx.translate(-pcx, -pcy); drawScene(ctx, A, t); ctx.restore();
    const qx = ox + (rx - pcx) * k, qy = oy + (ry - pcy) * k, qw = rw * k, qh = rh * k;
    ctx.save(); ctx.beginPath(); ctx.rect(qx, qy, qw, qh); ctx.clip();
    const s = lerp(Math.max(qw / SW, qh / SH), 1, e), cxB = lerp(qx + qw / 2, SW / 2, e), cyB = lerp(qy + qh / 2, SH / 2, e);
    ctx.translate(cxB, cyB); ctx.scale(s, s); ctx.translate(-SW / 2, -SH / 2); drawScene(ctx, B, t); ctx.restore();
  }
  function drawPush(ctx, A, B, t, p, vertical) {
    const e = eIO(p), off = vertical ? SH : SW;
    ctx.save(); vertical ? ctx.translate(0, -e * off) : ctx.translate(-e * off, 0); drawScene(ctx, A, t); ctx.restore();
    ctx.save(); vertical ? ctx.translate(0, (1 - e) * off) : ctx.translate((1 - e) * off, 0); drawScene(ctx, B, t); ctx.restore();
  }
  function drawIris(ctx, A, B, t, p) {
    drawScene(ctx, A, t); const e = eIO(p), f = B.focus || [SW / 2, SH / 2];
    ctx.save(); ctx.beginPath(); ctx.arc(f[0], f[1], e * Math.hypot(SW, SH), 0, 7); ctx.clip(); drawScene(ctx, B, t); ctx.restore();
  }
  function drawSlats(ctx, A, B, t, p) {
    drawScene(ctx, A, t); ctx.save(); ctx.beginPath();
    for (let i = 0; i < 3; i++) { const e = eIO(clamp(p * 1.4 - i * 0.2)); const w0 = SW * 0.8; const x0 = -w0 + i * SW * 0.5; ctx.moveTo(x0, SH); ctx.lineTo(x0 + w0 * 0.5, 0); ctx.lineTo(x0 + w0 * 0.5 + w0 * e, 0); ctx.lineTo(x0 + w0 * e, SH); }
    ctx.clip(); drawScene(ctx, B, t); ctx.restore();
  }
  /* transição de capítulo no fill de transição; cover 0.2 s, clear 0.2 s */
  function drawChapterCover(ctx, ph, p) {
    const col = C.transition_fill, st = T.chapter_transition;
    ctx.save(); ctx.fillStyle = col;
    if (st === 'blob_splat') {
      const s = ph === 'in' ? eOut(p) : 1 - eIn(p);
      const cx = ph === 'in' ? SW / 2 - 120 : SW / 2 - 120 + 260 * eIn(p), cy = SH / 2;
      const RS = Math.hypot(SW, SH) / Math.hypot(1920, 1080); ctx.beginPath(); ctx.arc(cx, cy, 1250 * RS * s * 0.95, 0, 7); ctx.fill();
      for (let i = 0; i < 12; i++) { const a = i * 2.39996, d = 1250 * s * (0.72 + 0.2 * hash(i)); ctx.beginPath(); ctx.arc(cx + Math.cos(a) * d * 0.62, cy + Math.sin(a) * d * 0.62, 230 * s * (0.7 + 0.5 * hash(i + 9)), 0, 7); ctx.fill(); }
      for (let i = 0; i < 10; i++) { const a = i * 2.39996 + 1, d = 1250 * s * (1.0 + 0.15 * hash(i + 30)); ctx.beginPath(); ctx.arc(cx + Math.cos(a) * d * 0.62, cy + Math.sin(a) * d * 0.62, 46 * s, 0, 7); ctx.fill(); }
    } else if (st === 'paint_swipe') {
      const e = eIO(p); const x0 = ph === 'in' ? -SW * 1.4 + e * SW * 1.4 : e * SW * 1.4;
      ctx.beginPath(); ctx.moveTo(x0, 0); ctx.lineTo(x0 + SW * 1.2, 0); ctx.lineTo(x0 + SW * 1.4, SH); ctx.lineTo(x0 + SW * 0.2, SH); ctx.fill();
    } else if (st === 'shutter_5_bars') {
      for (let i = 0; i < 5; i++) { const e = eIO(clamp(p * 1.5 - i * 0.12)); const h2 = ph === 'in' ? SH * e : SH * (1 - e); ctx.fillRect(i * SW / 5, ph === 'in' ? 0 : SH - h2, SW / 5 + 1, h2); }
    } else if (st === 'ink_drop') {
      const s = ph === 'in' ? eOut(p) : 1 - eIn(p); ctx.beginPath(); ctx.arc(SW / 2, SH / 2, s * 1150, 0, 7); ctx.fill();
    } else { // page_curl chapado
      const e = eIO(p); const x = ph === 'in' ? SW * (1 - e) : -SW * e;
      ctx.fillRect(x, 0, SW, SH); ctx.fillStyle = C.label_grey; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x - 120 * (1 - e), SH * 0.5); ctx.lineTo(x, SH); ctx.fill();
    }
    ctx.restore();
  }

  // ───────────────────────── builder ─────────────────────────
  function makeBuilder(sh) {
    const add = (it) => { sh.items.push(it); return it; };
    const ev = (t, name, gain = 0) => EV.push({ t: +t.toFixed(3), name, gain });
    const B = {
      at, atEnd, start: sh.start, end: () => sh.start + sh.dur,
      plate(name, o = {}) {
        sh.plate = name; const meta = window.PLATES[name];
        sh.meta = meta; sh.cam = o.cam || [[1.04, 0.5, 0.5], [1.1, 0.5, 0.5]]; sh.tile = meta.kind === 'tile';
        sh.portal = o.portal ? (Array.isArray(o.portal) ? o.portal : meta.portals[o.portal]) : (Object.values(meta.portals || {})[0] || [W * 0.4, H * 0.35, W * 0.2, H * 0.3]);
        sh.night = o.night || 0; sh.tint = o.tint; sh.vignette = o.vignette; sh.snaps = o.snaps || [];
        sh.vf = []; sh.vw = null; sh.vy = 0;
        return B;
      },
      // só no vertical: vf = [[t, x do mundo], ...] para onde a câmera olha; vw = largura de mundo visível; vy = desvio vertical
      vert(o = {}) { if (o.vf) sh.vf = o.vf.slice().sort((a, b) => a[0] - b[0]); if (o.vw) sh.vw = o.vw; if (o.vy) sh.vy = o.vy; return B; },
      char(name, o = {}) {
        const pp = new Puppet(name, Object.assign({ night: sh.night }, o)); sh.chars.push(pp);
        add({ space: 'world', z: 10 + (o.y || 900) / 1000, draw: (c, t) => pp.draw(c, t) });
        if (o.enter != null && o.enter > sh.start + 0.01) { ev(o.enter, 'pop'); add({ space: 'world', z: 11, draw: (c, t) => drawPuff(c, pp.x, (o.y || 900) - 20, t - o.enter, (o.h || 600) * 0.4) }); }
        return pp;
      },
      write(rect, lines, t0, o = {}) { // escreve num blank do próprio plate
        const r = typeof rect === 'string' ? sh.meta.blanks[rect] : rect;
        const colour = o.color ? (C[o.color] || o.color) : C.ink;
        const tmp = document.createElement('canvas').getContext('2d');
        const size = o.size || fitSize(tmp, lines, r[2] * 0.9, r[3] * 0.9);
        let t = t0;
        const starts = lines.map(l => { const s = t; t += entryDur(l) + 0.3; return s; });
        starts.forEach((s, i) => { for (let k = 0; k < lines[i].length; k += 3) ev(s + k / 28, 'tick', -6); });
        const lh = size * 1.18, top = r[1] + (r[3] - lh * lines.length) / 2;
        add({ space: 'world', z: 2, draw: (c, tt) => lines.forEach((l, i) => drawEntry(c, l, r[0] + r[2] / 2, top + lh * (i + 0.82), size, colour, starts[i], tt, 28, 'center')) });
        return t;
      },
      tag(x, y, label, t0, o = {}) { ev(t0, 'pop'); add({ space: 'world', z: 20, draw: (c, t) => drawTag(c, x, y, label, t - t0, o) }); return B; },
      hud(kind, value, t0, o = {}) { ev(t0, 'pop'); add({ space: 'screen', draw: (c, t) => drawHud(c, kind, value, o.slot != null ? o.slot : (kind === 'date' ? 0 : 1), t - t0, o.out != null ? t - o.out : null) }); return B; },
      stamp(text, x, y, t0) { ev(t0 + 0.12, 'thud'); add({ space: 'world', z: 30, draw: (c, t) => drawStamp(c, x, y, text, t - t0) }); return B; },
      x(x, y, size, t0) { ev(t0, 'hit'); ev(t0 + 0.12, 'hit', -3); add({ space: 'world', z: 31, draw: (c, t) => drawX(c, x, y, size, t - t0) }); return B; },
      banner(text, t0, o = {}) { ev(t0, 'whoosh', -4); const col = o.colour === 'accent' || !o.colour ? (window.ACCENT || C.headline_a) : (C[o.colour] || o.colour); add({ space: 'screen', draw: (c, t) => drawBanner(c, text, t - t0, col, o.out != null ? t - o.out : null, o.y) }); return B; },
      number(x, y, label, value, t0, o = {}) { ev(t0, 'pop'); add({ space: o.screen ? 'screen' : 'world', z: 25, draw: (c, t) => drawNumber(c, x, y, label, value, t - t0, o) }); return B; },
      bubble(x, y, text, t0, o = {}) { ev(t0, 'pop'); add({ space: 'world', z: 26, draw: (c, t) => drawBubble(c, x, y, text, t - t0, Object.assign({}, o, { dOut: o.out != null ? t - o.out : null })) }); return B; },
      puff(x, y, t0, size) { ev(t0, 'puff'); add({ space: 'world', z: 27, draw: (c, t) => drawPuff(c, x, y, t - t0, size) }); return B; },
      board(x, y, w, h, lines, t0, o = {}) { ev(t0 + 0.25, 'thud', -6); lines.forEach((l, i) => ev(t0 + 0.35 + i * 0.3, 'tick', -6)); add({ space: o.screen ? 'screen' : 'world', z: 28, draw: (c, t) => drawBoard(c, x, y, w, h, lines, t - t0, o) }); return B; },
      counter(x, y, label, keys, o = {}) {
        keys.forEach(k => ev(k[0], 'ding', -8));
        // vertical: o contador do motivo vira elemento de tela fixo (canto superior direito, acima dos botões do app)
        if (VERT) add({ space: 'screen', z: 24, draw: (c, t) => drawCounter(c, SW - 220, 330, label, keys, t, Object.assign({}, o, { scale: 0.85 })) });
        else add({ space: 'world', z: 24, draw: (c, t) => drawCounter(c, x, y, label, keys, t, o) });
        return B;
      },
      // ícone da CTA que entra com mola na palavra e flutua: kind = like | comment | share | follow
      icon(kind, x, y, t0, o = {}) { ev(t0, 'pop'); add({ space: o.screen ? 'screen' : 'world', z: o.z || 30, draw: (c, t) => {
        const d = t - t0; if (d < 0) return; const sp = Math.min(1, spring(d));
        drawIcon(c, kind, x, y - 12 * Math.sin(t * 3), (o.scale || 0.9) * sp * (1 + 0.06 * Math.sin(t * 5))); } }); return B; },
      custom(fn, o = {}) { add({ space: o.screen ? 'screen' : 'world', z: o.z || 15, draw: fn }); return B; },
      sfx(t, name, gain) { ev(t, name, gain); return B; },
    };
    return B;
  }

  // ───────────────────────── boot e seek ─────────────────────────
  let ctx;
  async function boot() {
    const cv = document.getElementById('c'); ctx = cv.getContext('2d');
    const ff = new FontFace(T.font[0], `url(${window.FONT_URL})`, { weight: '100 900' });
    await ff.load(); document.fonts.add(ff); await document.fonts.ready;
    const jobs = [];
    for (const [name, meta] of Object.entries(window.PLATES)) jobs.push(loadImg('plate:' + name, meta.src));
    for (const r of Object.values(window.RIG)) {
      for (const f of [r.body, ...Object.values(r.heads), ...Object.values(r.whole || {})]) jobs.push(loadImg(f, window.SPRITES + f));
    }
    await Promise.all(jobs);
    SHOTS.sort((a, b) => a.start - b.start);
    const voiceEnd = OFF + window.VOICE_DUR;
    if (STINGS.intro) { // a transição de capítulo revela o título num banner
      const I = STINGS.intro;
      SHOTS[0].opts.chapter = true;
      SHOTS.unshift({ phrase: '[intro]', isIntro: true, start: 0, opts: { transition: 'none' }, build: sh => {
        sh.plate(I.plate, { cam: [[1.04, 0.5, 0.5], [1.1, 0.5, 0.52]], night: I.night || 0 });
        sh.banner(I.title, 0.28, { colour: 'accent', out: I.dur - 0.45 });
        sh.sfx(0.02, 'splat', -4);
      } });
    }
    SHOTS[0].start = 0;
    if (STINGS.outro) { // board com o nome do canal entra balançando
      const O = STINGS.outro;
      SHOTS.push({ phrase: '[outro]', isOutro: true, start: voiceEnd + 0.35, opts: { chapter: true }, build: sh => {
        sh.plate(O.plate, { cam: [[1.08, 0.5, 0.55], [1.03, 0.5, 0.52]], night: O.night || 0 });
        if (VERT) { sh.vert({ vf: [[sh.start, 990]], vw: 820 }); sh.board(690, 250, 540, 220, [O.name], sh.start + 0.3, { size: 64 }); }
        else sh.board(560, 300, 800, 300, [O.name], sh.start + 0.3, { size: 104 });
        if (O.char) { const f = sh.char(O.char, { x: VERT ? 1230 : 1500, y: O.floor || 880, h: 430, pose: 'rest' }); f.pose(sh.start + 0.6, 'wave'); }
      } });
      window.END = +(voiceEnd + 0.35 + O.dur).toFixed(3);
    } else window.END = +(voiceEnd + (window.TAIL || 0.6)).toFixed(3);
    const cuts = [];
    SHOTS.forEach((sh, i) => {
      sh.dur = (i + 1 < SHOTS.length ? SHOTS[i + 1].start : window.END) - sh.start;
      sh.items = []; sh.chars = []; sh.index = i;
      sh.transition = sh.opts.chapter ? 'chapter' : (sh.opts.transition || (i > 0 && i % 6 === 5 ? 'cut' : 'shot'));
      sh.build(makeBuilder(sh));
      if (i > 0) {
        if (sh.transition === 'cut') cuts.push(sh.start);
        else if (sh.transition === 'chapter') { EV.push({ t: +(sh.start - 0.22).toFixed(3), name: 'whoosh', gain: 0 }); EV.push({ t: +(sh.start - 0.02).toFixed(3), name: 'splat', gain: -3 }); }
        else EV.push({ t: +(sh.start - 0.02).toFixed(3), name: 'whoosh', gain: -2 });
      }
    });
    window.CUTS = cuts; window.VOICE_END = voiceEnd; window.EV = EV.sort((a, b) => a.t - b.t); window.SHOTS = SHOTS.map(s => ({ start: s.start, dur: s.dur, plate: s.plate, transition: s.transition, phrase: s.phrase }));
    window.READY = true;
  }

  function render(c, t) {
    const i = shotAt(t), sh = SHOTS[i], d = t - sh.start, trD = R.shot_transition_s;
    c.save(); c.fillStyle = '#000'; c.fillRect(0, 0, SW, SH);
    const next = SHOTS[i + 1];
    if (next && next.transition === 'chapter' && next.start - t < 0.2) { drawScene(c, sh, t); drawChapterCover(c, 'in', 1 - (next.start - t) / 0.2); }
    else if (sh.isIntro && d < 0.2) { drawScene(c, sh, t); drawChapterCover(c, 'out', d / 0.2); }
    else if (i > 0 && sh.transition === 'chapter' && d < 0.2) { drawScene(c, sh, t); drawChapterCover(c, 'out', d / 0.2); }
    else if (i > 0 && sh.transition === 'shot' && d < trD) {
      const A = SHOTS[i - 1], p = d / trD, st = T.shot_transition;
      if (st === 'zoom_through') drawZoomThrough(c, A, sh, t, p);
      else if (st === 'push_horizontal') drawPush(c, A, sh, t, p, false);
      else if (st === 'push_vertical') drawPush(c, A, sh, t, p, true);
      else if (st === 'circle_iris') drawIris(c, A, sh, t, p);
      else drawSlats(c, A, sh, t, p);
    } else drawScene(c, sh, t);
    c.restore();
  }

  // ───────────────────────── legendas (só no vertical) ─────────────────────────
  let CAPS = null;
  function buildCaptions() {
    const ws = window.WORDS, out = []; let cur = [];
    const flush = () => { if (cur.length) out.push(cur); cur = []; };
    ws.forEach((w, i) => {
      const gap = i > 0 ? w.s - ws[i - 1].e : 0;
      const chars = cur.reduce((a, x) => a + x.w.length + 1, 0) + w.w.length;
      if (cur.length && (cur.length >= 3 || chars > 15 || gap > 0.25)) flush();
      cur.push(w);
    });
    flush();
    return out.map((g, i) => ({ words: g, s: g[0].s, e: i + 1 < out.length ? Math.min(out[i + 1][0].s, g[g.length - 1].e + 0.6) : g[g.length - 1].e + 0.4 }));
  }
  function drawCaptions(c, t) {
    if (!window.CAPTIONS) return;
    if (!CAPS) CAPS = buildCaptions();
    const cap = CAPS.find(k => t >= k.s && t < k.e); if (!cap) return;
    const size = 70, y = SH * 0.74;
    c.save(); c.font = font(size);
    const parts = cap.words.map(w => w.w.toUpperCase()); const space = c.measureText(' ').width;
    const widths = parts.map(x => c.measureText(x).width); const tw = widths.reduce((a, b) => a + b, 0) + space * (parts.length - 1);
    const s = pop(t - cap.s), w = tw + 70, h = size * 1.5;
    c.translate(SW / 2, y); c.scale(s, s);
    drawCard(c, -w / 2, -h / 2, w, h, { seed: 5 });
    let x = -tw / 2; c.textBaseline = 'middle';
    parts.forEach((p, i) => { c.fillStyle = t >= cap.words[i].s ? (t < cap.words[i].e + 0.05 ? C.alert : C.ink) : C.label_grey; c.fillText(p, x, 4); x += widths[i] + space; });
    c.restore();
  }

  window.seek = function (t) { render(ctx, t); drawCaptions(ctx, t); };
  // motion blur: N subframes em meio frame, média corrida; não atravessa cortes
  let scratch;
  window.renderBlur = function (t, n = 4, span = 0.5 / 30) {
    if (!scratch) { scratch = document.createElement('canvas'); scratch.width = SW; scratch.height = SH; }
    const sc = scratch.getContext('2d');
    const hard = [...window.CUTS, ...SHOTS.filter(s => s.transition === 'chapter').map(s => s.start)];
    // janelas de transição se movem muito por frame: mais amostras, senão vira cópia-fantasma
    const fast = SHOTS.some(s => s.transition === 'shot' && t >= s.start - 0.02 && t < s.start + R.shot_transition_s + 0.02);
    if (fast) n = 14;
    for (let k = 0; k < n; k++) {
      let ti = t + (k / n) * span;
      for (const cut of hard) if (t < cut && ti >= cut) ti = cut - 1e-4;
      render(sc, ti);
      ctx.globalAlpha = 1 / (k + 1); ctx.drawImage(scratch, 0, 0);
    }
    ctx.globalAlpha = 1;
    drawCaptions(ctx, t);
  };
  // para os shots: fonte do DNA (font(px)) e cor com alpha (rgba(hex, a)) — nunca escreva nome de fonte/hex fixo
  const rgba = (hex, a) => { const h = hex.replace('#', ''); return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`; };
  window.ENGINE = { boot, at, atEnd, POSES, C, T, VERT, SW, SH, font, rgba };
})();
