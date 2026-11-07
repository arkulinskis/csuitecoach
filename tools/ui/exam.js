/* The whole certification path in the real app: a fresh member completes every Executive Foundations module (briefing,
   drills, challenge), sits the final examination (honour code, 12-item recall round, capstone with the rubric), is
   issued a credential, opens the certificate and verifies the code publicly; the examination then says "Already
   certified". Run by tools/ui_test.py. Resolves to {ok, log}. */
(async function () {
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(120); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (el) => !!el && el.getClientRects().length > 0;
  const byText = (sel, t) => $$(sel).find((e) => vis(e) && e.textContent.trim().replace(/\s+/g, ' ') === t);
  async function click(sel, t) {
    const el = await until(() => (t ? byText(sel, t) : $$(sel).find(vis)), sel + (t ? ' "' + t + '"' : ''));
    el.scrollIntoView({ block: 'center' }); el.click(); return el;
  }
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), what || hash, 40000);
    await sleep(250);
  }
  const ok = (c, m) => { if (!c) throw new Error('FAILED: ' + m); say('ok   ' + m); };
  let seen = [];
  async function drillAll(max) {
    let n = 0; seen = [];
    for (let k = 0; k < (max || 40) && !vis($('.st-done')); k++) {
      const rv = $$('.cs-card .anvil-role-btn-lg button').find(vis);
      if (!rv) break;
      const before = $('.cs-drill .count').textContent;
      rv.click();
      await until(() => vis($('.anvil-role-cs-rate-yes button')), 'revealed');
      seen.push(before); $('.anvil-role-cs-rate-yes button').click(); n++;
      await until(() => vis($('.st-done')) || !$$('.cs-card').some(vis) || ($('.cs-drill .count').textContent !== before && $$('.cs-card .anvil-role-btn-lg button').some(vis)), 'next card', 15000);
    }
    return n;
  }
  try {
    // a fresh member
    location.hash = '#auth/signup'; window.UI_READY = false;
    await until(() => window.UI_READY && $$('.au-card input').filter(vis).length >= 3, 'sign-up');
    const i = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(i[0], 'Exam Candidate'); type(i[1], 'exam' + Date.now() + '@example.com'); type(i[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]'); if (!tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
    await until(() => location.hash === '#home' && window.UI_READY, 'signed in', 40000);

    await page('#tracks/core', () => $$('.tr-mod[href^="#module/"]').length >= 6, 'Executive Foundations');
    const mods = $$('.tr-mod[href^="#module/"]').map((a) => a.getAttribute('href').split('/')[1]);
    ok(mods.length === 6, 'Executive Foundations has 6 modules');
    for (const m of mods) {
      await page('#module/' + m, () => vis($('.md-steps .anvil-role-btn button')), 'module ' + m);
      await click('.md-steps .anvil-role-btn button', 'Mark as read');
      await until(() => $$('.md-step.done').length >= 1 && window.UI_READY, 'briefing read');
      await page('#study/' + m, () => $$('.cs-card').some(vis), 'drill ' + m);
      const n = await drillAll();
      await until(() => vis($('.st-done')), 'session done');
      await page('#challenge/ch-' + m, () => vis($('.ch-form textarea')), 'challenge ' + m);
      type($('.ch-form textarea'), 'I would align the board first, name one accountable owner, act within the week, communicate openly and review the result.');
      await click('.ch-form .anvil-role-btn button', 'Submit and compare');
      await until(() => $$('.cs-rub input').length >= 4, 'rubric');
      $$('.cs-rub input').forEach((b) => b.click());
      await click('.ch-model .anvil-role-btn button', 'Record my score');
      await until(() => vis($('.ch-result')), 'result');
      ok(/Module complete/.test($('.ch-result').textContent), m + ': read, ' + n + ' drills, challenge passed, module complete ' + seen.join('|'));
    }

    // the examination
    await page('#exam/core', () => $$('.ex-paper').some(vis), 'examination');
    ok(/two parts, one sitting/i.test(document.body.innerText), 'the examination opens once every module is complete');
    const begin = byText('.anvil-role-btn button', 'Begin the examination');
    ok(begin && begin.disabled, 'Begin waits for the honour code');
    $('.ex-honour input').click();
    await until(() => !begin.disabled, 'honour code ticked');
    begin.click();
    await until(() => $$('.cs-card').some(vis), 'recall round');
    ok(/Part I of II/.test($('.cs-hero').textContent), 'Part I: the recall round');
    const recall = await drillAll(30);
    ok(recall === 12, 'recall round: 12 items, rated once each, none come back (' + recall + ') ' + seen.join('|'));
    await until(() => $$('.ex-paper textarea').some(vis), 'capstone');
    ok(/Part II of II/.test($('.cs-hero').textContent), 'Part II: the capstone case');
    type($$('.ex-paper textarea').find(vis), 'Stabilise first: brief the chair today, appoint one owner, protect liquidity, tell staff and customers the facts we know, set a review in two weeks and report to the board.');
    await click('.ex-paper .anvil-role-btn button', 'Submit answer and see the criteria');
    await until(() => $$('.ex-paper .cs-rub input').length >= 4, 'criteria');
    $$('.ex-paper .cs-rub input').forEach((b) => b.click());
    await click('.ex-paper .anvil-role-btn button', 'Submit to the Board of Examiners');
    await until(() => $$('.ex-scores').some(vis), 'result', 40000);
    ok(/issued your credential/.test(document.body.innerText), 'passed: the Board of Examiners issues the credential');
    await until(() => $('.ex-cert [data-cert] .holder'), 'new certificate');
    ok($('.ex-cert [data-cert] .holder').textContent === 'Exam Candidate', 'the new certificate carries the member\'s name');
    const link = $$('.ex-links a').find((a) => /certificate/.test(a.getAttribute('href') || ''));
    const code = decodeURIComponent(link.getAttribute('href').split('/')[1]);
    ok(/^CSC-/.test(code), 'credential code issued: ' + code);

    await page('#certificate/' + code, () => $('[data-cert] .holder'), 'certificate');
    ok(/Valid credential/.test(document.body.innerText) && vis($('.ce-top a[href*="linkedin"]')), 'the holder sees the certificate, valid, with Add to LinkedIn');
    await page('#verify/' + code, () => vis($('.vf-res')), 'verify');
    ok($('.vf-res.ok') && /Exam Candidate/.test($('.vf-res').textContent), 'the code verifies on the public register');
    await page('#credentials', () => $$('.cr-item').length >= 1, 'credentials');
    ok($$('.cr-item [data-cert]').length >= 1, 'credentials page shows the certificate thumbnail');
    await page('#exam/core', () => $$('.ex-paper').some(vis), 'exam again');
    ok(/Already certified/.test(document.body.innerText), 'the examination now says Already certified');
    say('PASSED');
    return { ok: true, log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log };
  }
})();
