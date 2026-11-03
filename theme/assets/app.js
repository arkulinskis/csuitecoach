/* core.js: the shared front-end engine (window.UI). Same in every app made from APP_MAKER/template;
   app-specific things live in web/app.js (brand, nav, footer) and web/pages/*.html (the pages).

   Pages:   UI.page(name, {title, nav, icon, auth, order, chrome}, mount)
              auth: null (anyone) | 'guest' (signed-out only) | 'user' | 'admin'
              nav: label for the header / phone tab bar (omit to keep it out of the menus)
              mount(view, ctx) draws into `view`; ctx = {args, me, go, api}. Return a Promise (the page
              is "ready" when it resolves) or {ready, destroy}. URLs are #name/arg1/arg2.
   Server:  UI.api(fn, ...args) -> Promise of the server function's return value. A reply of
              {ok: false, error} rejects with that message (shown as a toast unless you .catch it).
            UI.apiQuiet(fn, ...args) is the same without Anvil's loading spinner.
   Auth:    UI.auth('login'|'signup'|'reset'|'logout', {...}) -> Promise of {ok, me, message}
   Helpers: UI.esc, UI.icon, UI.toast, UI.modal, UI.confirm, UI.busy, UI.formData, UI.fmtDate, UI.ago,
            UI.store, UI.setTheme, UI.feedback, UI.go, UI.refresh
   Tests:   window.UI_READY is true when the current page has finished loading. */
(function () {
  'use strict';
  if (window.UI && window.UI.__v) return;
  var UI = window.UI = { __v: 1, pages: {}, me: null, config: { name: 'App', key: 'app', home: 'home', landing: 'landing' } };
  window.UI_READY = false;

  // The saved theme lives under the app's key ('<key>.theme'), which is only known once the app configures UI:
  // apply it again then, or a saved Light/Dark choice is ignored after every reload.
  UI.configure = function (cfg) { Object.keys(cfg).forEach(function (k) { UI.config[k] = cfg[k]; }); if (cfg.key && UI.applyTheme) UI.applyTheme(UI.theme()); };

  /* ------------------------------------------------------------------ small helpers */
  UI.esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  UI.plural = function (n, one, many) { return n + ' ' + (n === 1 ? one : (many || one + 's')); };
  UI.initials = function (name) {
    var p = String(name || '?').trim().split(/\s+/);
    return ((p[0] || '?')[0] + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase();
  };
  UI.fmtDate = function (iso, opts) {
    if (!iso) return '';
    var d = iso.length <= 10 ? new Date(iso + 'T12:00:00') : new Date(iso);
    return d.toLocaleDateString(undefined, opts || { day: 'numeric', month: 'short', year: 'numeric' });
  };
  UI.fmtDateTime = function (iso) {
    return iso ? new Date(iso).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  };
  UI.ago = function (iso) {
    if (!iso) return '';
    var s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (s < 60) return 'just now';
    var steps = [[60, 'minute'], [24, 'hour'], [7, 'day'], [4.35, 'week'], [12, 'month'], [Infinity, 'year']], n = s / 60;
    for (var i = 0; i < steps.length; i++) {
      if (n < steps[i][0]) { n = Math.floor(n); return UI.plural(n, steps[i][1]) + ' ago'; }
      n = n / steps[i][0];
    }
    return '';
  };
  UI.store = {
    get: function (k, dflt) { try { var v = localStorage.getItem(UI.config.key + '.' + k); return v == null ? dflt : JSON.parse(v); } catch (e) { return dflt; } },
    set: function (k, v) { try { localStorage.setItem(UI.config.key + '.' + k, JSON.stringify(v)); } catch (e) {} }
  };
  UI.formData = function (form) {
    var out = {};
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || el.disabled) return;
      if (el.type === 'checkbox') out[el.name] = el.checked;
      else if (el.type === 'radio') { if (el.checked) out[el.name] = el.value; }
      else out[el.name] = el.value;
    });
    return out;
  };
  /* Disable a button while a Promise runs; returns the Promise. */
  UI.busy = function (btn, promise) {
    if (!btn) return promise;
    btn.disabled = true; btn.classList.add('is-busy');
    var done = function () { btn.disabled = false; btn.classList.remove('is-busy'); };
    promise.then(done, done);
    return promise;
  };

  var ICONS = {
    home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.5 3-5.5 6.5-5.5s6.5 2 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14.7c2.2.6 3.5 2.4 3.5 5.3"/>',
    sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12z"/>',
    bell: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    back: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    bug: '<rect x="7" y="8" width="10" height="12" rx="5"/><path d="M12 8V5M9 5.5 7.5 4M15 5.5 16.5 4M7 13H3M21 13h-4M7.5 18l-3 2M16.5 18l3 2M7.5 9.5l-3-2M16.5 9.5l3-2"/>',
    bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    inbox: '<path d="M3 13h5l1.5 3h5L16 13h5"/><path d="M5 5h14l2 8v6H3v-6z"/>',
    grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
    sparkle: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/>',
    database: '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.5"/><path d="M4.5 5.5v13c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5v-13"/><path d="M4.5 12c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14.3-4.9L4 8"/><path d="M4 4v4h4"/><path d="M4 13a8 8 0 0 0 14.3 4.9L20 16"/><path d="M20 20v-4h-4"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    map: '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    pin: '<path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    camera: '<path d="M4 8h3l2-3h6l2 3h3v12H4z"/><circle cx="12" cy="13.5" r="3.5"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    filter: '<path d="M4 5h16l-6 7.5V19l-4 1.5v-8z"/>',
    more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>'
  };
  UI.ICONS = ICONS;
  UI.icon = function (name, cls) {
    return '<svg class="ui-ic ' + (cls || '') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || ICONS.sparkle) + '</svg>';
  };

  /* ------------------------------------------------------------------ toasts, modals */
  UI.toast = function (msg, kind) {
    var box = document.querySelector('.ui-toasts');
    if (!box) { box = document.createElement('div'); box.className = 'ui ui-toasts'; box.setAttribute('aria-live', 'polite'); document.body.appendChild(box); }
    var t = document.createElement('div');
    t.className = 'ui-toast' + (kind ? ' ' + kind : '');
    t.innerHTML = (kind === 'error' ? UI.icon('info') : kind === 'ok' ? UI.icon('check') : '') + '<span>' + UI.esc(msg) + '</span>';
    box.appendChild(t);
    setTimeout(function () { t.classList.add('out'); setTimeout(function () { t.remove(); }, 300); }, kind === 'error' ? 6500 : 3200);
  };
  UI.modal = function (html, opts) {
    opts = opts || {};
    var prev = document.activeElement;
    var wrap = document.createElement('div');
    wrap.className = 'ui ui-modal-wrap';
    wrap.innerHTML = '<div class="ui-modal' + (opts.wide ? ' wide' : '') + '" role="dialog" aria-modal="true">' +
      '<button class="ui-btn ghost icon ui-modal-x" data-close aria-label="Close">' + UI.icon('x') + '</button>' + html + '</div>';
    document.body.appendChild(wrap);
    document.documentElement.classList.add('ui-modal-open');
    function key(e) { if (e.key === 'Escape') close(); }
    function close() {
      if (!wrap.parentNode) return;
      wrap.remove(); document.removeEventListener('keydown', key);
      if (!document.querySelector('.ui-modal-wrap')) document.documentElement.classList.remove('ui-modal-open');
      if (opts.onclose) opts.onclose();
      if (prev && prev.focus) prev.focus();
    }
    document.addEventListener('keydown', key);
    wrap.addEventListener('mousedown', function (e) { if (e.target === wrap) close(); });
    wrap.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) close(); });
    var first = wrap.querySelector('input, textarea, select');
    setTimeout(function () { (first || wrap.querySelector('.ui-modal')).focus && (first || wrap.querySelector('.ui-modal')).focus(); }, 30);
    return { el: wrap.querySelector('.ui-modal'), close: close };
  };
  UI.confirm = function (o) {
    o = typeof o === 'string' ? { title: o } : (o || {});
    return new Promise(function (resolve) {
      var answered = false;
      var m = UI.modal('<h2>' + UI.esc(o.title || 'Are you sure?') + '</h2>' + (o.text ? '<p class="muted">' + UI.esc(o.text) + '</p>' : '') +
        '<div class="ui-row end" style="margin-top:20px"><button class="ui-btn ghost" data-close>' + UI.esc(o.cancel || 'Cancel') + '</button>' +
        '<button class="ui-btn ' + (o.danger ? 'danger solid' : 'primary') + '" data-ok>' + UI.esc(o.ok || 'OK') + '</button></div>',
      { onclose: function () { if (!answered) resolve(false); } });
      m.el.querySelector('[data-ok]').onclick = function () { answered = true; m.close(); resolve(true); };
    });
  };

  /* ------------------------------------------------------------------ theme */
  UI.theme = function () { return UI.store.get('theme', 'auto'); };
  UI.applyTheme = function (t) {
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
    else document.documentElement.removeAttribute('data-theme');
    var dark = t === 'dark' || (t !== 'light' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('ui-dark', !!dark);
  };
  UI.setTheme = function (t) { UI.store.set('theme', t); UI.applyTheme(t); };
  UI.applyTheme(UI.theme());
  if (window.matchMedia) {
    try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () { UI.applyTheme(UI.theme()); }); } catch (e) {}
  }

  /* ------------------------------------------------------------------ server bridge */
  var bridge = null;
  function send(kind, payload) {
    if (!bridge) return Promise.reject(new Error('The app is still starting.'));
    var out;
    try { out = bridge(kind, JSON.stringify(payload || {})); } catch (e) { return Promise.reject(e); }
    return Promise.resolve(out).then(function (r) {
      r = typeof r === 'string' ? JSON.parse(r) : (r || {});
      if (r.error) {
        var err = new Error(r.error); err.uiApi = true; err.denied = !!r.denied;
        if (r.detail) console.error(kind, payload && payload.fn, r.detail);
        if (r.reload) setTimeout(function () { location.reload(); }, 2500);
        throw err;
      }
      return r.result;
    });
  }
  function apiCall(quiet, fn, args) {
    return send('call', { fn: fn, args: args, quiet: quiet }).then(function (res) {
      if (res && typeof res === 'object' && res.ok === false) {
        var err = new Error(res.error || 'That didn\'t work.'); err.uiApi = true; err.expected = true; err.result = res;
        throw err;
      }
      return res;
    });
  }
  UI.api = function (fn) { return apiCall(false, fn, Array.prototype.slice.call(arguments, 1)); };
  UI.apiQuiet = function (fn) { return apiCall(true, fn, Array.prototype.slice.call(arguments, 1)); };
  /* Errors nobody caught become a toast, so a failed action is never silent. */
  window.addEventListener('unhandledrejection', function (e) {
    if (e.reason && e.reason.uiApi) { e.preventDefault(); UI.toast(e.reason.message, 'error'); }
  });

  /* Sign in / up / out. On success it navigates: to where the visitor was heading (UI.after) or home
     after signing in, to the landing page after signing out. */
  UI.auth = function (kind, payload) {
    return send(kind, payload || {}).then(function (r) {
      if (r && r.ok === false) { var err = new Error(r.error); err.uiApi = true; err.expected = true; throw err; }
      if (r && 'me' in r && (r.me || kind === 'logout')) {
        UI.me = r.me || null;
        var target = r.me ? (UI.after || '#' + UI.config.home) : '#' + UI.config.landing;
        UI.after = null;
        if (location.hash === target) route(); else location.hash = target;
      }
      return r;
    });
  };
  /* Update the signed-in user's details (e.g. a new name) and redraw the header, without reloading the page. */
  UI.setMe = function (me) {
    UI.me = me || null;
    if (shellRoot) renderChrome(current.name);
  };

  /* ------------------------------------------------------------------ pages and routing */
  UI.page = function (name, opts, mount) {
    if (typeof opts === 'function') { mount = opts; opts = {}; }
    opts.name = name; opts.mount = mount;
    UI.pages[name] = opts;
  };
  UI.allowed = function (p) {
    if (!p) return false;
    if (p.auth === 'user') return !!UI.me;
    if (p.auth === 'admin') return !!(UI.me && UI.me.is_admin);
    if (p.auth === 'guest') return !UI.me;
    return true;
  };
  UI.navPages = function () {
    return Object.keys(UI.pages).map(function (k) { return UI.pages[k]; })
      .filter(function (p) { return p.nav && UI.allowed(p) && (!p.when || p.when()); })
      .sort(function (a, b) { return (a.order || 50) - (b.order || 50); });
  };
  UI.parseHash = function () {
    var h = (location.hash || '').replace(/^#!?\/?/, '');
    var parts = h.split('?')[0].split('/').filter(function (x) { return x !== ''; }).map(decodeURIComponent);
    return { name: parts[0] || '', args: parts.slice(1) };
  };
  UI.hashFor = function (name) {
    var args = Array.prototype.slice.call(arguments, 1).filter(function (a) { return a != null && a !== ''; });
    return '#' + [name].concat(args.map(encodeURIComponent)).join('/');
  };
  UI.go = function (name) {
    var h = UI.hashFor.apply(null, arguments);
    if (location.hash === h) route(); else location.hash = h;
  };
  UI.refresh = function () { route(); };
  UI.after = null;  // where to go after signing in

  var shellRoot = null, view = null, current = { name: null, destroy: null }, routeSeq = 0;

  function defaultPage() { return UI.me ? UI.config.home : UI.config.landing; }

  function route() {
    var r = UI.parseHash(), name = r.name || defaultPage(), p = UI.pages[name];
    if (!p) { name = defaultPage(); p = UI.pages[name]; r.args = []; }
    if (p.auth === 'guest' && UI.me) { p = UI.pages[UI.config.home]; name = UI.config.home; r.args = []; }
    if ((p.auth === 'user' || p.auth === 'admin') && !UI.me) {
      UI.after = location.hash && location.hash !== '#' ? location.hash : null;
      p = UI.pages.auth; name = 'auth'; r.args = [];
    }
    if (p.auth === 'admin' && !(UI.me && UI.me.is_admin)) {
      UI.toast('That page is for admins only.', 'error');
      p = UI.pages[UI.config.home]; name = UI.config.home; r.args = [];
    }
    var seq = ++routeSeq;
    window.UI_READY = false;
    if (current.destroy) { try { current.destroy(); } catch (e) { console.error(e); } }
    current = { name: name, args: r.args, destroy: null };
    if (shellRoot) {
      shellRoot.className = 'ui ui-shell page-' + name + (UI.me ? ' signed-in' : ' signed-out') + (p.chrome === false ? ' no-chrome' : '');
      renderChrome(name);
    }
    // A fresh element for every page, so listeners a page adds to `view` never pile up.
    var fresh = view.cloneNode(false);
    view.parentNode.replaceChild(fresh, view);
    view = fresh;
    window.scrollTo(0, 0);
    document.title = (p.title ? (typeof p.title === 'function' ? p.title(r.args) : p.title) + ' · ' : '') + UI.config.name;
    var ctx = { name: name, args: r.args, me: UI.me, go: UI.go, api: UI.api, page: p };
    var out;
    try { out = p.mount(view, ctx); } catch (e) { console.error(e); out = Promise.reject(e); }
    var ready = out && typeof out.then === 'function' ? out : (out && out.ready) || Promise.resolve();
    if (out && out.destroy) current.destroy = out.destroy;
    Promise.resolve(ready).then(function () { if (seq === routeSeq) window.UI_READY = true; },
      function (e) {
        if (seq !== routeSeq) return;
        console.error(e);
        if (!view.innerHTML) view.innerHTML = '<div class="ui-wrap"><div class="ui-empty">' + UI.icon('info') +
          '<h3>This page didn\'t load</h3><p class="muted">' + UI.esc(e && e.message || 'Something went wrong.') + '</p>' +
          '<button class="ui-btn" onclick="UI.refresh()">Try again</button></div></div>';
        window.UI_READY = true;
      });
  }
  UI.current = function () { return current; };

  /* The shell's parts come from web/app.js: UI.shell = {header(me, active), footer(me), tabbar(me, active)} */
  function renderChrome(active) {
    var S = UI.shell || {};
    var hd = shellRoot.querySelector('[data-ui-header]'), ft = shellRoot.querySelector('[data-ui-footer]'), tb = shellRoot.querySelector('[data-ui-tabbar]');
    if (hd) hd.innerHTML = S.header ? S.header(UI.me, active) : '';
    if (ft) ft.innerHTML = S.footer ? S.footer(UI.me, active) : '';
    if (tb) tb.innerHTML = S.tabbar ? S.tabbar(UI.me, active) : '';
  }
  UI.renderChrome = function () { if (shellRoot) renderChrome(current.name); };

  /* Called by client_code/Main.py (and by the local harness) once the page is up. */
  UI.start = function (node, bridgeFn, bootJson) {
    bridge = bridgeFn;
    var boot = typeof bootJson === 'string' ? JSON.parse(bootJson || '{}') : (bootJson || {});
    UI.me = boot.me || null;
    var host = node && node.matches && node.matches('[data-ui-app]') ? node : (node && node.querySelector('[data-ui-app]')) || node || document.body;
    host.innerHTML = '<div class="ui ui-shell">' +
      '<header class="ui-header" data-ui-header></header>' +
      '<main class="ui-main" data-ui-view></main>' +
      '<footer class="ui-footer" data-ui-footer></footer>' +
      '<nav class="ui-tabbar" data-ui-tabbar aria-label="Main"></nav></div>';
    shellRoot = host.firstChild;
    view = host.querySelector('[data-ui-view]');
    if (UI.shell && UI.shell.wire) UI.shell.wire(shellRoot);
    window.addEventListener('hashchange', route);
    route();
  };

  /* ------------------------------------------------------------------ feedback (footer + menu)
     All feedback goes to Prepsto. The widget tag in head.html (data-prepsto="CODE") slides its panel in;
     any [data-feedback] or [data-prepsto-open] element opens it. If the widget hasn't loaded, the panel opens in a new tab.
     There is no in-app feedback form any more: Admin -> Feedback only lists older messages (and app requests). */
  UI.feedback = function () {
    if (window.Prepsto && window.Prepsto.open) { window.Prepsto.open(); return; }
    var tag = document.querySelector('script[data-prepsto]');
    var code = tag && tag.getAttribute('data-prepsto');
    if (code && code.indexOf('__') !== 0) window.open('https://prepsto.com/#f/' + encodeURIComponent(code), '_blank', 'noopener');
    else UI.toast('Feedback is not set up yet.', 'error');
  };

  /* Shared clicks: [data-go="page/arg"], [data-feedback], [data-theme-set] anywhere in the app. */
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-go],[data-feedback],[data-theme-set]');
    if (!el) return;
    if (el.hasAttribute('data-go')) { e.preventDefault(); UI.go.apply(null, el.getAttribute('data-go').split('/')); }
    else if (el.hasAttribute('data-feedback')) { e.preventDefault(); UI.feedback(el.getAttribute('data-feedback') || null); }
    else if (el.hasAttribute('data-theme-set')) { e.preventDefault(); UI.setTheme(el.getAttribute('data-theme-set')); if (UI.shell && UI.shell.onTheme) UI.shell.onTheme(); }
  });
})();


/* app.js: this app's identity and frame: name, header, footer, phone tab bar, shared visuals (seal, photos).
   Pages live in web/pages/*.html. The engine (window.UI) is web/core.js. */
(function () {
  'use strict';
  UI.configure({
    name: 'C-Suite Coach',
    institute: 'C-Suite Coach Institute',
    key: 'csuitecoach',          // prefix for this app's browser storage
    tagline: 'Executive education and certification. Real cases, deliberate practice, earned credentials.',
    home: 'home',                // first page after signing in
    landing: 'landing'           // first page for visitors who aren't signed in
  });

  // Extra icons for this app (same 24px stroke style as core.js).
  var X = UI.ICONS;
  X.award = '<circle cx="12" cy="9" r="6"/><path d="M8.5 13.8 7 22l5-3 5 3-1.5-8.2"/>';
  X.book = '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5"/>';
  X.briefcase = '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>';
  X.cards = '<rect x="3" y="6" width="14" height="15" rx="2"/><path d="M7 3h12a2 2 0 0 1 2 2v13"/>';
  X.target = '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>';
  X.columns = '<path d="M12 3 21 8H3z"/><path d="M5 10v8M10 10v8M14 10v8M19 10v8M3 21h18"/>';
  X.scale = '<path d="M12 3v18M5 21h14M4 7h16"/><path d="M4 7l-2.5 6a3 3 0 0 0 5 0zM20 7l-2.5 6a3 3 0 0 0 5 0z"/>';
  X.flame = '<path d="M12 22a7 7 0 0 0 7-7c0-4-3-6-4-10-2 2-3 4-3 6-1-1-2-2-2-4-3 3-5 5.5-5 8a7 7 0 0 0 7 7z"/>';
  X.quote = '<path d="M7 7h4v5H6.5A3.5 3.5 0 0 0 10 17M15 7h4v5h-4.5A3.5 3.5 0 0 0 18 17"/>';
  X.pen = '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>';
  X.print = '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/>';
  X.link = '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>';
  X.alert = '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17h.01"/>';

  var esc = UI.esc;

  /* The institute's seal (SVG, gold), used in the footer, on certificates and on the landing page. */
  UI.seal = function (size, label) {
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
  UI.photo = function (name) { return '_/theme/' + name + '.jpg'; };

  function brand() {
    return '<a class="ui-brand" href="#" data-go="' + (UI.me ? UI.config.home : UI.config.landing) + '" aria-label="' + esc(UI.config.name) + ' home">' +
      '<img src="_/theme/icon.svg" alt="" width="34" height="34"><span class="bt"><b>' + esc(UI.config.name) + '</b><small>Institute · Est. 2026</small></span></a>';
  }

  function themeSwitch() {
    var t = UI.theme();
    return '<div class="ui-seg" role="group" aria-label="Appearance">' + [['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']].map(function (o) {
      return '<button type="button" data-theme-set="' + o[0] + '" class="' + (t === o[0] ? 'on' : '') + '">' + o[1] + '</button>';
    }).join('') + '</div>';
  }

  function userMenu(me) {
    return '<div class="ui-menu" data-menu hidden>' +
      '<div class="ui-menu-head"><strong>' + esc(me.name) + '</strong><span class="muted small">' + esc(me.email) + '</span>' +
      (me.rank ? '<span class="small" style="color:var(--c-accent-ink)">' + esc(me.rank) + ' · ' + (me.xp || 0) + ' XP</span>' : '') + '</div>' +
      '<a href="#profile" data-go="profile">' + UI.icon('user') + 'Your profile</a>' +
      '<a href="#credentials" data-go="credentials">' + UI.icon('award') + 'Your credentials</a>' +
      '<a href="#cases" data-go="cases">' + UI.icon('book') + 'The Casebook</a>' +
      '<a href="#verify" data-go="verify">' + UI.icon('shield') + 'Verify a credential</a>' +
      (me.is_admin ? '<a href="#admin" data-go="admin">' + UI.icon('sliders') + 'Admin</a>' : '') +
      '<div class="ui-menu-block"><span class="small muted">Appearance</span>' + themeSwitch() + '</div>' +
      '<button type="button" data-feedback>' + UI.icon('chat') + 'Submit feedback</button>' +
      '<button type="button" data-lk-open="overview">' + UI.icon('lock') + 'Privacy &amp; Terms</button>' +
      '<button type="button" data-signout>' + UI.icon('logout') + 'Sign out</button></div>';
  }

  var GUEST_NAV = [{ name: 'tracks', nav: 'Programs', icon: 'columns' }, { name: 'cases', nav: 'Casebook', icon: 'book' }, { name: 'verify', nav: 'Verify', icon: 'shield' }];

  UI.shell = {
    header: function (me, active) {
      var nav = me ? UI.navPages() : GUEST_NAV;
      return '<div class="ui-header-in">' + brand() +
        '<nav class="ui-nav" aria-label="Main">' + nav.map(function (p) {
          return '<a href="#' + p.name + '" class="' + (p.name === active ? 'on' : '') + '">' + UI.icon(p.icon) + '<span>' + esc(p.nav) + '</span></a>';
        }).join('') + '</nav>' +
        '<div class="ui-header-right">' +
        (me ? '<button type="button" class="ui-avatar-btn" data-menu-toggle aria-label="Your account" aria-haspopup="true">' + esc(UI.initials(me.name)) + '</button>' + userMenu(me)
          : (active === 'auth' ? '' : '<a class="ui-btn ghost" href="#auth" data-go="auth">Sign in</a><a class="ui-btn primary" href="#auth/signup" data-go="auth/signup">Enrol</a>')) +
        '</div></div>';
    },
    footer: function (me) {
      var col = function (title, links) {
        return '<div class="ft-col"><h4>' + title + '</h4>' + links.map(function (l) {
          if (l[0] === 'ext') return '<a href="' + l[2] + '" target="_blank" rel="noopener" data-prepsto-open>' + l[1] + '</a>';  // Prepsto feedback panel
          return l[0] === 'btn' ? '<button type="button" ' + l[2] + '>' + l[1] + '</button>' : '<a href="#' + l[0] + '" data-go="' + l[0] + '">' + l[1] + '</a>';
        }).join('') + '</div>';
      };
      return '<div class="ui-footer-in ft">' +
        '<div class="ft-brand">' + brand() + '<p class="muted small">' + esc(UI.config.tagline) + '</p></div>' +
        col('Programs', [['tracks', 'All programs'], ['tracks/core', 'Executive Foundations'], ['cases', 'The Casebook']]) +
        col('Credentials', [['verify', 'Verify a credential'], [me ? 'credentials' : 'landing', me ? 'Your credentials' : 'How certification works']]) +
        col('Institute', [['landing', 'About'], ['ext', 'Submit feedback', 'https://prepsto.com/#f/fha858r'], ['btn', 'Privacy &amp; Terms', 'data-lk-open="overview"']]) +
        '<div class="ft-seal" aria-hidden="true">' + UI.seal(76) + '</div>' +
        '<p class="ui-footer-legal small muted">© ' + new Date().getFullYear() + ' ' + esc(UI.config.institute) + '. A private executive-education program: its credentials are ' +
        'issued on its own authority and are not accredited academic qualifications. Case studies are drawn from public reporting. Photography: Pexels.</p></div>';
    },
    tabbar: function (me, active) {
      var nav = UI.navPages();
      if (!me || nav.length < 2) return '';
      return nav.slice(0, 4).map(function (p) {
        return '<a href="#' + p.name + '" class="' + (p.name === active ? 'on' : '') + '">' + UI.icon(p.icon) + '<span>' + esc(p.nav) + '</span></a>';
      }).join('') + '<a href="#profile" class="' + (active === 'profile' ? 'on' : '') + '">' + UI.icon('user') + '<span>You</span></a>';
    },
    wire: function (root) {
      root.addEventListener('click', function (e) {
        var t = e.target.closest('[data-menu-toggle]');
        var menu = root.querySelector('[data-menu]');
        if (t && menu) { menu.hidden = !menu.hidden; t.setAttribute('aria-expanded', String(!menu.hidden)); return; }
        if (e.target.closest('[data-signout]')) { UI.auth('logout').then(function () { UI.toast('Signed out. See you soon.'); }); }
        if (menu && !menu.hidden && !e.target.closest('[data-menu] .ui-seg')) menu.hidden = true;
      });
      document.addEventListener('keydown', function (e) {
        var menu = root.querySelector('[data-menu]');
        if (e.key === 'Escape' && menu) menu.hidden = true;
      });
    },
    onTheme: function () {  // redraw the menu's Auto/Light/Dark buttons and keep the menu open
      var menu = document.querySelector('[data-menu]'), open = menu && !menu.hidden;
      UI.renderChrome();
      if (open) document.querySelector('[data-menu]').hidden = false;
    }
  };
})();


/* ===== _shared.html ===== */
(function () {
  var esc = UI.esc;
  var CS = window.CS = {};

  CS.today = function () {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  };
  CS.bar = function (pct, cls) { return '<div class="cs-bar ' + (cls || '') + '"><i style="width:' + Math.max(0, Math.min(100, pct || 0)) + '%"></i></div>'; };
  CS.ring = function (pct, size, label) {
    var s = size || 64, r = s / 2 - 5, c = 2 * Math.PI * r, p = Math.max(0, Math.min(100, pct || 0));
    return '<span class="cs-ring" style="width:' + s + 'px;height:' + s + 'px"><svg width="' + s + '" height="' + s + '">' +
      '<circle cx="' + s / 2 + '" cy="' + s / 2 + '" r="' + r + '" fill="none" stroke="var(--c-surface-2)" stroke-width="5"/>' +
      '<circle cx="' + s / 2 + '" cy="' + s / 2 + '" r="' + r + '" fill="none" stroke="var(--c-accent)" stroke-width="5" stroke-linecap="round" stroke-dasharray="' + (c * p / 100).toFixed(1) + ' ' + c.toFixed(1) + '"/></svg>' +
      '<b>' + (label != null ? label : p + '%') + '</b></span>';
  };
  /* Photo band at the top of a page. o = {photo, eyebrow, title, lead, crumbs: [[hash, label]], meta: [[icon, text]], actions: html} */
  CS.hero = function (o) {
    return '<section class="cs-hero"><div class="ph" style="background-image:url(' + UI.photo(o.photo || 'ph-boardroom') + ')"></div><div class="in">' +
      (o.crumbs ? '<div class="crumbs">' + o.crumbs.map(function (c, i) {
        return (i ? '<span>›</span>' : '') + (c[0] ? '<a href="#' + c[0] + '">' + esc(c[1]) + '</a>' : '<span>' + esc(c[1]) + '</span>');
      }).join('') + '</div>' : '') +
      (o.eyebrow ? '<div class="eyebrow">' + esc(o.eyebrow) + '</div>' : '') + '<div class="gold-rule"></div>' +
      '<h1>' + esc(o.title) + '</h1>' + (o.lead ? '<p class="lead">' + esc(o.lead) + '</p>' : '') +
      (o.meta ? '<div class="meta">' + o.meta.map(function (m) { return '<span>' + UI.icon(m[0]) + esc(m[1]) + '</span>'; }).join('') + '</div>' : '') +
      (o.actions ? '<div class="ui-row" style="margin-top:22px">' + o.actions + '</div>' : '') + '</div></section>';
  };
  CS.tone = function (t) {
    return t === 'exemplary' ? '<span class="ui-badge good">Exemplary</span>' : t === 'cautionary' ? '<span class="ui-badge bad">Cautionary</span>' : '<span class="ui-badge warn">Mixed lessons</span>';
  };
  CS.caseCard = function (c) {
    return '<a class="cs-case ' + esc(c.tone) + '" href="#cases/' + esc(c.id) + '"><div class="top">' + CS.tone(c.tone) + '<span>' + esc(c.company) + ' · ' + esc(c.year) + '</span></div>' +
      '<h4>' + esc(c.title) + '</h4><p>' + esc(c.summary) + '</p></a>';
  };
  CS.trackCard = function (t) {
    var s = t.status;
    return '<a class="cs-pcard" href="#tracks/' + esc(t.id) + '"><div class="img" style="background-image:url(' + UI.photo(t.photo) + ')"><span class="code">' + esc(t.code) + '</span>' +
      (s && s.certified ? '<span class="done ui-badge gold">' + UI.icon('award') + 'Certified</span>' : '') + '</div>' +
      '<div class="txt"><span class="role">' + esc(t.role) + '</span><h3>' + esc(t.title) + '</h3><p>' + esc(t.blurb) + '</p>' +
      (s && s.started ? CS.bar(s.pct) : '') +
      '<div class="foot"><span>' + t.modules.length + ' modules · ' + t.items + ' drills · ' + t.challenges + ' challenges</span><span>~' + Math.round(t.minutes / 6) / 10 + ' h</span></div></div></a>';
  };
  CS.rubric = function (items, checked) {
    return '<div class="cs-rubric">' + items.map(function (r, i) {
      var on = checked && checked[i];
      return '<label class="' + (on ? 'on' : '') + '"><input type="checkbox" data-rub="' + i + '"' + (on ? ' checked' : '') + '><span>' + esc(r) + '</span></label>';
    }).join('') + '</div>';
  };
  CS.wireRubric = function (root) {
    root.addEventListener('change', function (e) {
      var b = e.target.closest('[data-rub]');
      if (b) b.closest('label').classList.toggle('on', b.checked);
    });
  };
  CS.readRubric = function (root) {
    return Array.prototype.map.call(root.querySelectorAll('[data-rub]'), function (b) { return b.checked; });
  };

  CS.confetti = function () {
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var box = document.createElement('div'); box.className = 'cs-confetti';
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

  /* ---------------------------------------------------------------- the flashcard engine
     CS.drill(el, items, {rate(item, knew) -> Promise|undefined, done(stats), exam: bool, title})
     Card: question -> Reveal -> answer -> "Still learning" / "Got it".
     Advice call: statement -> "Sound advice, or a trap?" -> Reveal verdict + why -> "I missed it" / "I called it".
     Outside exams, "Still learning" items come back once at the end of the session. */
  CS.drill = function (el, items, opts) {
    opts = opts || {};
    var queue = items.slice(), i = 0, revealed = false, again = {}, stats = { got: 0, missed: 0, ratings: {} }, total = items.length, busy = false;
    function cur() { return queue[i]; }
    function draw() {
      var it = cur();
      if (!it) { el.removeEventListener('keydown', key); document.removeEventListener('keydown', key); if (opts.done) opts.done(stats); return; }
      var answered = Object.keys(stats.ratings).length;
      var adv = it.kind === 'advice';
      el.innerHTML = '<div class="cs-drill"><div class="top">' + CS.bar(100 * answered / total) + '<span class="count">' + Math.min(answered + 1, total) + ' / ' + total + (queue.length > total ? ' · +' + (queue.length - total) + ' again' : '') + '</span></div>' +
        '<article class="cs-card' + (adv ? ' advice' : '') + '" data-card="' + esc(it.id) + '"><div class="kind">' +
        (adv ? '<span class="ui-badge gold">' + UI.icon('scale') + 'Advice call</span>' : '<span class="ui-badge brand">' + UI.icon('cards') + 'Recall</span>') +
        '<span class="ui-badge">' + esc(it.track_code) + ' · ' + esc(it.module_title) + '</span>' +
        (it.box != null && it.box > 0 ? '<span class="ui-badge good">Box ' + it.box + '</span>' : (it.box == null && !opts.exam ? '<span class="ui-badge warn">New</span>' : '')) + '</div>' +
        '<p class="q' + (adv ? ' quote' : '') + '">' + esc(it.q) + '</p>' +
        (adv ? '<p class="prompt">Sound advice for an executive, or a trap? Decide, then reveal.</p>' : '<p class="prompt">Answer from memory, out loud or in your head, then reveal.</p>') +
        (revealed ? '<div class="back">' + (adv ? '<span class="verdict ' + (it.sound ? 'sound' : 'trap') + '">' + UI.icon(it.sound ? 'check' : 'alert') + (it.sound ? 'Sound advice' : 'A trap') + '</span>' : '') +
          '<p class="a">' + esc(it.a) + '</p>' + (it.note ? '<p class="note">' + esc(it.note) + '</p>' : '') + '</div>' : '') +
        '<div class="actions">' + (revealed
          ? '<button class="ui-btn cs-rate-no" data-rate="0">' + UI.icon('refresh') + (adv ? 'I missed it' : 'Still learning') + '</button>' +
            '<button class="ui-btn cs-rate-yes" data-rate="1">' + UI.icon('check') + (adv ? 'I called it' : 'Got it') + '</button>'
          : '<button class="ui-btn primary lg block" data-reveal>' + (adv ? 'Reveal the verdict' : 'Reveal the answer') + '</button>') + '</div>' +
        '<div class="keys">Space to reveal · 1 ' + (adv ? 'missed' : 'still learning') + ' · 2 ' + (adv ? 'called it' : 'got it') + '</div></article></div>';
    }
    function reveal() { if (!revealed) { revealed = true; draw(); var b = el.querySelector('[data-rate="1"]'); if (b) b.focus(); } }
    function rate(knew) {
      if (!revealed || busy) return;
      var it = cur();
      var first = !(it.id in stats.ratings);
      if (first) { stats.ratings[it.id] = knew; if (knew) stats.got++; else stats.missed++; }
      if (!knew && !opts.exam && !again[it.id]) { again[it.id] = 1; queue.push(it); }
      var p = opts.rate ? opts.rate(it, knew) : null;
      busy = true;
      Promise.resolve(p).then(function () { busy = false; i++; revealed = false; draw(); }, function () { busy = false; });
    }
    function key(e) {
      if (!el.isConnected) { document.removeEventListener('keydown', key); return; }
      if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
      if (e.key === ' ' || e.key === 'Enter') { if (!revealed) { e.preventDefault(); reveal(); } }
      else if (e.key === '1') rate(false);
      else if (e.key === '2') rate(true);
    }
    el.addEventListener('click', function (e) {
      if (e.target.closest('[data-reveal]')) reveal();
      var r = e.target.closest('[data-rate]');
      if (r) rate(r.getAttribute('data-rate') === '1');
    });
    document.addEventListener('keydown', key);
    draw();
    return { stats: stats };
  };

  /* ---------------------------------------------------------------- the certificate
     c = {holder, credential, title, code, issued, status, demo, modules, track} */
  function signature(seed, ink) {
    ink = ink || '#1b2a4a';
    var pts = [], x = 10;
    for (var i = 0; i < 9; i++) { x += 14 + ((seed * (i + 3)) % 9); pts.push(x + ',' + (22 + ((seed * (i + 7)) % 15) - 7)); }
    return '<svg width="200" height="44" viewBox="0 0 200 44"><path d="M8 30 C 30 2, 40 44, 60 20 S 90 6, 104 26 S 140 40, 150 16 S 180 18, 192 24" fill="none" stroke="' + ink + '" stroke-width="1.6" stroke-linecap="round"/>' +
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
    return '<div class="cs-cert' + (fellow ? ' fellow' : '') + '" data-cert>' +
      '<svg class="guil" viewBox="0 0 940 647" preserveAspectRatio="none">' + corner(-40, -40, 0) + corner(840, -40, 90) + corner(-40, 547, 270) + corner(840, 547, 180) + '</svg>' +
      '<div class="frame"></div><div class="frame2"></div>' +
      (c.demo ? '<div class="sample">SAMPLE RECORD</div>' : '') +
      '<div class="inner">' +
      '<svg class="crest" viewBox="0 0 64 64"><rect width="64" height="64" rx="13" fill="' + (fellow ? '#c9a66b' : '#14213d') + '"/><path d="M32 11 52 22.5H12z" fill="' + (fellow ? '#14213d' : '#c9a66b') + '"/>' +
      [15.5, 28.5, 41.5].map(function (x) { return '<rect x="' + x + '" y="26" width="7" height="19" rx="1" fill="' + (fellow ? '#14213d' : '#c9a66b') + '"/>'; }).join('') +
      '<rect x="11" y="47.5" width="42" height="5.5" rx="1" fill="' + (fellow ? '#14213d' : '#c9a66b') + '"/></svg>' +
      '<div class="inst">C-SUITE COACH INSTITUTE</div><div class="sub">BOARD OF EXAMINERS · EXECUTIVE CERTIFICATION</div>' +
      '<div class="certify">This is to certify that</div>' +
      '<div class="holder">' + esc(c.holder) + '</div>' +
      '<div class="has">' + (fellow ? 'having earned the Institute\'s foundation and two role certificates, is admitted as a' : 'has satisfied the Board of Examiners in the program of study and examination for the') + '</div>' +
      '<div class="cred">' + esc(c.credential) + '</div>' +
      (c.modules && c.modules.length ? '<div class="mods">' + c.modules.map(esc).join(' · ') + '</div>' : '') +
      '<div class="bottom"><div class="sig">' + signature(seed, fellow ? '#c9a66b' : null) + '<div class="line">Registrar</div></div>' +
      '<div class="seal">' + UI.seal(132) + '</div>' +
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
    window.addEventListener('resize', fit);
    setTimeout(fit, 60);
    return function () { window.removeEventListener('resize', fit); };
  };
  CS.verifyUrl = function (code) { return location.origin + location.pathname + '#verify/' + encodeURIComponent(code); };
})();

/* ===== admin.html ===== */
(function () {
  var esc = UI.esc;
  var TABS = [['overview', 'Overview', 'grid'], ['credentials', 'Credentials', 'award'], ['feedback', 'Feedback', 'inbox'], ['users', 'Users', 'users'], ['demo', 'Demo data', 'database']];

  UI.page('admin', { title: 'Admin', auth: 'admin' }, function (view, ctx) {
    var tab = TABS.some(function (t) { return t[0] === ctx.args[0]; }) ? ctx.args[0] : 'overview';
    var fbFilter = 'new';
    view.innerHTML = '<div class="ui-wrap"><div class="ui-page-head"><div><h1>Admin</h1><p class="muted">Only admins see this page.</p></div></div>' +
      '<nav class="ui-tabs">' + TABS.map(function (t) {
        return '<a href="#admin/' + t[0] + '" class="' + (t[0] === tab ? 'on' : '') + '">' + UI.icon(t[2]) + t[1] + '</a>';
      }).join('') + '</nav><div data-body><div class="ui-skel"></div></div></div>';
    var body = view.querySelector('[data-body]');

    function overview() {
      return UI.api('admin_overview').then(function (d) {
        var stat = function (n, label, go) { return '<a class="ui-card ui-stat" href="#admin/' + go + '" style="text-decoration:none;color:inherit !important"><b>' + n + '</b><span>' + label + '</span></a>'; };
        body.innerHTML = '<div class="ad-stats">' + stat(d.users, 'people signed up', 'users') + stat(d.admins, UI.plural(d.admins, 'admin').replace(/^\d+ /, ''), 'users') +
          stat(d.feedback_new, 'new feedback', 'feedback') + stat(d.learners, 'active learners', 'users') + stat(d.modules_done, 'modules completed', 'overview') +
          stat(d.attempts, 'challenge attempts', 'overview') + stat(d.exams, 'examinations sat', 'credentials') + stat(d.credentials, 'credentials issued', 'credentials') + '</div>' +
          '<p class="muted small" style="margin-top:18px">Demo data is <b>' + esc(d.demo.state) + '</b> (' + d.demo.counts.users + ' demo people). Manage it in the Demo data tab.</p>';
      });
    }

    function feedback() {
      return UI.api('list_feedback', null).then(function (d) {
        var items = d.items.filter(function (i) { return fbFilter === 'all' || i.status === fbFilter; });
        body.innerHTML = '<div class="ui-row" style="margin-bottom:16px"><div class="ui-seg">' + [['new', 'New'], ['read', 'Read'], ['done', 'Done'], ['all', 'All']].map(function (f) {
          var n = f[0] === 'all' ? d.items.length : d.counts[f[0]];
          return '<button data-filter="' + f[0] + '" class="' + (fbFilter === f[0] ? 'on' : '') + '">' + f[1] + ' (' + n + ')</button>';
        }).join('') + '</div></div>' +
          (items.length ? '<div class="ad-fb">' + items.map(function (i) {
            var c = i.context || {};
            return '<div class="ui-item" data-id="' + esc(i.id) + '"><div class="meta"><span class="ui-badge ' + (i.kind === 'bug' ? 'bad' : i.kind === 'idea' ? 'brand' : '') + '">' + esc(i.kind_label) + '</span>' +
              '<b>' + esc(i.name) + '</b>' + (i.email ? '<a href="mailto:' + esc(i.email) + '">' + esc(i.email) + '</a>' : '') + '<span>' + esc(UI.fmtDateTime(i.created)) + '</span></div>' +
              '<p class="msg">' + esc(i.message) + '</p>' +
              '<div class="ctx">' + esc([c.page, c.screen, c.theme, c.browser].filter(Boolean).join(' · ')) + '</div>' +
              '<textarea data-note placeholder="Private note (only admins see it)">' + esc(i.note) + '</textarea>' +
              '<div class="ui-row" style="margin-top:10px">' + ['new', 'read', 'done'].map(function (s) {
                return '<button class="ui-btn sm' + (i.status === s ? ' primary' : '') + '" data-status="' + s + '">' + s[0].toUpperCase() + s.slice(1) + '</button>';
              }).join('') + '<span class="ui-spacer"></span><button class="ui-btn sm danger" data-del-fb>' + UI.icon('trash') + 'Delete</button></div></div>';
          }).join('') + '</div>'
            : '<div class="ui-empty">' + UI.icon('inbox') + '<h3>No ' + (fbFilter === 'all' ? '' : fbFilter + ' ') + 'messages</h3><p>New feedback goes to Prepsto (prepsto.com). Older messages and requests from the app show up here.</p></div>');
      });
    }

    function users(query) {
      return UI.api('list_users', query || null).then(function (d) {
        body.innerHTML = '<form class="ui-row" data-search style="margin-bottom:14px"><input type="search" name="q" placeholder="Search by name or email" value="' + esc(query || '') + '" style="max-width:360px">' +
          '<button class="ui-btn" type="submit">' + UI.icon('search') + 'Search</button><span class="muted small">' + UI.plural(d.total, 'person', 'people') + '</span></form>' +
          '<table class="ad-users"><thead><tr><th>Name</th><th>Email</th><th>Joined</th><th>Admin</th><th>Active</th></tr></thead><tbody>' +
          d.users.map(function (u) {
            return '<tr data-id="' + esc(u.id) + '"><td><b>' + esc(u.name) + '</b></td><td class="email">' + esc(u.email) + '</td><td class="joined muted">' + esc(UI.fmtDate(u.joined)) + '</td>' +
              '<td><label class="ui-check"><input type="checkbox" data-admin' + (u.is_admin ? ' checked' : '') + '> Admin</label></td>' +
              '<td><label class="ui-check"><input type="checkbox" data-enabled' + (u.enabled ? ' checked' : '') + '> Active</label></td></tr>';
          }).join('') + '</tbody></table>';
      });
    }

    function demo() {
      return UI.api('admin_overview').then(function (d) {
        var c = d.demo.counts;
        body.innerHTML = '<div class="ui-card ui-narrow" style="margin:0"><h3>Demo data</h3>' +
          '<p class="muted">Example people and content, so the app never looks empty for the first visitors. Demo rows are flagged, so removing them never touches real data. Once removed, it stays removed until you load it again.</p>' +
          '<p>Status: <b>' + esc(d.demo.state) + '</b> · ' + Object.keys(c).map(function (k) { return c[k] + ' ' + esc(k); }).join(', ') + '</p>' +
          '<div class="ui-row"><button class="ui-btn primary" data-demo="load">' + UI.icon('refresh') + (d.demo.state === 'loaded' ? 'Reload demo data' : 'Load demo data') + '</button>' +
          '<button class="ui-btn danger" data-demo="remove">' + UI.icon('trash') + 'Remove demo data</button></div></div>';
      });
    }

    function credentials(query) {
      return UI.api('admin_credentials', query || null).then(function (d) {
        body.innerHTML = '<form class="ui-row" data-csearch style="margin-bottom:14px"><input type="search" name="q" placeholder="Search by code or holder" value="' + esc(query || '') + '" style="max-width:360px">' +
          '<button class="ui-btn" type="submit">' + UI.icon('search') + 'Search</button><span class="muted small">' + UI.plural(d.total, 'credential') + '</span></form>' +
          (d.items.length ? '<table class="ad-users"><thead><tr><th>Holder</th><th>Credential</th><th>Issued</th><th>Code</th><th>Status</th></tr></thead><tbody>' +
          d.items.map(function (c) {
            return '<tr data-code="' + esc(c.code) + '"><td><b>' + esc(c.holder) + '</b>' + (c.demo ? ' <span class="ui-badge">Demo</span>' : '') + '<div class="small muted email">' + esc(c.email) + '</div></td>' +
              '<td>' + esc(c.credential) + '</td><td class="joined muted">' + esc(UI.fmtDate(c.issued)) + '</td><td><a href="#certificate/' + esc(c.code) + '">' + esc(c.code) + '</a></td>' +
              '<td><label class="ui-check"><input type="checkbox" data-revoked' + (c.status === 'revoked' ? ' checked' : '') + '> Revoked</label></td></tr>';
          }).join('') + '</tbody></table>' : '<div class="ui-empty">' + UI.icon('award') + '<h3>No credentials yet</h3><p>They appear here when members pass a final examination.</p></div>');
      });
    }

    var DRAW = { overview: overview, credentials: credentials, feedback: feedback, users: users, demo: demo };

    view.addEventListener('click', function (e) {
      var f = e.target.closest('[data-filter]');
      if (f) { fbFilter = f.getAttribute('data-filter'); feedback(); return; }
      var st = e.target.closest('[data-status]');
      if (st) {
        var card = st.closest('[data-id]');
        UI.api('set_feedback_status', card.getAttribute('data-id'), st.getAttribute('data-status'), card.querySelector('[data-note]').value).then(function () { UI.toast('Saved', 'ok'); feedback(); });
        return;
      }
      var del = e.target.closest('[data-del-fb]');
      if (del) {
        UI.confirm({ title: 'Delete this message?', ok: 'Delete', danger: true }).then(function (yes) {
          if (yes) UI.api('delete_feedback', del.closest('[data-id]').getAttribute('data-id')).then(feedback);
        });
        return;
      }
      var dm = e.target.closest('[data-demo]');
      if (dm) {
        var load = dm.getAttribute('data-demo') === 'load';
        UI.confirm({ title: load ? 'Load the demo data?' : 'Remove the demo data?', text: load ? 'Demo people and content are added (any old demo rows are replaced).' : 'Every demo row is deleted. Real data stays.', ok: load ? 'Load' : 'Remove', danger: !load })
          .then(function (yes) { if (yes) UI.busy(dm, UI.api(load ? 'demo_load' : 'demo_remove')).then(function () { UI.toast('Done', 'ok'); demo(); }); });
      }
    });
    view.addEventListener('change', function (e) {
      var crow = e.target.closest('tr[data-code]');
      if (crow && e.target.hasAttribute('data-revoked')) {
        var cb = e.target;
        UI.api('admin_set_revoked', crow.getAttribute('data-code'), cb.checked).then(function () { UI.toast(cb.checked ? 'Credential revoked' : 'Credential reinstated', 'ok'); },
          function (err) { cb.checked = !cb.checked; UI.toast(err.message, 'error'); });
        return;
      }
      var row = e.target.closest('tr[data-id]');
      if (!row) return;
      var id = row.getAttribute('data-id'), box = e.target;
      var fn = box.hasAttribute('data-admin') ? 'set_admin' : box.hasAttribute('data-enabled') ? 'set_enabled' : null;
      if (fn) UI.api(fn, id, box.checked).then(function () { UI.toast('Saved', 'ok'); }, function (err) { box.checked = !box.checked; UI.toast(err.message, 'error'); });
    });
    view.addEventListener('submit', function (e) {
      if (e.target.matches('[data-search]')) { e.preventDefault(); users(UI.formData(e.target).q); }
      if (e.target.matches('[data-csearch]')) { e.preventDefault(); credentials(UI.formData(e.target).q); }
    });
    return DRAW[tab]();
  });
})();

/* ===== auth.html ===== */
(function () {
  var esc = UI.esc;
  var GOOGLE_G = '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>' +
    '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>' +
    '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>' +
    '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>';
  function pw(name, auto) {
    return '<div class="au-pw"><input type="password" name="' + name + '" autocomplete="' + auto + '" required minlength="8">' +
      '<button type="button" data-show>Show</button></div>';
  }
  UI.page('auth', { title: 'Sign in', auth: 'guest' }, function (view, ctx) {
    var mode = ['signup', 'reset'].indexOf(ctx.args[0]) >= 0 ? ctx.args[0] : 'login';
    function draw(msg, isErr) {
      var heading = { login: 'Welcome back', signup: 'Create your account', reset: 'Reset your password' }[mode];
      var sub = { login: 'Sign in to continue to ' + esc(UI.config.name) + '.', signup: 'It\'s free and takes a few seconds.',
        reset: 'We\'ll email you a link to choose a new password.' }[mode];
      view.innerHTML = '<div class="au-wrap"><div class="ui-card au-card">' +
        '<h1>' + heading + '</h1><p class="muted">' + sub + '</p>' +
        (mode !== 'reset' ? '<div class="ui-seg" role="tablist"><button type="button" data-mode="login" class="' + (mode === 'login' ? 'on' : '') + '">Sign in</button>' +
          '<button type="button" data-mode="signup" class="' + (mode === 'signup' ? 'on' : '') + '">Create account</button></div>' : '<div style="height:14px"></div>') +
        '<form class="ui-stack" data-form="' + mode + '" novalidate>' +
        (mode === 'signup' ? '<label class="ui-field"><span>Your name</span><input type="text" name="name" autocomplete="name" required maxlength="60"></label>' : '') +
        '<label class="ui-field"><span>Email</span><input type="email" name="email" autocomplete="email" required></label>' +
        (mode === 'login' ? '<label class="ui-field"><span>Password</span>' + pw('password', 'current-password') + '</label>' : '') +
        (mode === 'signup' ? '<label class="ui-field"><span>Password <em>(at least 8 characters)</em></span>' + pw('password', 'new-password') + '</label>' +
          (window.LegalKit ? '<div>' + LegalKit.consentField() + '</div>' : '') : '') +
        '<div data-msg role="alert"' + (msg ? ' class="' + (isErr ? 'ui-error' : 'ui-note') + '">' + esc(msg) : ' hidden>') + '</div>' +
        '<button class="ui-btn primary block" type="submit">' + { login: 'Sign in', signup: 'Create account', reset: 'Send the link' }[mode] + '</button></form>' +
        (mode !== 'reset' ? '<div class="au-or">or</div><button type="button" class="ui-btn block au-google" data-google>' + GOOGLE_G + 'Continue with Google</button>' : '') +
        '<div class="au-links">' + (mode === 'login' ? '<a data-mode="reset">Forgot your password?</a>' : '<a data-mode="login">' + UI.icon('back') + ' Back to sign in</a>') +
        '<a href="#landing" data-go="landing">About ' + esc(UI.config.name) + '</a></div></div></div>';
      var first = view.querySelector('input');
      if (first && !msg) first.focus();
    }
    view.addEventListener('click', function (e) {
      var m = e.target.closest('[data-mode]');
      if (m) { e.preventDefault(); mode = m.getAttribute('data-mode'); history.replaceState(null, '', '#auth' + (mode === 'login' ? '' : '/' + mode)); draw(); return; }
      var g = e.target.closest('[data-google]');
      if (g) { google(g); return; }
      var s = e.target.closest('[data-show]');
      if (s) { var i = s.parentNode.querySelector('input'); i.type = i.type === 'password' ? 'text' : 'password'; s.textContent = i.type === 'password' ? 'Show' : 'Hide'; }
    });
    view.addEventListener('submit', function (e) {
      e.preventDefault();
      var form = e.target, v = UI.formData(form);
      var problem = !/^\S+@\S+\.\S+$/.test(v.email || '') ? 'Please enter a valid email address.'
        : mode !== 'reset' && (v.password || '').length < (mode === 'signup' ? 8 : 1) ? (mode === 'signup' ? 'Please choose a password of at least 8 characters.' : 'Please enter your password.')
        : mode === 'signup' && (v.name || '').trim().length < 2 ? 'Please tell us your name.' : null;
      if (problem) { say(problem, true); return; }
      if (mode === 'signup' && window.LegalKit && !LegalKit.consentChecked(form)) return;  // the kit shows its own message
      UI.busy(form.querySelector('[type=submit]'), UI.auth(mode, v)).then(function (r) {
        if (mode === 'reset' || (r && !r.me)) { mode = 'login'; draw(r && r.message, false); restore({ email: v.email }); }
        else UI.toast(mode === 'signup' ? 'Welcome to ' + UI.config.name + '!' : 'Welcome back!', 'ok');
      }, function (err) { say(err.message, true); });
    });
    // Sign-up asks for the Privacy & Terms tick here too (ticking it is remembered for the new account).
    function google(btn) {
      var form = view.querySelector('form'), v = mode === 'signup' ? UI.formData(form) : {};
      if (mode === 'signup' && window.LegalKit && !LegalKit.consentChecked(form)) return;
      UI.busy(btn, UI.auth('google', { name: (v.name || '').trim() })).then(function () {
        UI.toast(mode === 'signup' ? 'Welcome to ' + UI.config.name + '!' : 'Welcome back!', 'ok');
      }, function (err) { say(err.message, true); });
    }
    function say(msg, isErr) {
      var box = view.querySelector('[data-msg]');
      box.className = isErr ? 'ui-error' : 'ui-note'; box.textContent = msg; box.hidden = false;
    }
    function restore(v) {
      ['name', 'email'].forEach(function (k) { var i = view.querySelector('[name=' + k + ']'); if (i && v[k]) i.value = v[k]; });
    }
    draw();
  });
})();

/* ===== cases.html ===== */
(function () {
  var esc = UI.esc;
  function list(view) {
    var filter = 'all';
    return UI.api('get_cases').then(function (d) {
      function draw() {
        var items = d.cases.filter(function (c) { return filter === 'all' || c.tone === filter; });
        view.querySelector('[data-list]').innerHTML = items.map(CS.caseCard).join('');
        view.querySelectorAll('[data-f]').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-f') === filter); });
      }
      view.innerHTML = CS.hero({ photo: 'ph-podium', eyebrow: 'The Casebook', title: 'Decisions that made and broke companies',
          lead: 'Documented situations from public reporting, each with the lesson it teaches. Exemplary cases show what to do; cautionary cases show what it costs when it goes wrong.',
          meta: [['book', d.cases.length + ' case files'], ['check', d.cases.filter(function (c) { return c.tone === 'exemplary'; }).length + ' exemplary'],
                 ['alert', d.cases.filter(function (c) { return c.tone === 'cautionary'; }).length + ' cautionary']] }) +
        '<div class="ui-wrap"><div class="cb-filter ui-seg" role="group" aria-label="Filter">' +
          [['all', 'All cases'], ['exemplary', 'Exemplary'], ['cautionary', 'Cautionary'], ['mixed', 'Mixed']].map(function (f) { return '<button data-f="' + f[0] + '">' + f[1] + '</button>'; }).join('') +
        '</div><div class="cb-grid" data-list></div></div>';
      view.addEventListener('click', function (e) { var b = e.target.closest('[data-f]'); if (b) { filter = b.getAttribute('data-f'); draw(); } });
      draw();
    });
  }
  function one(view, id) {
    return UI.api('get_case', id).then(function (r) {
      var c = r.case;
      document.title = c.title + ' · ' + UI.config.name;
      view.innerHTML = CS.hero({ photo: c.tone === 'cautionary' ? 'ph-podium' : 'ph-board-table', crumbs: [['cases', 'The Casebook'], [null, c.company]],
          eyebrow: c.company + ' · ' + c.year, title: c.title, lead: c.summary, meta: [['briefcase', 'Seat: ' + c.role], [c.tone === 'cautionary' ? 'alert' : 'check', c.tone.charAt(0).toUpperCase() + c.tone.slice(1)]] }) +
        '<div class="ui-wrap"><article class="cb-file"><div class="story">' + c.story.map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('') + '</div>' +
        '<div class="cb-lesson"><div class="cs-kicker">The lesson</div><p>' + esc(c.lesson) + '</p></div>' +
        (c.modules.length ? '<div class="cs-kicker">Studied in</div><div class="ui-list" style="margin:10px 0 24px">' + c.modules.map(function (m) {
          return '<a class="ui-item" style="text-decoration:none;color:inherit !important" href="#module/' + esc(m.id) + '"><div class="grow"><h3>' + esc(m.title) + '</h3><p class="small muted">' + esc(m.track) + '</p></div>' + UI.icon('arrow') + '</a>';
        }).join('') + '</div>' : '') +
        '<div class="cs-kicker">Sources</div><ul style="margin:8px 0 0;padding-left:18px">' + c.sources.map(function (s) {
          return '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener" style="overflow-wrap:anywhere">' + esc(s.label) + '</a></li>'; }).join('') + '</ul>' +
        '<p class="small faint" style="margin-top:12px">A summary of public reporting, written for teaching. Details such as figures and quotations vary between sources.</p>' +
        '<div class="cb-nav">' + (c.prev ? '<a class="ui-btn" href="#cases/' + esc(c.prev) + '">' + UI.icon('back') + 'Previous case</a>' : '<span></span>') +
        (c.next ? '<a class="ui-btn" href="#cases/' + esc(c.next) + '">Next case' + UI.icon('arrow') + '</a>' : '') + '</div></article></div>';
    });
  }
  UI.page('cases', { title: 'The Casebook', nav: 'Casebook', icon: 'book', order: 50 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:260px"></div></div>';
    return ctx.args[0] ? one(view, ctx.args[0]) : list(view);
  });
})();

/* ===== certificate.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('certificate', { title: 'Certificate' }, function (view, ctx) {
    var code = ctx.args[0] || '', stop = null;
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:420px"></div></div>';
    var ready = UI.api('get_credential', code).then(function (c) {
      if (!c.found) {
        view.innerHTML = '<div class="ui-wrap ui-narrow"><div class="ui-empty">' + UI.icon('alert') + '<h3>No credential with that ID</h3><p>Check the code and try again.</p>' +
          '<a class="ui-btn primary" href="#verify">Verify a credential</a></div></div>';
        return;
      }
      document.title = c.holder + ', ' + c.credential + ' · ' + UI.config.name;
      var url = CS.verifyUrl(c.code), d = new Date(c.issued);
      var li = 'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=' + encodeURIComponent(c.credential) +
        '&organizationName=' + encodeURIComponent(UI.config.institute) + '&issueYear=' + d.getFullYear() + '&issueMonth=' + (d.getMonth() + 1) +
        '&certUrl=' + encodeURIComponent(url) + '&certId=' + encodeURIComponent(c.code);
      view.innerHTML = '<div class="ce-page"><div class="ce-in"><div class="ce-top no-print"><div><div class="eyebrow">' + esc(UI.config.institute) + ' · Certificate</div><h1>' + esc(c.credential) + '</h1></div>' +
        '<div class="ui-row"><button class="ui-btn" data-copy>' + UI.icon('link') + 'Copy link</button>' +
        (c.mine && c.status === 'valid' ? '<a class="ui-btn" href="' + esc(li) + '" target="_blank" rel="noopener">' + UI.icon('external') + 'Add to LinkedIn</a>' : '') +
        '<button class="ui-btn gold" data-print>' + UI.icon('print') + 'Print or save PDF</button></div></div>' +
        '<div class="cs-cert-wrap" data-wrap>' + CS.cert(c) + '</div>' +
        '<div class="no-print"><div class="ce-status">' + (c.status === 'valid' ? '<span class="ok">' + UI.icon('shield') + '</span><div><h3 style="margin:0">Valid credential</h3><p class="muted" style="margin:2px 0 0">Issued by the ' +
          esc(UI.config.institute) + ' and recorded on its register.' + (c.demo ? ' This is a sample record from the Institute\'s demonstration data.' : '') + '</p></div>'
          : '<span class="no">' + UI.icon('alert') + '</span><div><h3 style="margin:0">This credential has been revoked</h3><p class="muted" style="margin:2px 0 0">It is no longer valid.</p></div>') + '</div>' +
        '<div class="ce-detail"><div><span>Holder</span><b>' + esc(c.holder) + '</b></div><div><span>Credential ID</span><b>' + esc(c.code) + '</b></div>' +
        '<div><span>Issued</span><b>' + esc(UI.fmtDate(c.issued, { day: 'numeric', month: 'long', year: 'numeric' })) + '</b></div><div><span>Program</span><b>' + esc(c.title) + '</b></div></div>' +
        (c.outcomes.length ? '<div class="ui-card" style="margin-top:16px"><div class="cs-kicker">The holder has demonstrated the ability to</div><ul style="margin:10px 0 0;padding-left:18px;color:var(--c-muted)">' +
          c.outcomes.map(function (o) { return '<li>' + esc(o) + '</li>'; }).join('') + '</ul></div>' : '') +
        '<p class="small faint" style="margin-top:16px">' + esc(UI.config.institute) + ' is a private executive-education program. Its credentials are issued on its own authority and are not accredited academic qualifications.</p></div></div></div>';
      stop = CS.fitCert(view.querySelector('[data-wrap]'));
    });
    view.addEventListener('click', function (e) {
      if (e.target.closest('[data-print]')) window.print();
      if (e.target.closest('[data-copy]')) {
        var url = CS.verifyUrl(code.toUpperCase());
        (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { UI.toast('Verification link copied', 'ok'); },
          function () { UI.modal('<h2>Verification link</h2><input type="text" readonly value="' + esc(url) + '">'); });
      }
    });
    return { ready: ready, destroy: function () { if (stop) stop(); } };
  });
})();

/* ===== challenge.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('challenge', { title: 'Challenge', auth: 'user' }, function (view, ctx) {
    var id = ctx.args[0];
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:300px"></div></div>';
    var data = null, answer = '';

    function history(list) {
      if (!list.length) return '<p class="muted small">No attempts yet.</p>';
      return '<div class="ch-hist">' + list.map(function (a) {
        return '<details><summary><span>' + esc(UI.fmtDateTime(a.created)) + '</span><b style="color:' + (a.score >= data.pass_mark ? 'var(--c-good)' : 'var(--c-warn)') + '">' + a.score + '%</b></summary><p>' + esc(a.answer) + '</p></details>';
      }).join('') + '</div>';
    }

    function draw() {
      var c = data.challenge, m = data.module;
      document.title = c.title + ' · ' + UI.config.name;
      view.innerHTML = CS.hero({ photo: c.photo, crumbs: [['tracks/' + m.track_id, m.track], ['module/' + m.id, 'Module ' + m.n + ': ' + m.title], [null, 'Challenge']],
          eyebrow: 'Boardroom challenge', title: c.title, meta: [['target', data.pass_mark + '% of the rubric to pass'], ['star', data.best ? 'Your best: ' + data.best + '%' : 'First attempt']] }) +
        '<div class="ui-wrap"><div class="ch-layout"><div>' +
          '<div class="ch-brief"><div class="cs-kicker">The situation</div><p class="sit">' + esc(c.situation) + '</p><div class="ask">' + esc(c.ask) + '</div></div>' +
          '<form class="ch-form ui-stack" data-write style="margin-top:22px"><label class="ui-field"><span>Your decision <em>(write it as you would brief your board)</em></span>' +
          '<textarea name="answer" required minlength="40" maxlength="6000" placeholder="What do you decide, who do you involve, in what order, and why?">' + esc(answer) + '</textarea></label>' +
          '<div class="ui-row between"><span class="small muted">Commit to an answer before you see the examiners\' notes.</span><button class="ui-btn primary" type="submit">' + UI.icon('arrow') + 'Submit and compare</button></div></form>' +
          '<div data-model></div>' +
        '</div><aside class="ui-stack"><div class="ui-card"><div class="cs-kicker">How it\'s scored</div><p class="small muted" style="margin:8px 0 0">After you submit, you\'ll see the examiners\' model answer and ' + c.rubric.length +
          ' criteria. Tick each one your answer genuinely covered. Be strict: the drill is for you.</p></div>' +
          '<div class="ui-card"><div class="cs-kicker">Your attempts</div><div style="margin-top:10px">' + history(data.attempts) + '</div></div></aside></div></div>';
    }

    function compare() {
      var c = data.challenge;
      var box = view.querySelector('[data-model]');
      view.querySelector('[data-write]').hidden = true;
      box.innerHTML = '<div class="ch-model"><div class="cs-kicker">Your answer</div><div class="mine">' + esc(answer) + '</div>' +
        '<div class="cs-kicker">The examiners\' model answer</div><p class="model">' + esc(c.model) + '</p>' +
        '<div class="cs-kicker" style="margin-bottom:10px">Tick what your answer covered</div><form data-score>' + CS.rubric(c.rubric) +
        '<div class="ui-row between" style="margin-top:16px"><button type="button" class="ui-btn ghost" data-edit>' + UI.icon('edit') + 'Edit my answer</button>' +
        '<button class="ui-btn primary" type="submit">' + UI.icon('check') + 'Record my score</button></div></form><div data-result></div></div>';
      box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    view.addEventListener('submit', function (e) {
      e.preventDefault();
      if (e.target.matches('[data-write]')) {
        answer = UI.formData(e.target).answer.trim();
        if (answer.length < 40) { UI.toast('Write a few sentences first (at least 40 characters).', 'error'); return; }
        compare();
      } else if (e.target.matches('[data-score]')) {
        var btn = e.target.querySelector('[type=submit]');
        UI.busy(btn, UI.api('submit_challenge', id, answer, CS.readRubric(e.target), CS.today())).then(function (r) {
          e.target.querySelectorAll('input,button').forEach(function (x) { x.disabled = true; });
          var res = view.querySelector('[data-result]');
          res.innerHTML = '<div class="ch-result ' + (r.passed ? 'pass' : 'fail') + '"><div class="cs-kicker">' + (r.passed ? 'Passed' : 'Not yet') + '</div><div class="pct">' + r.score + '%</div>' +
            '<p class="small" style="margin:6px 0 14px">' + (r.passed ? (r.module_completed ? 'Module complete. Well done.' : 'Challenge passed. Finish the drills to complete the module.') : 'You need ' + data.pass_mark + '%. Study the model answer and try again.') + ' +' + r.xp_gained + ' XP</p>' +
            '<div class="ui-row" style="justify-content:center"><a class="ui-btn" href="#module/' + esc(data.module.id) + '">Back to the module</a>' +
            (r.passed ? '' : '<button class="ui-btn primary" data-retry>' + UI.icon('refresh') + 'Try again</button>') + '</div></div>';
          if (r.passed) CS.confetti();
        });
      }
    });
    view.addEventListener('click', function (e) {
      if (e.target.closest('[data-edit]')) { view.querySelector('[data-model]').innerHTML = ''; view.querySelector('[data-write]').hidden = false; }
      if (e.target.closest('[data-retry]')) { answer = ''; load(); }
    });
    CS.wireRubric(view);
    function load() { return UI.api('get_challenge', id).then(function (d) { data = d; draw(); }); }
    return load();
  });
})();

/* ===== credentials.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('credentials', { title: 'Credentials', nav: 'Credentials', icon: 'award', auth: 'user', order: 40 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:240px"></div></div>';
    var stops = [];
    function draw(d) {
      var f = d.fellow;
      view.innerHTML = CS.hero({ photo: 'ph-signing', eyebrow: 'The Institute\'s register', title: 'Your credentials',
          lead: 'Every credential has a public verification page. Share the link, print the certificate, or add it to LinkedIn.',
          meta: [['award', UI.plural(d.items.filter(function (i) { return i.status === 'valid'; }).length, 'credential')], ['shield', d.honour_roll ? 'On the Honour Roll' : 'Not on the Honour Roll']] }) +
        '<div class="ui-wrap">' +
        (d.items.length ? '<div class="cr-grid">' + d.items.map(function (c, i) {
          return '<a class="cr-item" href="#certificate/' + esc(c.code) + '"><div class="thumb"><div class="cs-cert-wrap" data-wrap="' + i + '"></div></div><div class="meta"><b>' + esc(c.credential) + '</b>' +
            '<small>' + esc(c.code) + ' · ' + esc(UI.fmtDate(c.issued)) + '</small> ' + (c.status === 'revoked' ? '<span class="ui-badge bad">Revoked</span>' : '<span class="ui-badge good">Valid</span>') + '</div></a>';
        }).join('') + '</div>'
          : '<div class="ui-empty"><span style="display:inline-block;margin-bottom:10px">' + UI.seal(90) + '</span><h3>No credentials yet</h3><p>Complete every module of a program, then pass its final examination. Executive Foundations is the place to start.</p>' +
            '<a class="ui-btn primary" href="#tracks/core">Open Executive Foundations</a></div>') +
        '<div class="cs-panel" style="margin-top:26px"><header><h3>The path to Fellowship</h3><span class="small muted">' + (f.have ? 'Achieved' : (f.core ? 1 : 0) + f.roles + ' of 3') + '</span></header><div class="body">' +
          '<div class="cr-fellow"><div>' + UI.seal(96) + '</div><div><p class="muted" style="margin-top:0">Hold Executive Foundations and any two role certificates to be admitted as a <b>Fellow of the C-Suite Coach Institute (FCSCI)</b>.</p>' +
          '<div class="cr-path">' + d.tracks.map(function (t) {
            return '<div class="' + (t.have ? 'have' : '') + '">' + UI.icon(t.have ? 'award' : 'lock') + '<span>' + esc(t.title) + '</span></div>';
          }).join('') + '</div></div></div></div></div>' +
        '<div class="cs-panel" style="margin-top:20px"><header><h3>Honour Roll</h3></header><div class="body"><label class="ui-check"><input type="checkbox" data-honour' + (d.honour_roll ? ' checked' : '') + '>' +
          '<span>Show my name, job title and credentials on the public Honour Roll. <span class="muted">Your credential codes can be verified either way.</span></span></label></div></div>' +
        '</div>';
      d.items.forEach(function (c, i) {
        var w = view.querySelector('[data-wrap="' + i + '"]');
        w.innerHTML = CS.cert(c);
        stops.push(CS.fitCert(w));
      });
    }
    view.addEventListener('change', function (e) {
      if (!e.target.matches('[data-honour]')) return;
      var on = e.target.checked;
      UI.api('update_profile', ctx.me.name, null, on).then(function (r) { UI.setMe(r.me); UI.toast(on ? 'You\'re on the Honour Roll' : 'Removed from the Honour Roll', 'ok'); },
        function (err) { e.target.checked = !on; UI.toast(err.message, 'error'); });
    });
    var ready = UI.api('my_credentials').then(draw);
    return { ready: ready, destroy: function () { stops.forEach(function (s) { s(); }); } };
  });
})();

/* ===== exam.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('exam', { title: 'Final examination', auth: 'user' }, function (view, ctx) {
    var track = ctx.args[0], d = null, ratings = {}, answer = '', stopFit = null;
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:300px"></div></div>';

    function head(sub) {
      return CS.hero({ photo: 'ph-signing', crumbs: [['tracks', 'Programs'], ['tracks/' + d.track.id, d.track.title], [null, 'Examination']],
        eyebrow: 'Board of Examiners', title: 'Final examination: ' + d.track.title, lead: sub || ('For the ' + d.track.credential + '.') });
    }
    function hist() {
      if (!d.history.length) return '';
      return '<div class="ui-card" style="margin-top:18px"><div class="cs-kicker">Previous sittings</div><table class="ex-hist"><thead><tr><th>Date</th><th>Recall</th><th>Capstone</th><th>Result</th></tr></thead><tbody>' +
        d.history.map(function (h) { return '<tr><td>' + esc(UI.fmtDateTime(h.finished)) + '</td><td>' + h.drill + '%</td><td>' + h.scenario + '%</td><td>' + (h.passed ? '<span class="ui-badge good">Passed</span>' : '<span class="ui-badge warn">Not passed</span>') + '</td></tr>'; }).join('') +
        '</tbody></table></div>';
    }

    function intro() {
      view.innerHTML = head() + '<div class="ui-wrap"><div class="ex-wrap"><div class="ex-paper"><div class="cs-kicker">Instructions to candidates</div><h2>Two parts, one sitting</h2>' +
        '<p class="muted">Allow about 30 minutes. Answer from memory: no notes, no briefings, no searching.</p>' +
        '<div class="ex-rules"><div><b>' + d.items.length + '</b><span>Part I: recall drills from the whole program. ' + d.pass_drill + '% “Got it” to pass.</span></div>' +
        '<div><b>1</b><span>Part II: the capstone case “' + esc(d.capstone.title) + '”. ' + d.pass_scenario + '% of the rubric to pass.</span></div>' +
        '<div><b>' + d.retake_minutes + '′</b><span>If you don\'t pass, you can sit it again after ' + d.retake_minutes + ' minutes.</span></div></div>' +
        '<label class="ui-check ex-honour"><input type="checkbox" data-honour><span><b>Honour code.</b> I will answer from memory without notes or help, and score myself strictly against the criteria. ' +
        'I understand my credential will carry my name and a public verification code.</span></label>' +
        '<div class="ui-row end"><a class="ui-btn ghost" href="#tracks/' + esc(d.track.id) + '">Not now</a><button class="ui-btn primary lg" data-begin disabled>' + UI.icon('pen') + 'Begin the examination</button></div></div>' + hist() + '</div></div>';
    }

    function part1() {
      view.innerHTML = head('Part I of II: recall') + '<div class="ui-wrap"><div class="ex-part"><span class="pill">Part I</span><h2>Recall round</h2></div><div data-drill></div></div>';
      CS.drill(view.querySelector('[data-drill]'), d.items, {
        exam: true,
        rate: function (it, knew) { ratings[it.id] = knew; },
        done: function () { part2(); }
      });
    }

    function part2() {
      var c = d.capstone;
      view.innerHTML = head('Part II of II: the capstone case') + '<div class="ui-wrap"><div class="ex-wrap"><div class="ex-part" style="max-width:none"><span class="pill">Part II</span><h2>' + esc(c.title) + '</h2></div>' +
        '<div class="ex-paper"><div class="cs-kicker">The situation</div><p style="font-size:1.06rem;line-height:1.7">' + esc(c.situation) + '</p>' +
        '<p style="font:600 1.4rem/1.3 var(--font-display)">' + esc(c.ask) + '</p>' +
        '<form class="ui-stack" data-write><textarea name="answer" required minlength="80" maxlength="8000" style="min-height:240px" placeholder="Your plan, in the order you would act.">' + esc(answer) + '</textarea>' +
        '<div class="ui-row end"><button class="ui-btn primary" type="submit">' + UI.icon('arrow') + 'Submit answer and see the criteria</button></div></form><div data-mark></div></div></div></div>';
    }

    function mark() {
      var c = d.capstone, box = view.querySelector('[data-mark]');
      view.querySelector('[data-write]').hidden = true;
      box.innerHTML = '<div class="cs-kicker">Your answer</div><div style="white-space:pre-wrap;background:var(--c-surface-2);padding:14px;border-radius:4px;margin:8px 0 18px;overflow-wrap:anywhere">' + esc(answer) + '</div>' +
        '<div class="cs-kicker">The examiners\' model answer</div><p style="line-height:1.65">' + esc(c.model) + '</p>' +
        '<div class="cs-kicker" style="margin-bottom:10px">Tick each criterion your answer met</div><form data-final>' + CS.rubric(c.rubric) +
        '<div class="ui-row end" style="margin-top:18px"><button class="ui-btn gold lg" type="submit">' + UI.icon('award') + 'Submit to the Board of Examiners</button></div></form>';
      box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function result(r) {
      if (r.passed) CS.confetti();
      view.innerHTML = head(r.passed ? 'Congratulations.' : 'Not passed this time.') + '<div class="ui-wrap"><div class="ex-wrap"><div class="ex-paper" style="text-align:center">' +
        '<div class="cs-kicker">' + (r.passed ? 'The Board of Examiners has issued your credential' : 'Result') + '</div>' +
        '<div class="ex-scores"><div><b style="color:' + (r.drill >= d.pass_drill ? 'var(--c-good)' : 'var(--c-bad)') + '">' + r.drill + '%</b><span>Recall (' + d.pass_drill + '% to pass)</span></div>' +
        '<div><b style="color:' + (r.scenario >= d.pass_scenario ? 'var(--c-good)' : 'var(--c-bad)') + '">' + r.scenario + '%</b><span>Capstone (' + d.pass_scenario + '% to pass)</span></div></div>' +
        (r.passed ? '<div class="cs-cert-wrap" data-wrap style="margin:10px 0 20px"></div>' +
            (r.fellow ? '<p class="ui-note">' + UI.icon('star') + ' You now hold Foundations and two role certificates: you have been admitted as a <b>Fellow of the Institute</b>. <a href="#certificate/' + esc(r.fellow) + '">See your Fellowship certificate</a>.</p>' : '') +
            '<div class="ui-row" style="justify-content:center"><a class="ui-btn primary" href="#certificate/' + esc(r.code) + '">' + UI.icon('award') + 'Open your certificate</a><a class="ui-btn" href="#credentials">All credentials</a></div>'
          : '<p class="muted">Review the drills you missed (they\'re due again today) and the capstone criteria. You can sit the examination again in ' + r.retake_minutes + ' minutes.</p>' +
            '<div class="ui-row" style="justify-content:center"><a class="ui-btn primary" href="#study/review">' + UI.icon('cards') + 'Review now</a><a class="ui-btn" href="#tracks/' + esc(d.track.id) + '">Back to the program</a></div>') +
        '</div></div></div>';
      if (r.passed) {
        UI.apiQuiet('get_credential', r.code).then(function (c) {
          var w = view.querySelector('[data-wrap]');
          if (w) { w.innerHTML = CS.cert(c); stopFit = CS.fitCert(w); }
        });
      }
    }

    function other() {
      var body;
      if (d.state === 'certified') {
        body = '<div class="ex-paper" style="text-align:center"><div class="cs-kicker">Already certified</div><h2>You hold the ' + esc(d.track.credential) + '</h2>' +
          '<a class="ui-btn primary" href="#certificate/' + esc(d.status.credential.code) + '">' + UI.icon('award') + 'View certificate</a></div>';
      } else if (d.state === 'cooldown') {
        body = '<div class="ex-paper" style="text-align:center"><div class="cs-kicker">Please wait</div><h2>You can sit the examination again in ' + UI.plural(d.minutes, 'minute') + '</h2>' +
          '<p class="muted">Use the time to review: missed drills from your last sitting are due now.</p><a class="ui-btn primary" href="#study/review">' + UI.icon('cards') + 'Review now</a></div>';
      } else {
        body = '<div class="ex-paper"><div class="cs-kicker">Not yet open</div><h2>Complete every module first</h2><p class="muted">The examination opens when all ' + d.status.modules + ' modules are complete. Still to finish:</p>' +
          '<div class="ui-list">' + d.missing.map(function (m) { return '<a class="ui-item" style="text-decoration:none;color:inherit !important" href="#module/' + esc(m.id) + '"><div class="grow"><h3>' + esc(m.title) + '</h3></div>' + UI.icon('arrow') + '</a>'; }).join('') + '</div></div>';
      }
      view.innerHTML = head() + '<div class="ui-wrap"><div class="ex-wrap">' + body + hist() + '</div></div>';
    }

    view.addEventListener('change', function (e) {
      if (e.target.matches('[data-honour]')) view.querySelector('[data-begin]').disabled = !e.target.checked;
    });
    view.addEventListener('click', function (e) { if (e.target.closest('[data-begin]')) part1(); });
    view.addEventListener('submit', function (e) {
      e.preventDefault();
      if (e.target.matches('[data-write]')) {
        answer = UI.formData(e.target).answer.trim();
        if (answer.length < 80) { UI.toast('Write at least a short paragraph (80 characters).', 'error'); return; }
        mark();
      } else if (e.target.matches('[data-final]')) {
        UI.busy(e.target.querySelector('[type=submit]'), UI.api('submit_exam', d.exam_id, ratings, answer, CS.readRubric(e.target), true, CS.today())).then(result);
      }
    });
    CS.wireRubric(view);

    var ready = UI.api('get_exam', track).then(function (r) {
      d = r;
      document.title = 'Examination: ' + d.track.title + ' · ' + UI.config.name;
      if (d.state === 'ready') intro(); else other();
    });
    return { ready: ready, destroy: function () { if (stopFit) stopFit(); } };
  });
})();

/* ===== home.html ===== */
(function () {
  var esc = UI.esc;
  function greeting() { var h = new Date().getHours(); return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'; }

  UI.page('home', { title: 'Dashboard', nav: 'Home', icon: 'home', auth: 'user', order: 10 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:160px"></div><div class="ui-skel" style="height:260px;margin-top:20px"></div></div>';
    function draw(d) {
      var me = d.me, r = me.rank, first = ctx.me.name.split(' ')[0];
      var into = r.next_at ? Math.round(100 * (me.xp - r.floor) / (r.next_at - r.floor)) : 100;
      var n = d.next;
      var stepBadge = function (ok, label) { return '<span class="ui-badge ' + (ok ? 'good' : '') + '">' + UI.icon(ok ? 'check' : 'clock') + label + '</span>'; };
      view.innerHTML =
        '<section class="hm-top"><div class="ph"></div><div class="in"><div><div class="eyebrow">' + esc(greeting()) + (me.title ? ' · ' + esc(me.title) : '') + '</div>' +
          '<h1>Welcome back, ' + esc(first) + '</h1><p class="sub">' + d.learned + ' of ' + d.total_items + ' drills learned · ' + d.modules_done + ' of ' + d.modules_total + ' modules complete · ' +
          UI.plural(d.credentials.length, 'credential') + '</p></div>' +
          '<div class="hm-rank"><div class="r"><b>' + esc(r.rank) + '</b><span>' + me.xp + ' XP</span></div>' + CS.bar(into) +
          '<div class="r"><span>' + (r.next ? (r.next_at - me.xp) + ' XP to ' + esc(r.next) : 'The highest rank') + '</span><span>' + UI.icon('flame') + ' ' + UI.plural(me.streak, 'day') + '</span></div></div></div></section>' +
        '<div class="ui-wrap" style="padding-top:0"><div class="hm-grid"><div class="hm-col">' +
          '<div class="ui-card hm-review"><div class="big">' + d.due + '</div><div><h3>' + (d.due ? 'Drills due for review today' : 'You\'re up to date') + '</h3>' +
            '<p class="muted small" style="margin:0">' + (d.due ? 'A few minutes of recall keeps it for months.' : 'New drills come due as your memory needs them. Keep going with a module.') + '</p>' +
            '<div class="hm-week">' + d.week.map(function (w) { return '<i class="' + (w.active ? 'on' : '') + '" title="' + esc(w.day) + '">' + 'SMTWTFS'[new Date(w.day + 'T12:00:00').getDay()] + '</i>'; }).join('') + '</div></div>' +
            (d.due ? '<a class="ui-btn primary lg" href="#study/review" data-go="study/review">' + UI.icon('cards') + 'Start review</a>' : '<a class="ui-btn lg" href="#tracks" data-go="tracks">' + UI.icon('columns') + 'Programs</a>') + '</div>' +
          d.ready_exam.map(function (id) {
            var t = d.tracks.filter(function (x) { return x.id === id; })[0];
            return '<div class="ui-card hm-exam ui-row between"><div><div class="cs-kicker">Examination open</div><h3 style="margin:4px 0 0">' + esc(t.title) + '</h3>' +
              '<p class="muted small" style="margin:4px 0 0">You\'ve completed every module. Sit the final examination for your ' + esc(t.credential) + '.</p></div>' +
              '<a class="ui-btn gold" href="#exam/' + esc(id) + '" data-go="exam/' + esc(id) + '">' + UI.icon('award') + 'Sit the examination</a></div>';
          }).join('') +
          (n ? '<div class="ui-card hm-next"><div class="img" style="background-image:url(' + UI.photo(n.photo) + ')"></div><div class="txt">' +
            '<div class="cs-kicker">' + (n.status.pct ? 'Continue' : 'Up next') + ' · ' + esc(n.track) + ' · Module ' + n.n + '</div>' +
            '<h3>' + esc(n.title) + '</h3><p class="muted" style="margin:0">' + esc(n.summary) + '</p>' +
            '<div class="hm-steps">' + stepBadge(n.status.read, 'Briefing') + stepBadge(n.status.learned === n.status.total, 'Drills ' + n.status.learned + '/' + n.status.total) +
            stepBadge(n.status.challenge_passed, 'Challenge') + '</div>' +
            '<div class="ui-row" style="margin-top:6px"><a class="ui-btn primary" href="#module/' + esc(n.id) + '" data-go="module/' + esc(n.id) + '">' + UI.icon('arrow') + (n.status.pct ? 'Continue' : 'Begin') + '</a></div></div></div>'
            : '<div class="ui-card"><h3>Every started program is complete</h3><p class="muted">Choose your next program and keep building toward the Fellowship.</p><a class="ui-btn primary" href="#tracks" data-go="tracks">Browse programs</a></div>') +
          '<div class="cs-panel"><header><h3>Your programs</h3><a class="small" href="#tracks">All programs</a></header><div class="body hm-tracks">' +
            d.tracks.map(function (t) {
              var s = t.status;
              return '<a class="hm-track" href="#tracks/' + esc(t.id) + '"><span class="th" style="background-image:url(' + UI.photo(t.photo) + ')"></span>' +
                '<div><b>' + esc(t.title) + '</b><small>' + esc(t.role) + ' · ' + s.modules_done + '/' + s.modules + ' modules</small>' + CS.bar(s.pct) + '</div>' +
                (s.certified ? '<span class="ui-badge gold">' + UI.icon('award') + 'Certified</span>' : s.exam_ready ? '<span class="ui-badge brand">Exam open</span>' : '<span class="small muted">' + s.pct + '%</span>') + '</a>';
            }).join('') + '</div></div>' +
        '</div><div class="hm-col">' +
          '<div class="cs-panel"><header><h3>Your credentials</h3><a class="small" href="#credentials">View all</a></header><div class="body">' +
            (d.credentials.length ? d.credentials.map(function (c) {
              return '<a class="hm-cred" href="#certificate/' + esc(c.code) + '"><span class="medal">' + UI.icon('award') + '</span><div><b>' + esc(c.credential) + '</b><small>' + esc(c.code) + ' · ' + esc(UI.fmtDate(c.issued)) + '</small></div></a>';
            }).join('') : '<p class="muted small" style="margin:0">Complete a program and pass its examination to earn your first credential. Executive Foundations is the place to start.</p>') +
          '</div></div>' +
          '<div class="cs-panel"><header><h3>Case of the day</h3>' + CS.tone(d.case.tone) + '</header><div class="body">' +
            '<div class="small muted">' + esc(d.case.company) + ' · ' + esc(d.case.year) + '</div><h4 style="font-size:1.35rem;margin:4px 0 6px">' + esc(d.case.title) + '</h4>' +
            '<p class="muted small">' + esc(d.case.summary) + '</p><a class="ui-btn sm" href="#cases/' + esc(d.case.id) + '">' + UI.icon('book') + 'Read the case</a></div></div>' +
          '<div class="cs-panel"><header><h3>Honour Roll</h3><span class="small muted">Recently certified</span></header><div class="body hm-honour">' +
            (d.honour.length ? d.honour.map(function (h) {
              return '<a href="#verify/' + esc(h.code) + '"><span class="ui-avatar">' + esc(UI.initials(h.name)) + '</span><div><b>' + esc(h.name) + '</b><small>' + esc(h.credential) + ' · ' + esc(UI.ago(h.issued)) + '</small></div></a>';
            }).join('') : '<p class="muted small">No one yet. Opt in from your profile when you\'re certified.</p>') + '</div></div>' +
        '</div></div></div>';
    }
    return UI.api('get_dashboard', CS.today()).then(draw);
  });
})();

/* ===== landing.html ===== */
// Watch section: swap the video's cover for YouTube's player (privacy-enhanced) only when it's pressed.
  if (!window.__ytFilm) {
    window.__ytFilm = true;
    document.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[data-yt-film]') : null;
      if (!b) return;
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-yt-film') + '?autoplay=1&rel=0&playsinline=1';
      f.title = b.getAttribute('data-yt-title') || 'Video';
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen = true;
      f.referrerPolicy = 'strict-origin-when-cross-origin';
      b.parentNode.replaceChild(f, b);
    });
  }
(function () {
  var esc = UI.esc;
  var SAMPLE = { holder: 'Margaret Okafor', credential: 'Certificate in Chief Financial Leadership', code: 'CSC-CFO-2026-T4WX9N', issued: new Date().toISOString(), track: 'cfo', demo: true,
                 modules: ['The four faces of the CFO', 'Liquidity, rates and risk', 'Investors, guidance and integrity'] };
  var STEPS = [
    ['book', 'Study the briefing', 'Research-based essentials, what excellent executives do, the advice to avoid, and real case files.'],
    ['cards', 'Drill to retention', 'Active recall and advice calls on spaced repetition, so what you learn is still there in six months.'],
    ['target', 'Pass the challenge', 'A realistic boardroom scenario. Write your decision, then score it against the examiners\' rubric.'],
    ['award', 'Sit the examination', 'A recall round and a capstone case under an honour code. Pass, and your credential is issued with a public verification code.']
  ];
  var FAQ = [
    ['Is this an accredited qualification?', 'No. C-Suite Coach Institute is a private executive-education program. Its certificates are issued on the Institute\'s own authority and verified on its own register. They show that you completed a demanding course of study and examination; they are not university degrees or regulated professional licences.'],
    ['Who is it for?', 'Current C-suite executives, the vice-presidents and directors preparing for the role, founders who suddenly have a board, and anyone who wants to understand how good executives think.'],
    ['How long does a certificate take?', 'Executive Foundations is about 2 hours of study plus your drill sessions over a week or two; each role program is about 1 to 1.5 hours. Spaced repetition works best a little every day.'],
    ['How do the examinations work?', 'Every module ends with a scenario challenge. The final examination combines a recall round of 12 items drawn from the whole program (80% to pass) with a capstone scenario scored against a rubric (70% to pass). Both are self-assessed under an honour code; you can retake after 30 minutes.'],
    ['Where does the content come from?', 'From published research and public reporting: McKinsey\'s CEO Excellence study, the CEO Genome Project in Harvard Business Review, Spencer Stuart, Deloitte, NACD, the work of Jim Collins and Amy Edmondson, regulators\' rules, and well-documented cases. Every module lists its sources. No affiliation with or endorsement by these organisations is implied.'],
    ['What does it cost?', 'Nothing. Enrol with an email address and start studying.'],
    ['Who can see my progress?', 'Only you. If you opt in to the Honour Roll, your name, job title and credentials appear there. Anyone with a credential code can verify it; that is what a credential is for.']
  ];

  UI.page('landing', { title: 'Executive certification' }, function (view, ctx) {
    var me = ctx.me;
    var primary = me ? '<a class="ui-btn gold lg" href="#home" data-go="home">Go to your dashboard ' + UI.icon('arrow') + '</a><a class="ui-btn lg ghostl" href="#tracks" data-go="tracks">Programs</a>'
      : '<a class="ui-btn gold lg" href="#auth/signup" data-go="auth/signup">Enrol, free ' + UI.icon('arrow') + '</a><a class="ui-btn lg ghostl" href="#tracks" data-go="tracks">Explore the programs</a>';
    view.innerHTML =
      '<section class="lp-hero"><div class="bg"></div><div class="in"><div class="lp-copy">' +
        '<div class="eyebrow">C-Suite Coach Institute · Executive certification</div>' +
        '<h1>The standard for <em>executive judgement</em>.</h1>' +
        '<p class="lp-lead">Seven certification programs for current and aspiring C-suite leaders. Learn from real boardroom cases, practise decisions in scenario challenges, and lock it in with spaced-repetition drills. Earn credentials anyone can verify.</p>' +
        '<div class="lp-cta">' + primary + '</div>' +
        '<div class="lp-proof"><div><b data-n="tracks">7</b><span>Programs</span></div><div><b data-n="cases">24</b><span>Case files</span></div><div><b data-n="items">200+</b><span>Drills</span></div><div><b data-n="challenges">31</b><span>Challenges</span></div></div>' +
      '</div><div class="lp-art" aria-hidden="true"><div class="mini"><div class="cs-cert-wrap" data-wrap>' + CS.cert(SAMPLE) + '</div></div>' +
        '<div class="lp-verify">' + UI.icon('check') + '<span>Verified on the Institute\'s register</span><code>' + esc(SAMPLE.code) + '</code></div>' +
        '<div class="chip">' + UI.icon('check') + '<div><b>Challenge passed · 86%</b>Two Days Before the Board</div></div>' +
        '<div class="chip chip2">' + UI.icon('flame') + '<div><b>12-day streak</b>Daily review done</div></div></div></div></section>' +

      '<div class="lp-strip"><div class="in"><span class="lbl">Grounded in published research</span>' +
        ['McKinsey', 'Harvard Business Review', 'Spencer Stuart', 'Deloitte', 'NACD', 'Good to Great'].map(function (s) { return '<span class="src">' + s + '</span>'; }).join('') + '</div></div>' +

      '<section class="lp-section ytf" id="watch"><div class="ui-wrap"><div class="ytf-in"><div class="ytf-copy"><div class="eyebrow"><svg viewBox="0 0 28 20" width="20" height="14" aria-hidden="true"><rect width="28" height="20" rx="5" fill="#FF0033"/><path d="M11.2 5.8v8.4l7.3-4.2z" fill="#fff"/></svg>Watch</div><h2>See C-Suite Coach in about a minute</h2><p>A short video tour of what C-Suite Coach does and how it works.</p><a class="ytf-link" href="https://www.youtube.com/watch?v=Z5MC3w_B89A" target="_blank" rel="noopener">Watch on YouTube &#8599;</a></div><div><div class="ytf-frame"><button type="button" class="ytf-cover" data-yt-film="Z5MC3w_B89A" data-yt-title="C-Suite Coach video" aria-label="Play the C-Suite Coach video (1:12)"><img src="_/theme/yt-cover.jpg" alt="" loading="lazy" decoding="async" width="960" height="540"><span class="ytf-play" aria-hidden="true"><svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.3.3 34 .3 34 .3s-21.3 0-26.5 1.4a8.5 8.5 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.5 8.5 0 0 0 6 6c5.2 1.4 26.5 1.4 26.5 1.4s21.3 0 26.5-1.4a8.5 8.5 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="#FF0033"/><path d="M45 24 27 14v20z" fill="#fff"/></svg></span><span class="ytf-len">1:12</span></button></div><p class="ytf-note">The video loads from YouTube when you press play.</p></div></div></div></section>' +
      '<section class="lp-section" id="how"><div class="ui-wrap"><div class="lp-head"><div class="eyebrow">The method</div><h2>How certification works</h2>' +
        '<p>Modelled on how professionals in high-stakes fields train: understand it, recall it until it\'s automatic, then apply it under pressure.</p></div>' +
        '<div class="lp-steps">' + STEPS.map(function (s, i) { return '<div class="lp-step">' + UI.icon(s[0]) + '<div class="n">' + ['I', 'II', 'III', 'IV'][i] + '</div><h3>' + esc(s[1]) + '</h3><p>' + esc(s[2]) + '</p></div>'; }).join('') + '</div></div></section>' +

      '<section class="lp-section alt"><div class="ui-wrap"><div class="lp-head"><div class="eyebrow">Programs</div><h2>Seven paths to the C-suite</h2>' +
        '<p>Start with Executive Foundations, then specialise. Hold Foundations and two role certificates to be admitted as a Fellow of the Institute.</p></div>' +
        '<div class="lp-programs" data-programs><div class="ui-skel" style="height:300px"></div><div class="ui-skel" style="height:300px"></div><div class="ui-skel" style="height:300px"></div></div></div></section>' +

      '<section class="lp-section"><div class="ui-wrap"><div class="lp-head"><div class="eyebrow">The Casebook</div><h2>Learn from what really happened</h2>' +
        '<p>Twenty-four documented situations, from the Tylenol recall to the collapse of Silicon Valley Bank, each with the lesson it teaches.</p></div>' +
        '<div class="lp-cases" data-cases></div><p style="text-align:center;margin-top:22px"><a class="ui-btn" href="#cases" data-go="cases">' + UI.icon('book') + 'Open the Casebook</a></p></div></section>' +

      '<section class="lp-section alt"><div class="ui-wrap"><div class="lp-head"><div class="eyebrow">Sound advice, and traps</div><h2>What the research says</h2></div>' +
        '<div class="cs-dd"><div class="good"><h4>' + UI.icon('check') + 'What excellent executives do</h4><ul>' +
        ['Decide earlier, and match the process to how reversible the decision is.', 'Thank the first person who brings bad news.', 'Tell the board chair before the meeting, never during it.',
         'Act on stated values in a crisis before all the facts are in.', 'Judge every use of capital by long-term value per share.', 'Change incentives together with the message.'].map(function (t) { return '<li>' + UI.icon('check') + '<span>' + esc(t) + '</span></li>'; }).join('') +
        '</ul></div><div class="bad"><h4>' + UI.icon('x') + 'Advice to avoid</h4><ul>' +
        ['"Never decide until you have all the facts."', '"My door is always open, so people will tell me."', '"Don\'t apologise: it admits liability."',
         '"A board of famous names protects the company."', '"Fix misconduct with more ethics training."', '"Announce your vision in week one."'].map(function (t) { return '<li>' + UI.icon('x') + '<span>' + esc(t) + '</span></li>'; }).join('') +
        '</ul></div></div></div></section>' +

      '<section class="lp-section"><div class="ui-wrap lp-quote"><blockquote>Once I have 65% certainty around the answer, I have to make a call.</blockquote>' +
        '<cite>A CEO quoted in the CEO Genome Project, Harvard Business Review, 2017</cite></div></section>' +

      '<section class="lp-section alt"><div class="ui-wrap lp-certrow"><div><div class="eyebrow">Credentials</div><h2>A certificate you can stand behind</h2>' +
        '<p class="muted">Every credential carries a unique ID and a public verification page on the Institute\'s register. Print it, add it to your LinkedIn profile, or send the link to anyone who asks.</p>' +
        '<form class="ui-row" data-verify style="margin-top:18px"><input type="text" name="code" placeholder="e.g. CSC-CFO-2026-T4WX9N" style="max-width:300px" aria-label="Credential ID">' +
        '<button class="ui-btn primary" type="submit">' + UI.icon('shield') + 'Verify</button></form></div>' +
        '<div><div class="eyebrow">Honour Roll</div><div class="lp-honour" data-honour></div></div></div></section>' +

      '<section class="lp-section"><div class="ui-wrap"><div class="lp-head"><h2>Questions</h2></div><div class="lp-faq">' +
        FAQ.map(function (q) { return '<details><summary>' + esc(q[0]) + '</summary><p>' + esc(q[1]) + '</p></details>'; }).join('') + '</div></div></section>' +

      '<section class="lp-section" style="padding-top:0"><div class="ui-wrap"><div class="lp-band"><div><h2>Begin with Executive Foundations</h2><p>Six modules, one examination, and your first credential.</p></div>' +
        (me ? '<a class="ui-btn gold lg" href="#tracks/core" data-go="tracks/core">Open the program</a>' : '<a class="ui-btn gold lg" href="#auth/signup" data-go="auth/signup">Enrol, free</a>') +
      '</div></div></section>';

    var stopFit = CS.fitCert(view.querySelector('[data-wrap]'));
    view.addEventListener('submit', function (e) {
      if (!e.target.matches('[data-verify]')) return;
      e.preventDefault();
      var code = UI.formData(e.target).code.trim();
      if (code) UI.go('verify', code);
    });
    var cases = ['tylenol', 'redslide', 'svb'];
    var ready = Promise.all([UI.api('get_catalog'), UI.apiQuiet('get_cases'), UI.apiQuiet('get_honour_roll')]).then(function (r) {
      view.querySelector('[data-programs]').innerHTML = r[0].tracks.map(CS.trackCard).join('');
      var n = { tracks: r[0].tracks.length, cases: r[0].cases, items: r[0].totals.items, challenges: r[0].totals.challenges };
      Object.keys(n).forEach(function (k) { view.querySelector('[data-n="' + k + '"]').textContent = n[k]; });
      view.querySelector('[data-cases]').innerHTML = r[1].cases.filter(function (c) { return cases.indexOf(c.id) >= 0; }).map(CS.caseCard).join('');
      var h = r[2].items.slice(0, 6);
      view.querySelector('[data-honour]').innerHTML = h.length ? h.map(function (x) {
        return '<a href="#verify/' + esc(x.code) + '"><span class="ui-avatar">' + esc(UI.initials(x.name)) + '</span><div><b>' + esc(x.name) + '</b><small>' + esc(x.title) + '</small>' +
          '<small style="color:var(--c-accent-ink)">' + esc(x.credential) + '</small></div></a>';
      }).join('') : '<p class="muted">The first graduates will appear here.</p>';
    });
    return { ready: ready, destroy: stopFit };
  });
})();

/* ===== module.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('module', { title: 'Module' }, function (view, ctx) {
    var id = ctx.args[0];
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:260px"></div></div>';
    if (!id) { UI.go('tracks'); return Promise.resolve(); }

    function steps(m) {
      var st = m.status;
      if (!st) return '<div class="ui-card md-steps"><div class="cs-kicker">Members</div><h3 style="margin:6px 0">Earn this module</h3>' +
        '<p class="muted small">Enrol to drill the ' + m.items + ' recall items with spaced repetition, take the challenge “' + esc(m.challenge.title) + '”, and work toward the ' + esc(m.track.title) + ' certificate.</p>' +
        '<a class="ui-btn primary block" href="#auth/signup" data-go="auth/signup">Enrol, free</a></div>';
      var learned = st.learned === st.total;
      return '<div class="md-steps"><div class="ui-card">' +
        '<div class="ui-row between"><div class="cs-kicker">Module ' + m.n + ' of ' + m.track.count + '</div>' + CS.ring(st.pct, 50) + '</div>' +
        (st.complete ? '<div class="md-complete" style="margin-top:12px">' + UI.icon('award') + '<h3>Module complete</h3><p class="small muted" style="margin:0">Keep reviewing the drills as they come due.</p></div>' : '') +
        '<div class="md-step ' + (st.read ? 'done' : '') + '"><span class="dot">' + (st.read ? UI.icon('check') : 'I') + '</span><div><b>Read the briefing</b><p>The research, the advice and the cases.</p>' +
          (st.read ? '' : '<button class="ui-btn sm" data-read>' + UI.icon('check') + 'Mark as read</button>') + '</div></div>' +
        '<div class="md-step ' + (learned ? 'done' : '') + '"><span class="dot">' + (learned ? UI.icon('check') : 'II') + '</span><div><b>Drill: ' + st.learned + ' of ' + st.total + ' learned</b>' +
          '<p>' + st.mastered + ' mastered. Rate each one honestly.</p>' + CS.bar(100 * st.learned / st.total) +
          '<a class="ui-btn sm ' + (st.read && !learned ? 'primary' : '') + '" style="margin-top:10px" href="#study/' + esc(m.id) + '">' + UI.icon('cards') + (st.learned ? 'Drill again' : 'Start drilling') + '</a></div></div>' +
        '<div class="md-step ' + (st.challenge_passed ? 'done' : '') + '"><span class="dot">' + (st.challenge_passed ? UI.icon('check') : 'III') + '</span><div><b>Challenge: ' + esc(m.challenge.title) + '</b>' +
          '<p>' + (st.challenge ? 'Best score ' + st.challenge + '%' + (st.challenge_passed ? '' : ' · 70% to pass') : 'A boardroom scenario. 70% to pass.') + '</p>' +
          '<a class="ui-btn sm ' + (learned && !st.challenge_passed ? 'primary' : '') + '" href="#challenge/' + esc(m.challenge.id) + '">' + UI.icon('target') + (st.challenge ? 'Try again' : 'Take the challenge') + '</a></div></div>' +
        '</div>' + (m.next ? '<a class="ui-card tight" style="text-decoration:none;color:inherit !important" href="#module/' + esc(m.next.id) + '"><div class="cs-kicker">Next module</div><b>' + esc(m.next.title) + '</b></a>'
          : '<a class="ui-card tight" style="text-decoration:none;color:inherit !important" href="#tracks/' + esc(m.track.id) + '"><div class="cs-kicker">Last module</div><b>Back to ' + esc(m.track.title) + '</b></a>') + '</div>';
    }

    function draw(m) {
      document.title = m.title + ' · ' + UI.config.name;
      view.innerHTML = CS.hero({ photo: m.photo, crumbs: [['tracks', 'Programs'], ['tracks/' + m.track.id, m.track.title], [null, 'Module ' + m.n]],
          eyebrow: m.track.code + ' · Module ' + m.n, title: m.title, lead: m.summary,
          meta: [['clock', m.minutes + ' min'], ['cards', m.cards + ' recall · ' + m.advice + ' advice calls'], ['target', 'Challenge: ' + m.challenge.title]] }) +
        '<div class="ui-wrap"><div class="md-layout"><article>' +
          '<div class="cs-kicker">The briefing</div><div class="md-brief" style="margin-top:12px">' + m.briefing.map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('') + '</div>' +
          '<section class="md-sec"><h2>Sound advice, and traps</h2><div class="cs-dd"><div class="good"><h4>' + UI.icon('check') + 'Do</h4><ul>' +
            m.do.map(function (t) { return '<li>' + UI.icon('check') + '<span>' + esc(t) + '</span></li>'; }).join('') + '</ul></div>' +
            '<div class="bad"><h4>' + UI.icon('x') + 'Avoid</h4><ul>' + m.dont.map(function (t) { return '<li>' + UI.icon('x') + '<span>' + esc(t) + '</span></li>'; }).join('') + '</ul></div></div></section>' +
          (m.cases.length ? '<section class="md-sec"><h2>Case files</h2><div class="md-cases">' + m.cases.map(CS.caseCard).join('') + '</div></section>' : '') +
          '<section class="md-sec"><h2>Sources</h2><ol class="md-sources">' + m.sources.map(function (s) {
            return '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.label) + '</a></li>'; }).join('') + '</ol>' +
            '<p class="small faint" style="margin-top:10px">Summaries are the Institute\'s own. Read the originals for full detail.</p></section>' +
          (m.status && !m.status.read ? '<div class="md-read"><div><b>Finished reading?</b><div class="small muted">Mark the briefing as read, then start the drills.</div></div>' +
            '<button class="ui-btn primary" data-read>' + UI.icon('check') + 'Mark as read and drill</button></div>' : '') +
        '</article><aside>' + steps(m) + '</aside></div></div>';
    }

    view.addEventListener('click', function (e) {
      var b = e.target.closest('[data-read]');
      if (!b) return;
      var toDrill = !!b.closest('.md-read');
      UI.busy(b, UI.api('mark_read', id, CS.today())).then(function (r) {
        UI.toast(r.module_completed ? 'Module complete!' : 'Briefing read · +10 XP', 'ok');
        if (r.module_completed) CS.confetti();
        if (toDrill) UI.go('study', id); else load();
      });
    });
    function load() { return UI.api('get_module', id).then(function (r) { draw(r.module); }); }
    return load();
  });
})();

/* ===== profile.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('profile', { title: 'Your profile', auth: 'user' }, function (view, ctx) {
    var me = ctx.me;
    view.innerHTML = '<div class="ui-wrap ui-narrow"><div class="pf-head"><span class="ui-avatar">' + esc(UI.initials(me.name)) + '</span>' +
      '<div><h1>' + esc(me.name) + '</h1><div class="small" style="color:var(--c-accent-ink)">' + esc(me.rank || '') + ' · ' + (me.xp || 0) + ' XP</div><div class="muted">' + esc(me.email) + (me.joined ? ' · member since ' + esc(UI.fmtDate(me.joined, { month: 'long', year: 'numeric' })) : '') + '</div></div></div>' +
      '<div class="pf-grid"><form class="ui-card ui-stack" data-name><h3>Your details</h3><label class="ui-field"><span>Full name <em>(printed on certificates you earn from now on)</em></span>' +
      '<input type="text" name="name" value="' + esc(me.name) + '" maxlength="60" required></label>' +
      '<label class="ui-field"><span>Job title <em>(optional, shown on the Honour Roll)</em></span><input type="text" name="title" value="' + esc(me.title || '') + '" maxlength="80" placeholder="e.g. VP Finance"></label>' +
      '<label class="ui-check"><input type="checkbox" name="honour"' + (me.honour_roll ? ' checked' : '') + '><span>Show me on the public Honour Roll once I&rsquo;m certified</span></label>' +
      '<button class="ui-btn primary" type="submit">Save</button></form>' +
      '<div class="ui-card ui-stack"><h3>Appearance</h3><p class="muted small">Follow your device, or pick one.</p><div data-theme-box></div>' +
      '<h3 style="margin-top:22px">Password</h3><p class="muted small">We\'ll email you a link to choose a new one.</p>' +
      '<button class="ui-btn" data-reset>' + UI.icon('mail') + 'Email me a reset link</button></div></div>' +
      '<div class="ui-card" style="margin-top:16px"><div class="pf-links">' +
      '<a href="#credentials" data-go="credentials">' + UI.icon('award') + 'Your credentials</a><a href="#cases" data-go="cases">' + UI.icon('book') + 'The Casebook</a>' +
      (me.is_admin ? '<a href="#admin" data-go="admin">' + UI.icon('shield') + 'Admin</a>' : '') +
      '<button data-feedback>' + UI.icon('chat') + 'Submit feedback</button>' +
      '<button data-lk-open="overview">' + UI.icon('lock') + 'Privacy &amp; Terms, and your data</button>' +
      '<button data-signout-here>' + UI.icon('logout') + 'Sign out</button></div></div></div>';
    function themeBox() {
      var t = UI.theme();
      view.querySelector('[data-theme-box]').innerHTML = '<div class="ui-seg">' + [['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']].map(function (o) {
        return '<button type="button" data-theme-pick="' + o[0] + '" class="' + (t === o[0] ? 'on' : '') + '">' + o[1] + '</button>';
      }).join('') + '</div>';
    }
    themeBox();
    view.addEventListener('click', function (e) {
      var t = e.target.closest('[data-theme-pick]');
      if (t) { UI.setTheme(t.getAttribute('data-theme-pick')); themeBox(); UI.renderChrome(); return; }
      if (e.target.closest('[data-reset]')) {
        UI.busy(e.target.closest('[data-reset]'), UI.auth('reset', { email: me.email })).then(function (r) { UI.toast(r.message, 'ok'); });
      }
      if (e.target.closest('[data-signout-here]')) UI.auth('logout');
    });
    view.querySelector('[data-name]').addEventListener('submit', function (e) {
      e.preventDefault();
      var v = UI.formData(e.target);
      UI.busy(e.target.querySelector('[type=submit]'), UI.api('update_profile', v.name, v.title, !!v.honour)).then(function (r) {
        UI.setMe(r.me); ctx.me = r.me; UI.toast('Saved', 'ok');
        view.querySelector('.pf-head h1').textContent = r.me.name;
      });
    });
  });
})();

/* ===== study.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('study', { title: 'Review', nav: 'Review', icon: 'cards', auth: 'user', order: 30 }, function (view, ctx) {
    var scope = ctx.args[0] || 'review';
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:360px;max-width:760px;margin:0 auto"></div></div>';
    var completed = [];
    return UI.api('get_study', scope, CS.today()).then(function (d) {
      var back = scope === 'review' ? '<a class="ui-btn ghost sm" href="#home">' + UI.icon('back') + 'Dashboard</a>' : '<a class="ui-btn ghost sm" href="#module/' + esc(scope) + '">' + UI.icon('back') + 'Back to the module</a>';
      if (!d.items.length) {
        view.innerHTML = '<div class="ui-wrap"><div class="st-head"><div><div class="cs-kicker">' + esc(d.subtitle) + '</div><h1>' + esc(d.title) + '</h1></div>' + back + '</div>' +
          '<div class="ui-empty ui-narrow">' + UI.icon('check') + '<h3>Nothing due right now</h3><p>Every drill you\'ve learned is scheduled for later. Start a new module to add more.</p>' +
          '<a class="ui-btn primary" href="#tracks" data-go="tracks">Browse programs</a></div></div>';
        return;
      }
      view.innerHTML = '<div class="ui-wrap"><div class="st-head"><div><div class="cs-kicker">' + esc(d.subtitle) + '</div><h1>' + esc(d.title) + '</h1></div>' + back + '</div>' +
        '<div data-drill></div><div class="st-legend">Spaced repetition: each “Got it” moves a drill up a box. Next review after ' +
        d.boxes.slice(1).map(function (n) { return n + 'd'; }).join(' · ') + '.</div></div>';
      var el = view.querySelector('[data-drill]');
      CS.drill(el, d.items, {
        rate: function (it, knew) {
          return UI.apiQuiet('rate_item', it.id, knew, CS.today()).then(function (r) {
            if (r.module_completed) { completed.push(r.module_title); UI.toast('Module complete: ' + r.module_title, 'ok'); CS.confetti(); }
          });
        },
        done: function (s) {
          var n = s.got + s.missed, pct = n ? Math.round(100 * s.got / n) : 0;
          view.querySelector('.st-legend').hidden = true;
          el.innerHTML = '<div class="ui-card st-done"><div class="cs-kicker">Session complete</div><div class="score">' + pct + '%</div><div class="muted">recalled on the first try</div>' +
            '<div class="split"><div><b style="color:var(--c-good)">' + s.got + '</b><span>Got it</span></div><div><b style="color:var(--c-bad)">' + s.missed + '</b><span>Still learning</span></div>' +
            '<div><b>+' + (s.got * 3 + s.missed) + '</b><span>XP</span></div></div>' +
            (completed.length ? '<p class="ui-note">' + UI.icon('award') + ' Module complete: ' + esc(completed.join(', ')) + '</p>' : '') +
            '<p class="muted small">' + (s.missed ? 'The ones you missed come back today. Revisit them before you sleep.' : 'Excellent. These drills will return when your memory needs them.') + '</p>' +
            '<div class="ui-row" style="justify-content:center;margin-top:14px">' +
            (scope === 'review' ? '<a class="ui-btn primary" href="#home">Back to the dashboard</a>'
              : '<a class="ui-btn" href="#study/' + esc(scope) + '" data-again>' + UI.icon('refresh') + 'Drill again</a><a class="ui-btn primary" href="#module/' + esc(scope) + '">' + UI.icon('target') + 'Back to the module</a>') +
            '</div></div>';
          if (pct >= 90 && n >= 5) CS.confetti();
        }
      });
      view.addEventListener('click', function (e) { if (e.target.closest('[data-again]')) { e.preventDefault(); UI.refresh(); } });
    });
  });
})();

/* ===== tracks.html ===== */
(function () {
  var esc = UI.esc;

  function catalog(view) {
    return UI.api('get_catalog').then(function (d) {
      view.innerHTML = CS.hero({ photo: 'ph-board-table', eyebrow: 'The Institute\'s programs', title: 'Programs of study',
        lead: 'Executive Foundations is the shared core. Each role program builds the judgement a specific seat demands. Every program ends in an examination and a verifiable credential.',
        meta: [['columns', d.tracks.length + ' programs'], ['cards', d.totals.items + ' drills'], ['target', d.totals.challenges + ' challenges'], ['book', d.cases + ' case files']] }) +
        '<div class="ui-wrap"><div class="tr-grid">' + d.tracks.map(CS.trackCard).join('') + '</div>' +
        '<div class="tr-fellow"><div>' + UI.seal(84) + '</div><div><div class="cs-kicker" style="color:#c9a66b">The Fellowship</div><h3>Fellow of the C-Suite Coach Institute</h3>' +
        '<p>Hold Executive Foundations and any two role certificates and you are admitted as a Fellow (FCSCI), with its own certificate.</p></div>' +
        (d.signed_in ? '<a class="ui-btn gold" href="#credentials" data-go="credentials">Your progress</a>' : '<a class="ui-btn gold" href="#auth/signup" data-go="auth/signup">Enrol, free</a>') + '</div></div>';
    });
  }

  function track(view, ctx, id) {
    return UI.api('get_track', id).then(function (r) {
      var t = r.track, s = t.status, me = ctx.me;
      document.title = t.title + ' · ' + UI.config.name;
      var action = !me ? '<a class="ui-btn primary lg" href="#auth/signup" data-go="auth/signup">Enrol to begin</a>'
        : s.certified ? '<a class="ui-btn primary lg" href="#certificate/' + esc(s.credential.code) + '">' + UI.icon('award') + 'View your certificate</a>'
        : s.exam_ready ? '<a class="ui-btn primary lg" href="#exam/' + esc(t.id) + '">' + UI.icon('award') + 'Sit the final examination</a>'
        : '<a class="ui-btn primary lg" href="#module/' + esc((t.modules.filter(function (m) { return !m.status.complete; })[0] || t.modules[0]).id) + '">' + UI.icon('arrow') + (s.started ? 'Continue' : 'Begin module 1') + '</a>';
      view.innerHTML = CS.hero({ photo: t.photo, crumbs: [['tracks', 'Programs'], [null, t.code]], eyebrow: t.role, title: t.title, lead: t.blurb,
          meta: [['briefcase', t.modules.length + ' modules'], ['cards', t.items + ' drills'], ['target', t.challenges + ' challenges'], ['clock', '~' + Math.round(t.minutes / 6) / 10 + ' hours of study'], ['award', t.credential]],
          actions: action }) +
        '<div class="ui-wrap"><div class="tr-layout"><div class="tr-mods">' +
        t.modules.map(function (m) {
          var st = m.status;
          return '<a class="tr-mod" href="#module/' + esc(m.id) + '"><div class="num">' + m.n + '</div><div><h3>' + esc(m.title) + '</h3><p>' + esc(m.summary) + '</p>' +
            '<div class="meta"><span class="ui-badge">' + UI.icon('clock') + m.minutes + ' min</span><span class="ui-badge">' + UI.icon('cards') + m.items + ' drills</span>' +
            '<span class="ui-badge">' + UI.icon('target') + esc(m.challenge.title) + '</span>' +
            (st ? (st.complete ? '<span class="ui-badge good">' + UI.icon('check') + 'Complete</span>' : st.pct ? '<span class="ui-badge brand">' + st.pct + '% · ' + st.steps + '/3 steps</span>' : '') : '') +
            '</div></div>' + (st ? CS.ring(st.pct, 54) : '<span class="ui-badge">' + UI.icon('lock') + 'Members</span>') + '</a>';
        }).join('') +
        '<div class="tr-mod capstone"><div class="num">' + UI.icon('award') + '</div><div><h3>Final examination</h3><p>A recall round of 12 drills from the whole program and the capstone case, “' + esc(t.capstone.title) + '”. ' +
          'Pass both to be issued the ' + esc(t.credential) + '.</p><div class="meta"><span class="ui-badge">80% recall</span><span class="ui-badge">70% capstone</span><span class="ui-badge">Honour code</span></div></div>' +
          (s ? (s.certified ? '<span class="ui-badge gold">Certified</span>' : s.exam_ready ? '<a class="ui-btn gold sm" href="#exam/' + esc(t.id) + '">Begin</a>' : '<span class="ui-badge">' + UI.icon('lock') + s.modules_done + '/' + s.modules + '</span>') : '') + '</div>' +
        '</div><aside class="tr-side">' +
          (s ? '<div class="ui-card"><div class="ui-row">' + CS.ring(s.pct, 76) + '<div><div class="cs-kicker">Your progress</div><b>' + s.modules_done + ' of ' + s.modules + ' modules</b>' +
            '<div class="small muted">' + (s.certified ? 'Certified ' + esc(UI.fmtDate(s.credential.issued)) : s.exam_ready ? 'Examination open' : 'Complete every module to unlock the examination') + '</div></div></div></div>' : '') +
          '<div class="ui-card"><div class="cs-kicker">What you\'ll be able to do</div><ul style="margin-top:10px">' + t.outcomes.map(function (o) { return '<li>' + esc(o) + '</li>'; }).join('') + '</ul></div>' +
          '<div class="ui-card"><div class="cs-kicker">Each module</div><ul style="margin-top:10px"><li>A research briefing, with good advice and traps</li><li>Real case files from the Casebook</li>' +
            '<li>Recall drills and advice calls on spaced repetition</li><li>A boardroom challenge scored on a rubric (70% to pass)</li></ul></div>' +
        '</aside></div></div>';
    });
  }

  UI.page('tracks', { title: 'Programs', nav: 'Programs', icon: 'columns', order: 20 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:240px"></div></div>';
    return ctx.args[0] ? track(view, ctx, ctx.args[0]) : catalog(view);
  });
})();

/* ===== verify.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('verify', { title: 'Verify a credential' }, function (view, ctx) {
    var code = ctx.args[0] || '';
    view.innerHTML = CS.hero({ photo: 'ph-signing', eyebrow: 'The Institute\'s register', title: 'Verify a credential',
        lead: 'Enter a credential ID to confirm it was issued by the C-Suite Coach Institute and is still valid.' }) +
      '<div class="ui-wrap"><div class="vf-box"><form class="ui-card" data-verify><div class="vf-form"><input type="text" name="code" value="' + esc(code) + '" placeholder="CSC-XXX-2026-XXXXXX" aria-label="Credential ID" required>' +
      '<button class="ui-btn primary" type="submit">' + UI.icon('shield') + 'Verify</button></div><div data-res></div></form></div>' +
      '<div style="margin-top:40px"><div class="cs-kicker">Honour Roll</div><h2 style="margin:6px 0 16px">Recently certified</h2><div class="vf-roll" data-roll><div class="ui-skel"></div></div></div></div>';
    var res = view.querySelector('[data-res]');
    function check(c) {
      if (!c) { res.innerHTML = ''; return Promise.resolve(); }
      return UI.api('get_credential', c).then(function (r) {
        if (!r.found) {
          res.innerHTML = '<div class="vf-res bad">' + UI.icon('alert') + '<div><h3 style="margin:0">Not found</h3><p class="muted" style="margin:4px 0 0">No credential with the ID <b>' + esc(c.toUpperCase()) + '</b> is on the register. Check for typos.</p></div></div>';
          return;
        }
        var valid = r.status === 'valid';
        res.innerHTML = '<div class="vf-res ' + (valid ? 'ok' : 'bad') + '">' + UI.icon(valid ? 'shield' : 'alert') + '<div><h3 style="margin:0">' + (valid ? 'Verified: a valid credential' : 'Revoked: no longer valid') + '</h3>' +
          '<dl><dt>Holder</dt><dd>' + esc(r.holder) + '</dd><dt>Credential</dt><dd>' + esc(r.credential) + '</dd><dt>Issued</dt><dd>' + esc(UI.fmtDate(r.issued, { day: 'numeric', month: 'long', year: 'numeric' })) + '</dd>' +
          '<dt>ID</dt><dd>' + esc(r.code) + (r.demo ? ' <span class="ui-badge">Sample record</span>' : '') + '</dd></dl>' +
          '<a class="ui-btn sm" style="margin-top:12px" href="#certificate/' + esc(r.code) + '">' + UI.icon('award') + 'View the certificate</a></div></div>';
      });
    }
    view.addEventListener('submit', function (e) {
      e.preventDefault();
      var c = UI.formData(e.target).code.trim();
      if (!c) return;
      history.replaceState(null, '', '#verify/' + encodeURIComponent(c.toUpperCase()));
      UI.busy(e.target.querySelector('[type=submit]'), check(c));
    });
    UI.apiQuiet('get_honour_roll').then(function (h) {
      view.querySelector('[data-roll]').innerHTML = h.items.length ? h.items.map(function (x) {
        return '<a href="#verify/' + esc(x.code) + '"><span class="ui-avatar">' + esc(UI.initials(x.name)) + '</span><div><b>' + esc(x.name) + '</b><small>' + esc(x.title) + '</small><small style="color:var(--c-accent-ink)">' + esc(x.credential) + '</small></div></a>';
      }).join('') : '<p class="muted">The first graduates will appear here.</p>';
    });
    return check(code);
  });
})();
