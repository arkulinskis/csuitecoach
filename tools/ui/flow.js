/* The main user journeys, run inside the real app (Anvil App Server) by tools/ui_test.py through tools/live/drive.mjs.
   Resolves to {ok, log}. Keep log lines ASCII (the Windows console). Ported from the JavaScript version's
   tools/preview/tests/flowtest.html: landing, sign-up with the consent tick, dashboard, a module (read, drill all 10,
   challenge, module complete), review, programs, the locked examination, the Casebook filter, credentials, public
   verification + certificate, profile (job title + Honour Roll), feedback link, admin kept out, sign out, sign in. */
(async function () {
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (el) => !!el && el.getClientRects().length > 0;
  const text = () => document.body.innerText;
  const byText = (sel, t) => $$(sel).find((e) => vis(e) && e.textContent.trim().replace(/\s+/g, ' ') === t);
  async function click(sel, t) {
    const el = await until(() => (t ? byText(sel, t) : $$(sel).find(vis)), sel + (t ? ' "' + t + '"' : ''));
    el.scrollIntoView({ block: 'center' });
    el.click();
    return el;
  }
  function type(input, value) {
    input.focus();
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;  // the old page stays until the router runs
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), what || hash, 40000);
    await sleep(300);
  }
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };

  try {
    // ---- landing (visitors)
    await page('#landing', () => $('.lp-hero h1') && $$('.cs-pcard').length >= 7, 'landing');
    ok($('.lp-hero a[href="#auth/signup"]'), 'landing: hero with an Enrol link');
    ok($('.lp-hero [data-cert] .holder') && $('.lp-hero [data-cert] .holder').textContent === 'Margaret Okafor', 'landing: the sample certificate is drawn');
    ok($$('.cs-pcard').length === 7 && $$('.lp .cs-case').length === 3, 'landing: 7 programs and 3 cases from the server');
    ok($('.ytf-cover') && $('[data-lk-open]'), 'landing: Watch section and Privacy & Terms link');
    ok($$('.ui-nav a').map((a) => a.getAttribute('href')).join(',') === '#tracks,#cases,#verify', 'header: visitors get Programs, Casebook, Verify');

    // ---- members-only page sends visitors to sign in, then back
    await page('#credentials', () => true);
    await until(() => window.UI_READY && $$('.au-card input').length >= 2, 'redirected to sign in');
    ok(true, 'a members-only page asks visitors to sign in');

    // ---- sign up (needs the consent tick)
    await click('.au-card .ui-seg button', 'Create account');
    await until(() => $$('.au-card input').filter(vis).length >= 3, 'sign-up form');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(inputs[0], 'Test Person'); type(inputs[1], 'flow' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    await click('.anvil-role-btn-block button', 'Create account');
    await sleep(1200);
    ok(!$('.anvil-role-avatar button') || !vis($('.anvil-role-avatar button')), 'no account without the consent tick');
    const tick = $('.au-card input[type=checkbox]');
    ok(tick, 'the consent tick box is there');
    if (!tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
    await until(() => location.hash === '#credentials' && window.UI_READY && $('.anvil-role-cr-path'), 'back on the page they wanted', 40000);
    ok(/No credentials yet/.test(text()), 'sign-up: signed in, sent on to Credentials (empty state + Fellowship path)');
    ok($('.anvil-role-avatar button') && /TP/.test($('.anvil-role-avatar button').textContent), 'header: account button with initials');

    // ---- dashboard
    await page('#home', () => $$('.hm-track').length >= 7, 'home');
    ok(/Test/.test($('.hm-top h1').textContent), 'dashboard greets the new member by first name');
    ok($$('.hm-track').length === 7, 'dashboard lists the 7 programs');
    ok($('.hm-next a[href="#module/core-decide"]'), 'dashboard suggests the first module');
    ok($$('.ui-nav a').length === 5 && $$('.anvil-role-hm-week .wd').length === 7, 'members get 5 header links; the week strip has 7 days');

    // ---- module: read the briefing, then drill
    await page('#module/core-decide', () => $$('.cs-para').length && $$('.cs-src').length >= 2, 'module');
    ok($$('.md .cs-case').length >= 1 && $$('.cs-dd-li').length >= 4, 'module shows the briefing, Do / Avoid, case files and sources');
    await click('.md-read .anvil-role-btn button', 'Mark as read and drill');
    await until(() => location.hash === '#study/core-decide' && window.UI_READY && vis($('.cs-card')), 'drill opens', 30000);
    ok(true, 'marking the briefing read opens the drill');
    let rated = 0;
    for (let k = 0; k < 40 && !vis($('.st-done')); k++) {
      const rv = $('.cs-card .anvil-role-btn-lg button');
      if (vis(rv)) { rv.click(); await until(() => vis($('.anvil-role-cs-rate-yes button')), 'revealed'); }
      const yes = $('.anvil-role-cs-rate-yes button');
      if (!vis(yes)) break;
      const before = $('.cs-drill .count').textContent;
      yes.click(); rated++;
      await until(() => vis($('.st-done')) || ($('.cs-drill .count').textContent !== before && vis($('.cs-card .anvil-role-btn-lg button'))), 'next card', 15000);
    }
    await until(() => vis($('.st-done')), 'session summary');
    ok(rated === 10, 'drilled all 10 items of the module (' + rated + ')');
    ok(/100%/.test($('.st-done').textContent), 'session summary shows the score');

    // ---- keyboard: Space reveals, 2 rates (a second module, one card)
    await page('#study/core-direction', () => vis($('.cs-card')), 'second drill');
    document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
    await until(() => vis($('.anvil-role-cs-rate-yes button')), 'space reveals');
    const c1 = $('.cs-drill .count').textContent;
    document.dispatchEvent(new KeyboardEvent('keydown', { key: '2', bubbles: true }));
    await until(() => $('.cs-drill .count').textContent !== c1, 'key 2 rates');
    ok(true, 'drill keys: Space reveals, 2 says Got it');

    // ---- challenge: write, compare, tick the rubric, pass, module complete
    await page('#challenge/ch-core-decide', () => vis($('.ch-form textarea')), 'challenge');
    ok(/The Two Doors/.test(text()), 'challenge page shows the scenario');
    type($('.ch-form textarea'), 'Delegate the pricing test this week, run diligence on the acquisition with the board, and delay the commission change to next quarter.');
    await click('.ch-form .anvil-role-btn button', 'Submit and compare');
    await until(() => vis($('.ch-model')) && $$('.cs-rub input').length >= 4, 'model answer');
    ok(/model answer/.test($('.ch-model').textContent), 'submitting shows the model answer and the rubric');
    $$('.cs-rub input').forEach((b) => b.click());
    ok($$('.cs-rub.on').length === $$('.cs-rub').length, 'ticked criteria turn green');
    await click('.ch-model .anvil-role-btn button', 'Record my score');
    await until(() => vis($('.ch-result')), 'challenge result', 30000);
    ok($('.ch-result.pass') && /100%/.test($('.ch-result').textContent), 'challenge passed at 100%');
    ok(/Module complete/.test($('.ch-result').textContent), 'briefing + drills + challenge completes the module');
    ok($$('.cs-rub input').every((b) => b.disabled), 'the rubric is locked once the score is recorded');
    await page('#home', () => $('.hm-next a[href]'), 'home again');
    ok($('.hm-next a[href="#module/core-direction"]'), 'dashboard moves on to module 2');

    // ---- review, programs, examination, casebook
    await page('#study/review', () => vis($('.ui-empty')) || vis($('.cs-card')), 'review');
    ok(/Nothing due/.test(text()), 'nothing due right after learning');
    await page('#tracks', () => $$('.cs-pcard').length >= 7, 'programs');
    ok($$('.cs-pcard').length === 7 && $('.tr-fellow'), 'programs catalogue shows 7 programs and the Fellowship');
    await page('#tracks/core', () => $$('.tr-mod').length >= 7, 'one program');
    ok($$('.tr-mod').length === 7 && /Complete/.test($('.tr-mods').textContent), 'program page lists 6 modules + the examination, with progress');
    await page('#exam/core', () => $$('.ex-paper').some(vis), 'examination');
    ok(/complete every module first/i.test(text()) && $$('.cs-mlink').filter(vis).length === 5, 'examination is locked until every module is complete (5 to go)');
    await page('#cases', () => $$('.cs-case').length >= 20, 'casebook');
    const nCases = $$('.cs-case').length;
    await click('.cb-filter .anvil-role-seg button', 'Cautionary');
    await until(() => $$('.cs-case').length < nCases, 'filtered');
    ok($$('.cs-case.cautionary').length === $$('.cs-case').length, 'the Casebook lists cases and filters them');
    await page('#cases/svb', () => $$('.cs-para').length && $('.cb-lesson'), 'one case');
    ok($$('.cs-src').length >= 1 && $$('.cb-nav a').some(vis), 'a case file: story, lesson, sources, previous / next');

    // ---- public verification + certificate of a demo credential
    await page('#verify/CSC-CFO-2026-T4WX9N', () => vis($('.vf-res')), 'verify');
    ok($('.vf-res.ok') && /Margaret Okafor/.test($('.vf-res').textContent), 'a demo credential verifies');
    await page('#certificate/CSC-CFO-2026-T4WX9N', () => $('[data-cert] .holder'), 'certificate');
    ok($('[data-cert] .holder').textContent === 'Margaret Okafor' && /Valid credential/.test(text()), 'certificate page renders the holder and says it is valid');
    ok(!vis($('.ce-top a[href*="linkedin"]')), 'Add to LinkedIn is only for the holder');
    await page('#certificate/CSC-FEL-2026-D9RV3C', () => $('[data-cert].fellow'), 'fellowship certificate');
    ok(true, 'the Fellowship certificate is the navy version');
    await page('#verify/NOPE-123', () => vis($('.vf-res')), 'verify unknown');
    ok($('.vf-res.bad') && /Not found/.test($('.vf-res').textContent), 'an unknown code is reported as not found');
    type($('.vf-form input'), 'csc-cfo-2026-t4wx9n');
    await click('.vf-form .anvil-role-btn button', 'Verify');
    await until(() => $('.vf-res.ok'), 'lookup');
    ok(location.hash === '#verify/CSC-CFO-2026-T4WX9N', 'a lookup puts the code in the address (shareable)');

    // ---- profile: job title + Honour Roll opt-in
    await page('#profile', () => $('.pf-grid'), 'profile');
    const pfInputs = $$('.pf-grid input').filter((i) => vis(i) && i.type !== 'checkbox');
    type(pfInputs[1], 'Director of Strategy');
    const hb = $('.pf-grid input[type=checkbox]');
    if (!hb.checked) hb.click();
    await click('.pf-grid .anvil-role-btn-primary button', 'Save');
    await sleep(2500);
    await page('#credentials', () => $('.anvil-role-cs-check input'), 'credentials again');
    ok($('.anvil-role-cs-check input').checked, 'profile saves the Honour Roll choice (credentials page agrees)');
    await page('#profile', () => $('.pf-grid'), 'profile again');
    ok($$('.pf-grid input').filter((i) => vis(i) && i.type !== 'checkbox')[1].value === 'Director of Strategy', 'profile saves the job title');

    // ---- feedback: one footer link, and it goes to Prepsto
    const pl = $$('.ui-footer [data-prepsto-open]');
    ok(pl.length === 1 && pl[0].textContent.trim() === 'Submit feedback' && /prepsto\.com\/#f\//.test(pl[0].href), 'the footer has one Submit feedback link to Prepsto');
    ok(/arkvital\.com/.test($('.ui-footer').textContent) && /addanapp\.com/.test($('.ui-footer').textContent), 'footer: Contact developer + Parent company');

    // ---- members can't open admin
    await page('#admin', () => true);
    await sleep(800);
    ok(!$('.ad-stats'), 'non-admins are kept out of #admin');

    // ---- light / dark switch in the account menu
    await click('.anvil-role-avatar button');
    await click('.ui-menu .ui-seg button', 'Dark');
    ok(document.documentElement.classList.contains('ui-dark'), 'menu: Dark switches the theme');
    await click('.ui-menu .ui-seg button', 'Auto');

    // ---- sign out
    await click('.ui-menu button', 'Sign out');
    await until(() => location.hash === '#landing' && window.UI_READY && $('.ui-header .ui-btn.primary'), 'signed out');
    ok(true, 'sign out: back to the landing page as a visitor');

    // ---- sign in with a wrong password
    await page('#auth', () => $$('.au-card input').filter(vis).length >= 2, 'sign in');
    const li = $$('.au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(li[0], 'nobody@example.com'); type(li[1], 'wrong-password-123');
    await click('.anvil-role-btn-block button', 'Sign in');
    await until(() => vis($('.anvil-role-msg-error')), 'error message');
    ok(true, 'a wrong password shows an error');

    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
