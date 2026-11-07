/* cs-cert.js: the drawing engines that stay JavaScript (the old web/pages/_shared.html + the seal from web/app.js).
   window.CS:
     CS.seal(size, label)     the Institute's gold seal (SVG string)
     CS.cert(c)               the 1000x707 certificate (fixed paper colours in both themes); c = {holder, credential,
                              code, issued, status, demo, modules, track}
     CS.fitCert(wrap)         scale a .cs-cert-wrap's certificate to the wrapper's width; returns a cleanup function
     CS.ring(pct, size, label) a progress ring (SVG string)
     CS.confetti()            gold confetti (skipped under reduced motion)
     CS.today()               the browser's local date, YYYY-MM-DD (streaks and due dates follow the member's day)
     CS.fmtDate(iso, style)   'short' (6 Nov 2026), 'long' (6 November 2026), 'month' (November 2026), 'time' (6 Nov, 14:05)
     CS.verifyUrl(code)       the public verification address of a credential
   Python reaches these through client_code/cs.py and the Certificate / Seal / Ring components. */
(function () {
  'use strict';
  var CS = window.CS = window.CS || {};
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  CS.today = function () {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  };
  CS.fmtDate = function (iso, style) {
    if (!iso) return '';
    var d = iso.length <= 10 ? new Date(iso + 'T12:00:00') : new Date(iso);
    if (isNaN(d.getTime())) return '';
    if (style === 'time') return d.toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    var opts = style === 'long' ? { day: 'numeric', month: 'long', year: 'numeric' }
      : style === 'month' ? { month: 'long', year: 'numeric' } : { day: 'numeric', month: 'short', year: 'numeric' };
    return d.toLocaleDateString(undefined, opts);
  };
  CS.weekday = function (day) { return 'SMTWTFS'[new Date(day + 'T12:00:00').getDay()]; };
  CS.verifyUrl = function (code) { return location.origin + location.pathname + '#verify/' + encodeURIComponent(code); };

  /* The institute's seal (SVG, gold), used in the footer, on certificates and on the landing page. */
  CS.seal = function (size, label) {
    var s = size || 120, id = 'sl' + Math.random().toString(36).slice(2, 7);
    var ticks = '';
    for (var i = 0; i < 48; i++) {
      var a = i * Math.PI / 24, r1 = 47, r2 = i % 2 ? 44.5 : 43;
      ticks += '<line x1="' + (50 + r1 * Math.cos(a)).toFixed(2) + '" y1="' + (50 + r1 * Math.sin(a)).toFixed(2) + '" x2="' + (50 + r2 * Math.cos(a)).toFixed(2) + '" y2="' + (50 + r2 * Math.sin(a)).toFixed(2) + '"/>';
    }
    return '<svg class="cs-seal" width="' + s + '" height="' + s + '" viewBox="0 0 100 100" role="img" aria-label="Seal of the C-Suite Coach Institute">' +
      '<defs><path id="' + id + '" d="M50 50m-34 0a34 34 0 1 1 68 0a34 34 0 1 1-68 0"/>' +
      '<radialGradient id="' + id + 'g" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="#e9d3a6"/><stop offset=".55" stop-color="#c9a66b"/><stop offset="1" stop-color="#9c7a43"/></radialGradient></defs>' +
      '<circle cx="50" cy="50" r="49" fill="url(#' + id + 'g)"/>' +
      '<g stroke="#7d5f30" stroke-width=".8" opacity=".7">' + ticks + '</g>' +
      '<circle cx="50" cy="50" r="41" fill="none" stroke="#7d5f30" stroke-width=".8"/>' +
      '<circle cx="50" cy="50" r="27" fill="none" stroke="#7d5f30" stroke-width=".8"/>' +
      '<text font-family="Cormorant Garamond, Georgia, serif" font-weight="700" font-size="7.4" letter-spacing="1.6" fill="#4d3815"><textPath href="#' + id + '" startOffset="0">' +
      esc(label || 'C-SUITE COACH INSTITUTE · BOARD OF EXAMINERS ·') + '</textPath></text>' +
      '<g fill="#4d3815"><path d="M50 32 64 40H36z"/><rect x="39" y="42" width="3.6" height="12" rx=".5"/><rect x="48.2" y="42" width="3.6" height="12" rx=".5"/><rect x="57.4" y="42" width="3.6" height="12" rx=".5"/>' +
      '<rect x="36" y="56" width="28" height="3" rx=".5"/></g>' +
      '<text x="50" y="68" text-anchor="middle" font-family="Cormorant Garamond, Georgia, serif" font-weight="700" font-size="6" letter-spacing="1" fill="#4d3815">MMXXVI</text></svg>';
  };

  CS.ring = function (pct, size, label) {
    var s = size || 64, r = s / 2 - 5, c = 2 * Math.PI * r, p = Math.max(0, Math.min(100, pct || 0));
    return '<span class="cs-ring" style="width:' + s + 'px;height:' + s + 'px" role="img" aria-label="' + p + '% complete"><svg width="' + s + '" height="' + s + '" aria-hidden="true">' +
      '<circle cx="' + s / 2 + '" cy="' + s / 2 + '" r="' + r + '" fill="none" stroke="var(--c-surface-2)" stroke-width="5"/>' +
      '<circle cx="' + s / 2 + '" cy="' + s / 2 + '" r="' + r + '" fill="none" stroke="var(--c-accent)" stroke-width="5" stroke-linecap="round" stroke-dasharray="' + (c * p / 100).toFixed(1) + ' ' + c.toFixed(1) + '"/></svg>' +
      '<b aria-hidden="true">' + esc(label != null && label !== '' ? label : p + '%') + '</b></span>';
  };

  CS.confetti = function () {
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var box = document.createElement('div'); box.className = 'cs-confetti'; box.setAttribute('aria-hidden', 'true');
    var cols = ['#c9a66b', '#e9d3a6', '#14213d', '#b08d57', '#ffffff'];
    for (var i = 0; i < 70; i++) {
      var p = document.createElement('i');
      p.style.left = Math.random() * 100 + 'vw';
      p.style.background = cols[i % cols.length];
      p.style.animationDuration = (1.8 + Math.random() * 1.8) + 's';
      p.style.animationDelay = (Math.random() * .4) + 's';
      p.style.transform = 'rotate(' + Math.random() * 180 + 'deg)';
      box.appendChild(p);
    }
    document.body.appendChild(box);
    setTimeout(function () { box.remove(); }, 4200);
  };

  /* ---------------------------------------------------------------- the certificate */
  function signature(seed, ink) {
    ink = ink || '#1b2a4a';
    var pts = [], x = 10;
    for (var i = 0; i < 9; i++) { x += 14 + ((seed * (i + 3)) % 9); pts.push(x + ',' + (22 + ((seed * (i + 7)) % 15) - 7)); }
    return '<svg width="200" height="44" viewBox="0 0 200 44" aria-hidden="true"><path d="M8 30 C 30 2, 40 44, 60 20 S 90 6, 104 26 S 140 40, 150 16 S 180 18, 192 24" fill="none" stroke="' + ink + '" stroke-width="1.6" stroke-linecap="round"/>' +
      '<path d="M' + pts.join(' L') + '" fill="none" stroke="' + ink + '" stroke-width="1.1" opacity=".55" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  }
  function guilloche(gold) {
    var d = '';
    for (var k = 0; k < 6; k++) {
      var pts = [];
      for (var t = 0; t <= 360; t += 4) {
        var a = t * Math.PI / 180, r = 60 + 8 * Math.sin(7 * a + k);
        pts.push((70 + r * Math.cos(a)).toFixed(1) + ',' + (70 + r * Math.sin(a)).toFixed(1));
      }
      d += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="' + gold + '" stroke-width=".5"/>';
    }
    return d;
  }
  CS.cert = function (c) {
    var fellow = c.track === 'fellow', gold = fellow ? '#c9a66b' : '#b08d57';
    var g = guilloche(gold);
    var corner = function (x, y, rot) { return '<g transform="translate(' + x + ' ' + y + ') rotate(' + rot + ' 70 70)">' + g + '</g>'; };
    var issued = c.issued ? new Date(c.issued).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
    var seed = (c.code || 'x').split('').reduce(function (s, ch) { return s + ch.charCodeAt(0); }, 0);
    var mods = c.modules || [];
    return '<div class="cs-cert' + (fellow ? ' fellow' : '') + '" data-cert>' +
      '<svg class="guil" viewBox="0 0 940 647" preserveAspectRatio="none" aria-hidden="true">' + corner(-40, -40, 0) + corner(840, -40, 90) + corner(-40, 547, 270) + corner(840, 547, 180) + '</svg>' +
      '<div class="frame"></div><div class="frame2"></div>' +
      (c.demo ? '<div class="sample">SAMPLE RECORD</div>' : '') +
      '<div class="inner">' +
      '<svg class="crest" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="13" fill="' + (fellow ? '#c9a66b' : '#14213d') + '"/><path d="M32 11 52 22.5H12z" fill="' + (fellow ? '#14213d' : '#c9a66b') + '"/>' +
      [15.5, 28.5, 41.5].map(function (x) { return '<rect x="' + x + '" y="26" width="7" height="19" rx="1" fill="' + (fellow ? '#14213d' : '#c9a66b') + '"/>'; }).join('') +
      '<rect x="11" y="47.5" width="42" height="5.5" rx="1" fill="' + (fellow ? '#14213d' : '#c9a66b') + '"/></svg>' +
      '<div class="inst">C-SUITE COACH INSTITUTE</div><div class="sub">BOARD OF EXAMINERS · EXECUTIVE CERTIFICATION</div>' +
      '<div class="certify">This is to certify that</div>' +
      '<div class="holder">' + esc(c.holder) + '</div>' +
      '<div class="has">' + (fellow ? 'having earned the Institute’s foundation and two role certificates, is admitted as a' : 'has satisfied the Board of Examiners in the program of study and examination for the') + '</div>' +
      '<div class="cred">' + esc(c.credential) + '</div>' +
      (mods.length ? '<div class="mods">' + mods.map(esc).join(' · ') + '</div>' : '') +
      '<div class="bottom"><div class="sig">' + signature(seed, fellow ? '#c9a66b' : null) + '<div class="line">Registrar</div></div>' +
      '<div class="seal">' + CS.seal(132) + '</div>' +
      '<div class="sig">' + signature(seed + 11, fellow ? '#c9a66b' : null) + '<div class="line">Chair, Board of Examiners</div></div></div>' +
      '<div class="facts"><span>Credential ID: ' + esc(c.code) + '</span><span>Issued ' + esc(issued) + '</span><span>Verify at the Institute’s register</span></div>' +
      '</div>' + (c.status === 'revoked' ? '<div class="stamp">REVOKED</div>' : '') + '</div>';
  };
  /* Scale a .cs-cert-wrap's certificate (designed at 1000x707) to the wrapper's width. Returns a cleanup function. */
  CS.fitCert = function (wrap) {
    function fit() {
      var cert = wrap.querySelector('[data-cert]');
      if (!cert) return;
      var w = wrap.clientWidth || 1000, s = Math.min(1, w / 1000);
      cert.style.transform = 'scale(' + s + ')';
      wrap.style.height = Math.ceil(707 * s) + 'px';
    }
    fit();
    var ro = window.ResizeObserver ? new ResizeObserver(fit) : null;
    if (ro) ro.observe(wrap);
    window.addEventListener('resize', fit);
    setTimeout(fit, 60);
    return function () { window.removeEventListener('resize', fit); if (ro) ro.disconnect(); };
  };
})();
