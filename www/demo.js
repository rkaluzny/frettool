(function () {
  'use strict';

  const TITLE_MAX = 60;
  const DESC_MAX = 250;

  let STRING_COUNT = 6;
  let NUM_FRETS = 12;
  const S_SPACE = 55;
  const F_SPACE = 65;
  const M_TOP = 70;
  const M_BOTTOM = 50;
  const M_SIDE = 50;
  const DOT_R = 14;
  const SMALL_R = 8;
  const MARKER_R = 8;
  const BARRE_HW = 14;
  const BARRE_MR = 3;
  const HIT_R = 20;

  const PRESET_COLORS = ['#4c6ef5', '#4cc9f0', '#7c5cff', '#f97316', '#22d3ee'];
  const FRET_MARKERS = { 3: 1, 5: 1, 7: 1, 9: 1, 12: 2 };

  const COLORS = {
    bg: '#1a2046', surface: '#1f2547', string: '#b9bee0',
    fretLine: '#4a5080', nut: '#cfd3ea', dotDefault: '#4c6ef5',
    dotHover: '#7d8bf7', dotSelected: '#ff6b6b', marker: '#6a6f9c',
    text: '#f1eeeb', textMuted: '#a9b0d6',
  };

  const canvas = document.getElementById('fretboardCanvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  const chordName = document.getElementById('chordName');
  const titleCounter = document.getElementById('titleCounter');
  const chordDesc = document.getElementById('chordDesc');
  const descCounter = document.getElementById('descCounter');
  const instrumentSel = document.getElementById('instrumentSel');
  const fretRange = document.getElementById('fretRange');
  const stringRange = document.getElementById('stringRange');
  const fretVal = document.getElementById('fretVal');
  const stringVal = document.getElementById('stringVal');
  const undoBtn = document.getElementById('undoBtn');
  const redoBtn = document.getElementById('redoBtn');
  const clearBtn = document.getElementById('clearBtn');

  let pos = new Set();
  let xPos = new Set();
  let dotTypes = {};
  let dotSmall = {};
  let dotColors = {};
  let dotTexts = {};
  let labels = {};
  let barreExcluded = new Set();
  let selectedBarreKey = null;
  let hoveredPos = null;
  let hoveredX = null;
  let hoveredBarreKey = null;
  let gridHover = null;

  // --- Undo / Redo ---
  let history = [];
  let future = [];

  function snapshot() {
    return JSON.stringify({
      pos: [...pos], xPos: [...xPos],
      dotTypes, dotSmall, dotColors, dotTexts,
      labels, barreExcluded: [...barreExcluded],
      NUM_FRETS, STRING_COUNT,
    });
  }

  function restore(s) {
    const d = JSON.parse(s);
    pos = new Set(d.pos);
    xPos = new Set(d.xPos);
    dotTypes = d.dotTypes;
    dotSmall = d.dotSmall;
    dotColors = d.dotColors;
    dotTexts = d.dotTexts;
    labels = d.labels;
    barreExcluded = new Set(d.barreExcluded);
    NUM_FRETS = d.NUM_FRETS;
    STRING_COUNT = d.STRING_COUNT;
    selectedBarreKey = null;
    fretRange.value = NUM_FRETS;
    stringRange.value = STRING_COUNT;
    fretVal.textContent = NUM_FRETS;
    stringVal.textContent = STRING_COUNT;
    instrumentSel.value = STRING_COUNT + ',' + NUM_FRETS;
  }

  function pushHistory() {
    history.push(snapshot());
    future = [];
    updateHistoryButtons();
  }

  function undo() {
    if (!history.length) return;
    future.push(snapshot());
    restore(history.pop());
    draw();
    updateHistoryButtons();
  }

  function redo() {
    if (!future.length) return;
    history.push(snapshot());
    restore(future.pop());
    draw();
    updateHistoryButtons();
  }

  function updateHistoryButtons() {
    undoBtn.disabled = history.length === 0;
    redoBtn.disabled = future.length === 0;
  }

  function key(s, f) { return s + ',' + f; }

  function getBarreGroups() {
    if (STRING_COUNT < 2) return [];
    let byFret = {};
    for (let p of pos) {
      let [s, f] = p.split(',').map(Number);
      if (!byFret[f]) byFret[f] = [];
      byFret[f].push(s);
    }
    let groups = [];
    for (let f in byFret) {
      f = parseInt(f);
      let strings = byFret[f].sort((a, b) => a - b);
      let runs = [];
      let cur = [strings[0]];
      for (let i = 1; i < strings.length; i++) {
        if (strings[i] === strings[i - 1] + 1 &&
            dotTypes[key(strings[i], f)] !== 'square' &&
            dotTypes[key(strings[i], f)] !== 'triangle' &&
            !dotSmall[key(strings[i], f)] &&
            dotTypes[key(strings[i - 1], f)] !== 'square' &&
            dotTypes[key(strings[i - 1], f)] !== 'triangle' &&
            !dotSmall[key(strings[i - 1], f)]) {
          cur.push(strings[i]);
        } else {
          if (cur.length >= 2) runs.push(cur);
          cur = [strings[i]];
        }
      }
      if (cur.length >= 2) runs.push(cur);
      for (let run of runs) {
        run = run.filter(s => !barreExcluded.has(key(s, f)));
        if (run.length >= 2) {
          let groupKey = 'f' + f + '_s' + run[0] + '-' + run[run.length - 1];
          groups.push({
            key: groupKey, fret: f, strings: run,
            startString: run[0], endString: run[run.length - 1],
            notes: run.map(s => [s, f]),
            color: dotColors[key(run[0], f)] || COLORS.dotDefault,
            labels: {},
            getLabel: function (s) { return dotTexts[key(s, this.fret)] || ''; },
          });
        }
      }
    }
    for (let g of groups) {
      g.color = dotColors[key(g.notes[0][0], g.notes[0][1])] || COLORS.dotDefault;
      for (let [s, f] of g.notes) {
        let lbl = dotTexts[key(s, f)];
        if (lbl) g.labels[s] = lbl;
      }
    }
    return groups;
  }

  function getBarrePositions() {
    let s = new Set();
    for (let g of getBarreGroups()) {
      for (let p of g.notes) s.add(key(p[0], p[1]));
    }
    return s;
  }

  function isInBarre(s, f) {
    for (let g of getBarreGroups()) {
      if (g.fret === f && g.strings.includes(s)) return g;
    }
    return null;
  }

  function getGridPos(mx, my) {
    let fw = (w - 2 * M_SIDE) / NUM_FRETS;
    let sh = (h - M_TOP - M_BOTTOM) / (STRING_COUNT - 1);
    if (mx < M_SIDE - 10) {
      let si = Math.round((my - M_TOP) / sh);
      if (si >= 0 && si < STRING_COUNT) return [si, 0];
    }
    if (mx < M_SIDE || mx > w - M_SIDE) return null;
    let si = Math.round((my - M_TOP) / sh);
    let fi = Math.round((mx - M_SIDE) / fw);
    if (fi < 1) fi = 1;
    if (fi > NUM_FRETS) fi = NUM_FRETS;
    if (si >= 0 && si < STRING_COUNT && fi >= 1 && fi <= NUM_FRETS) return [si, fi];
    return null;
  }

  function inRange(s, f) {
    return s >= 0 && s < STRING_COUNT && f >= 0 && f <= NUM_FRETS;
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);

    let fw = (w - 2 * M_SIDE) / NUM_FRETS;
    let sh = (h - M_TOP - M_BOTTOM) / (STRING_COUNT - 1);

    // Background board
    let grad = ctx.createLinearGradient(0, M_TOP - 10, 0, h - M_BOTTOM + 10);
    grad.addColorStop(0, '#232a52');
    grad.addColorStop(1, '#1a2046');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect(M_SIDE - 10, M_TOP - 10, w - 2 * M_SIDE + 20, h - M_TOP - M_BOTTOM + 20, 8);
    ctx.fill();

    // Grid hover preview
    if (gridHover) {
      let [s, f] = gridHover;
      let cx = M_SIDE + (f - 0.5) * fw;
      let cy = M_TOP + s * sh;
      ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.arc(cx, cy, DOT_R, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.dotHover;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Strings
    for (let i = 0; i < STRING_COUNT; i++) {
      let y = M_TOP + i * sh;
      ctx.beginPath();
      ctx.moveTo(M_SIDE, y);
      ctx.lineTo(w - M_SIDE, y);
      ctx.strokeStyle = COLORS.string;
      ctx.lineWidth = 2 + i * 0.6;
      ctx.stroke();
    }

    // Frets
    for (let i = 0; i <= NUM_FRETS; i++) {
      let x = M_SIDE + i * fw;
      let lw = (i === 0) ? 8 : 2.5;
      ctx.beginPath();
      ctx.moveTo(x, M_TOP);
      ctx.lineTo(x, h - M_BOTTOM);
      ctx.strokeStyle = (i === 0) ? COLORS.nut : COLORS.fretLine;
      ctx.lineWidth = lw;
      ctx.stroke();
      if (i > 0 && i % 2 === 0) {
        ctx.fillStyle = COLORS.textMuted;
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(String(i), x - fw / 2, h - 20);
      }
    }

    // Fret markers
    for (let fn in FRET_MARKERS) {
      fn = parseInt(fn);
      if (fn > NUM_FRETS) continue;
      let x = M_SIDE + (fn - 0.5) * fw;
      let cnt = FRET_MARKERS[fn];
      ctx.fillStyle = COLORS.marker;
      if (cnt === 1) {
        let y = M_TOP + (STRING_COUNT - 1) * sh / 2;
        ctx.beginPath();
        ctx.arc(x, y, MARKER_R, 0, Math.PI * 2);
        ctx.fill();
      } else {
        let y1 = M_TOP + (STRING_COUNT - 1) * sh * 0.3;
        let y2 = M_TOP + (STRING_COUNT - 1) * sh * 0.7;
        for (let y of [y1, y2]) {
          ctx.beginPath();
          ctx.arc(x, y, MARKER_R, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    // Fret labels
    for (let fn in labels) {
      fn = parseInt(fn);
      if (fn > 0 && fn <= NUM_FRETS) {
        let x = M_SIDE + (fn - 0.5) * fw;
        let y = M_TOP - 16;
        ctx.fillStyle = COLORS.text;
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(labels[fn], x, y);
      }
    }

    // X markers
    for (let p of xPos) {
      let [s, f] = p.split(',').map(Number);
      let cx, cy;
      if (f === 0) { cx = M_SIDE - 25; cy = M_TOP + s * sh; }
      else { cx = M_SIDE + (f - 0.5) * fw; cy = M_TOP + s * sh; }
      if (hoveredX && hoveredX[0] === s && hoveredX[1] === f) {
        ctx.strokeStyle = COLORS.dotHover;
        ctx.lineWidth = 2;
        ctx.strokeRect(cx - HIT_R - 4, cy - HIT_R - 4, HIT_R * 2 + 8, HIT_R * 2 + 8);
      }
      ctx.fillStyle = COLORS.dotSelected;
      ctx.font = 'bold 18px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('X', cx, cy);
    }

    // Barre groups (draw first so dots are on top)
    let barreG = getBarreGroups();
    let barrePosK = new Set();
    for (let g of barreG) {
      for (let [s, f] of g.notes) barrePosK.add(key(s, f));
    }

    for (let g of barreG) {
      drawBarre(g, fw, sh);
    }

    // Dots
    for (let p of pos) {
      let [s, f] = p.split(',').map(Number);
      let pk = key(s, f);
      if (barrePosK.has(pk) && f > 0) continue;

      let cx, cy;
      if (f === 0) { cx = M_SIDE - 25; cy = M_TOP + s * sh; }
      else { cx = M_SIDE + (f - 0.5) * fw; cy = M_TOP + s * sh; }

      let isSmall = !!dotSmall[pk];
      let baseR = isSmall ? SMALL_R : DOT_R;
      let sc = introScale(pk);
      let r = baseR * sc;
      let color = dotColors[pk] || COLORS.dotDefault;
      let type = dotTypes[pk] || 'circle';

      // Hover glow
      if (hoveredPos && hoveredPos[0] === s && hoveredPos[1] === f) {
        ctx.strokeStyle = COLORS.dotHover;
        ctx.lineWidth = 2;
        ctx.strokeRect(cx - r - 4, cy - r - 4, r * 2 + 8, r * 2 + 8);
      }

      ctx.fillStyle = color;
      ctx.strokeStyle = 'rgba(255,255,255,0.85)';
      ctx.lineWidth = 2;

      if (type === 'square' || isSmall) {
        ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
        ctx.strokeRect(cx - r, cy - r, r * 2, r * 2);
      } else if (type === 'triangle') {
        ctx.beginPath();
        ctx.moveTo(cx, cy - r);
        ctx.lineTo(cx - r, cy + r);
        ctx.lineTo(cx + r, cy + r);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }

      let label = dotTexts[pk] || '';
      if (label) {
        let lum = luminance(color);
        ctx.fillStyle = lum > 0.62 ? '#0e1230' : '#f1eeeb';
        let fs = label.length > 1 ? 10 : 13;
        ctx.font = 'bold ' + fs + 'px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, cx, cy + 1);
      }
    }

    // Barre dot markers (for dots inside barres)
    for (let g of barreG) {
      let cx = M_SIDE + (g.fret - 0.5) * fw;
      for (let s of g.strings) {
        let cy = M_TOP + s * sh;
        let pk = key(s, g.fret);
        let lbl = g.labels[s] || '';
        if (!lbl) {
          ctx.beginPath();
          ctx.arc(cx, cy, (BARRE_MR + 1) * introScale(pk), 0, Math.PI * 2);
          ctx.fillStyle = g.color;
          ctx.fill();
          ctx.strokeStyle = 'rgba(255,255,255,0.85)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
        if (lbl) {
          let lum = luminance(g.color);
          ctx.fillStyle = lum > 0.62 ? '#0e1230' : '#f1eeeb';
          let fs = lbl.length > 1 ? 9 : 11;
          ctx.font = 'bold ' + fs + 'px sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(lbl, cx, cy);
        }
      }
    }
  }

  function drawBarre(g, fw, sh) {
    let cx = M_SIDE + (g.fret - 0.5) * fw;
    let half = BARRE_HW;
    let topY = M_TOP + g.startString * sh;
    let botY = M_TOP + g.endString * sh;
    let left = cx - half;
    let right = cx + half;
    let top = topY - half;
    let bottom = botY + half;
    let capD = half * 2;

    let sel = selectedBarreKey === g.key;
    let hov = hoveredBarreKey === g.key;
    let outline = sel || hov;

    ctx.fillStyle = g.color;

    // Body
    if (bottom - top > capD) {
      ctx.fillRect(left, top + half, half * 2, bottom - top - capD);
    }

    // Top cap
    ctx.beginPath();
    ctx.ellipse(cx, top + half, half, half, 0, 0, Math.PI * 2);
    ctx.fill();

    // Bottom cap
    ctx.beginPath();
    ctx.ellipse(cx, bottom - half, half, half, 0, 0, Math.PI * 2);
    ctx.fill();

    if (outline) {
      ctx.strokeStyle = sel ? COLORS.dotSelected : COLORS.dotHover;
      ctx.lineWidth = sel ? 3 : 2;
      ctx.strokeRect(left - 1, top - 1, half * 2 + 2, bottom - top + 2);
    }
  }

  function luminance(hex) {
    let c = hex.replace('#', '');
    if (c.length < 6) return 0.5;
    let r = parseInt(c.substr(0, 2), 16) / 255;
    let g = parseInt(c.substr(2, 2), 16) / 255;
    let b = parseInt(c.substr(4, 2), 16) / 255;
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  function pruneOutOfRange() {
    for (let p of [...pos]) {
      let [s, f] = p.split(',').map(Number);
      if (!inRange(s, f)) { pos.delete(p); delete dotTypes[p]; delete dotSmall[p]; delete dotColors[p]; delete dotTexts[p]; }
    }
    for (let p of [...xPos]) {
      let [s, f] = p.split(',').map(Number);
      if (!inRange(s, f)) xPos.delete(p);
    }
  }

  function updateCounters() {
    titleCounter.textContent = chordName.value.length + ' / ' + TITLE_MAX;
    descCounter.textContent = chordDesc.value.length + ' / ' + DESC_MAX;
  }

  chordName.addEventListener('input', function () {
    if (this.value.length > TITLE_MAX) this.value = this.value.slice(0, TITLE_MAX);
    updateCounters();
  });

  chordDesc.addEventListener('input', function () {
    if (this.value.length > DESC_MAX) this.value = this.value.slice(0, DESC_MAX);
    updateCounters();
  });

  // --- Controls ---
  instrumentSel.addEventListener('change', function () {
    let [sc, nf] = this.value.split(',').map(Number);
    pushHistory();
    STRING_COUNT = sc;
    NUM_FRETS = nf;
    fretRange.value = nf;
    stringRange.value = sc;
    fretVal.textContent = nf;
    stringVal.textContent = sc;
    selectedBarreKey = null;
    pruneOutOfRange();
    draw();
  });

  fretRange.addEventListener('input', function () {
    NUM_FRETS = parseInt(this.value);
    fretVal.textContent = NUM_FRETS;
    draw();
  });
  fretRange.addEventListener('change', function () {
    pushHistory();
    pruneOutOfRange();
    draw();
  });

  stringRange.addEventListener('input', function () {
    STRING_COUNT = parseInt(this.value);
    stringVal.textContent = STRING_COUNT;
    draw();
  });
  stringRange.addEventListener('change', function () {
    pushHistory();
    pruneOutOfRange();
    draw();
  });

  undoBtn.addEventListener('click', undo);
  redoBtn.addEventListener('click', redo);
  clearBtn.addEventListener('click', function () {
    if (!pos.size && !xPos.size) return;
    pushHistory();
    pos = new Set();
    xPos = new Set();
    dotTypes = {}; dotSmall = {}; dotColors = {}; dotTexts = {};
    labels = {}; barreExcluded = new Set();
    selectedBarreKey = null;
    draw();
  });

  // --- Mouse handling ---
  let lastDown = { button: -1, time: 0 };
  let mousePos = { x: 0, y: 0 };

  canvas.addEventListener('mousemove', function (e) {
    let rect = canvas.getBoundingClientRect();
    let scaleX = canvas.width / rect.width;
    let scaleY = canvas.height / rect.height;
    mousePos.x = (e.clientX - rect.left) * scaleX;
    mousePos.y = (e.clientY - rect.top) * scaleY;
    updateHover(mousePos.x, mousePos.y);
  });

  canvas.addEventListener('mouseleave', function () {
    hoveredPos = null;
    hoveredX = null;
    hoveredBarreKey = null;
    gridHover = null;
    canvas.style.cursor = 'default';
    draw();
  });

  function updateHover(mx, my) {
    let oldH = hoveredPos, oldX = hoveredX, oldB = hoveredBarreKey, oldG = gridHover;
    hoveredPos = null; hoveredX = null; hoveredBarreKey = null; gridHover = null;

    let gp = getGridPos(mx, my);
    if (gp) {
      let [s, f] = gp;
      let pk = key(s, f);
      if (xPos.has(pk)) {
        hoveredX = [s, f];
      } else if (pos.has(pk)) {
        let bg = isInBarre(s, f);
        if (bg) {
          hoveredBarreKey = bg.key;
          hoveredPos = [s, f];
        } else {
          hoveredPos = [s, f];
        }
      } else {
        gridHover = [s, f];
      }
    }

    // Also check barre hitboxes
    for (let g of getBarreGroups()) {
      let fw = (w - 2 * M_SIDE) / NUM_FRETS;
      let sh = (h - M_TOP - M_BOTTOM) / (STRING_COUNT - 1);
      let cx = M_SIDE + (g.fret - 0.5) * fw;
      let xPad = Math.max(18, fw * 0.22);
      let yPad = Math.max(14, sh * 0.22);
      let half = BARRE_HW;
      let topY = M_TOP + g.startString * sh;
      let botY = M_TOP + g.endString * sh;
      let left = cx - half - xPad;
      let right = cx + half + xPad;
      let top = topY - half - yPad;
      let bottom = botY + half + yPad;
      if (mx >= left && mx <= right && my >= top && my <= bottom) {
        if (!hoveredPos) hoveredBarreKey = g.key;
      }
    }

    canvas.style.cursor = (hoveredPos || hoveredX || hoveredBarreKey || gridHover) ? 'pointer' : 'default';

    if (oldH !== hoveredPos || oldX !== hoveredX || oldB !== hoveredBarreKey || oldG !== gridHover) {
      draw();
    }
  }

  canvas.addEventListener('click', function (e) {
    let gp = getGridPos(mousePos.x, mousePos.y);
    if (!gp) return;
    let [s, f] = gp;
    let pk = key(s, f);

    // Check for X marker click -> remove
    if (xPos.has(pk)) {
      pushHistory();
      xPos.delete(pk);
      draw();
      return;
    }

    // Click on existing dot
    if (pos.has(pk)) {
      pushHistory();
      let bg = isInBarre(s, f);
      if (bg) {
        if (selectedBarreKey === bg.key) {
          // Remove this note from barre
          pos.delete(pk);
          delete dotTypes[pk];
          delete dotSmall[pk];
          delete dotColors[pk];
          delete dotTexts[pk];
          selectedBarreKey = null;
        } else {
          selectedBarreKey = bg.key;
        }
      } else {
        pos.delete(pk);
        delete dotTypes[pk];
        delete dotSmall[pk];
        delete dotColors[pk];
        delete dotTexts[pk];
      }
      draw();
      return;
    }

    // Place new dot
    if (f === 0) return;
    pushHistory();
    pos.add(pk);
    xPos.delete(pk);
    dotColors[pk] = COLORS.dotDefault;

    let ctrl = e.ctrlKey || e.metaKey;
    let shift = e.shiftKey;
    let alt = e.altKey;

    if (ctrl && shift) dotTypes[pk] = 'square';
    else if (ctrl) dotTypes[pk] = 'square';
    else if (shift) dotTypes[pk] = 'triangle';
    else dotTypes[pk] = 'circle';

    dotSmall[pk] = !!alt;
    selectedBarreKey = null;
    draw();
  });

  canvas.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    let gp = getGridPos(mousePos.x, mousePos.y);
    if (!gp) return;
    let [s, f] = gp;
    let pk = key(s, f);

    // Right-click on existing dot -> properties
    if (pos.has(pk)) {
      pushHistory();
      let currLbl = dotTexts[pk] || '';
      let lbl = prompt('Label (max 2 chars):', currLbl);
      if (lbl !== null) {
        lbl = lbl.trim().slice(0, 2);
        if (lbl) dotTexts[pk] = lbl;
        else delete dotTexts[pk];
      }
      draw();
      return;
    }

    // Right-click on existing X -> remove
    if (xPos.has(pk)) {
      pushHistory();
      xPos.delete(pk);
      selectedBarreKey = null;
      draw();
      return;
    }

    // Right-click on empty -> add X
    pushHistory();
    xPos.add(pk);
    pos.delete(pk);
    delete dotTypes[pk];
    delete dotSmall[pk];
    delete dotColors[pk];
    delete dotTexts[pk];
    draw();
  });

  canvas.addEventListener('dblclick', function (e) {
    let fw = (w - 2 * M_SIDE) / NUM_FRETS;
    if (mousePos.y < M_TOP - 10) {
      let fi = Math.round((mousePos.x - M_SIDE) / fw);
      if (fi >= 1 && fi <= NUM_FRETS) {
        pushHistory();
        let curr = labels[String(fi)] || '';
        let lbl = prompt('Label for fret ' + fi + ':', curr);
        if (lbl !== null) {
          if (lbl.trim()) labels[String(fi)] = lbl.trim();
          else delete labels[String(fi)];
        }
        draw();
      }
    }
  });

  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    let dir = e.deltaY < 0 ? 1 : -1;
    if (dir === 0) return;

    let themeDot = COLORS.dotDefault;
    let presets = PRESET_COLORS.filter(c => c !== themeDot).concat([themeDot]);

    if (hoveredBarreKey) {
      let bg = getBarreGroups().find(g => g.key === hoveredBarreKey);
      if (!bg || !bg.notes.length) return;
      pushHistory();
      let [s0, f0] = bg.notes[0];
      let ck = key(s0, f0);
      let cur = dotColors[ck] || COLORS.dotDefault;
      let idx = presets.indexOf(cur);
      if (idx < 0) idx = 0;
      let nidx = (idx + dir + presets.length) % presets.length;
      let nc = presets[nidx];
      for (let [s, f] of bg.notes) dotColors[key(s, f)] = nc;
      draw();
      return;
    }

    if (hoveredPos) {
      pushHistory();
      let [s, f] = hoveredPos;
      let pk = key(s, f);
      let cur = dotColors[pk] || COLORS.dotDefault;
      let idx = presets.indexOf(cur);
      if (idx < 0) idx = 0;
      let nidx = (idx + dir + presets.length) % presets.length;
      dotColors[pk] = presets[nidx];
      draw();
    }
  }, { passive: false });

  document.addEventListener('keydown', function (e) {
    const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);
    if (typing) return;

    if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
      e.preventDefault();
      if (e.shiftKey) redo(); else undo();
      return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || e.key === 'Y')) {
      e.preventDefault();
      redo();
      return;
    }

    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (hoveredPos) {
        e.preventDefault();
        pushHistory();
        let [s, f] = hoveredPos;
        let pk = key(s, f);
        pos.delete(pk);
        delete dotTypes[pk];
        delete dotSmall[pk];
        delete dotColors[pk];
        delete dotTexts[pk];
        selectedBarreKey = null;
        draw();
      }
    }

    // Barre split: select a barre, hover a string, press up/down to split
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      if (selectedBarreKey && hoveredPos) {
        let [s, f] = hoveredPos;
        let bg = isInBarre(s, f);
        if (bg) {
          e.preventDefault();
          pushHistory();
          let pk = key(s, f);
          if (barreExcluded.has(pk)) barreExcluded.delete(pk);
          else barreExcluded.add(pk);
          selectedBarreKey = null;
          draw();
        }
      }
    }
  });

  // --- Intro showcase animation ---
  let introActive = false;
  let introStart = 0;
  let introOrder = {};
  const INTRO_DELAY = 110;
  const INTRO_DUR = 420;

  function easeOutBack(x) {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  }

  function introScale(pk) {
    if (!introActive) return 1;
    const idx = introOrder[pk] !== undefined ? introOrder[pk] : 0;
    const t = (performance.now() - introStart - idx * INTRO_DELAY) / INTRO_DUR;
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    return easeOutBack(t);
  }

  function startIntro() {
    const sample = [
      { s: 0, f: 0, t: 'circle',  c: '#4cc9f0', l: '' },
      { s: 1, f: 1, t: 'triangle',c: '#4c6ef5', l: '1' },
      { s: 2, f: 0, t: 'circle',  c: '#4c6ef5', l: '' },
      { s: 3, f: 2, t: 'square',  c: '#4c6ef5', l: '2' },
      { s: 4, f: 3, t: 'circle',  c: '#7c5cff', l: '3' },
      { s: 5, f: 3, t: 'circle',  c: '#7c5cff', l: '3' },
    ];
    pos = new Set();
    dotTypes = {}; dotSmall = {}; dotColors = {}; dotTexts = {}; labels = {}; barreExcluded = new Set();
    let i = 0;
    for (let n of sample) {
      let k = key(n.s, n.f);
      pos.add(k);
      dotTypes[k] = n.t;
      dotColors[k] = n.c;
      if (n.l) dotTexts[k] = n.l;
      introOrder[k] = i++;
    }
    chordName.value = 'C major';
    titleCounter.textContent = chordName.value.length + ' / ' + TITLE_MAX;
    introActive = true;
    introStart = performance.now();
    requestAnimationFrame(introLoop);
  }

  function introLoop() {
    draw();
    let span = Object.keys(introOrder).length * INTRO_DELAY + INTRO_DUR + 60;
    if (introActive && performance.now() - introStart < span) {
      requestAnimationFrame(introLoop);
    } else {
      introActive = false;
      draw();
    }
  }

  window.addEventListener('pointerdown', function () { introActive = false; }, true);
  window.addEventListener('keydown', function () { introActive = false; }, true);

  // --- Scroll reveal (covers the rest of the page) ---
  const revealEls = document.querySelectorAll(
    '.section-title, .section-desc, .feature-card, ' +
    '.demo-header, .fretboard-wrap, .demo-desc, ' +
    '.help-item, .download-card, .dl-note, .wave-divider, .tool-group, .footer'
  );
  const stagger = {};
  revealEls.forEach(function (el) {
    el.classList.add('reveal');
    let delay = 0;
    if (el.classList.contains('feature-card') || el.classList.contains('download-card')) {
      stagger.card = (stagger.card || 0);
      delay = (stagger.card++ % 3) * 90;
    } else if (el.classList.contains('help-item')) {
      stagger.help = (stagger.help || 0);
      delay = (stagger.help++) * 55;
    } else if (el.classList.contains('tool-group')) {
      stagger.tool = (stagger.tool || 0);
      delay = (stagger.tool++) * 70;
    } else if (el.classList.contains('wave-divider')) {
      delay = 0;
    }
    if (delay) el.style.transitionDelay = delay + 'ms';
  });
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  // --- Cursor tilt ---
  function attachTilt(el, max) {
    el.addEventListener('mousemove', function (e) {
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      el.style.transform = 'perspective(800px) rotateY(' + (px * max) + 'deg) rotateX(' + (-py * max) + 'deg) translateY(-6px)';
    });
    el.addEventListener('mouseleave', function () { el.style.transform = ''; });
  }
  document.querySelectorAll('.feature-card, .download-card').forEach(function (el) { attachTilt(el, 7); });

  // --- Hamburger menu ---
  const hamburger = document.querySelector('.hamburger');
  const mainNav = document.getElementById('mainNav');
  if (hamburger && mainNav) {
    hamburger.addEventListener('click', function () {
      var isOpen = mainNav.classList.toggle('open');
      hamburger.classList.toggle('active');
      hamburger.setAttribute('aria-expanded', String(isOpen));
    });
    mainNav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        mainNav.classList.remove('open');
        hamburger.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mainNav.classList.contains('open')) {
        mainNav.classList.remove('open');
        hamburger.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Initial draw
  updateCounters();
  updateHistoryButtons();
  startIntro();
})();
