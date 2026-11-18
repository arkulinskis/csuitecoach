/* The team plan, end to end (Teams.py, Pages/Team, Pages/Join): a manager signs up, creates a team, invites two
   leaders (links copied, no email), a visitor opens one personal link, creates an account, comes back to the invite and
   joins, sees "Assigned by" on the dashboard; the manager then sees them as a Member with progress, changes nothing
   else, cancels the other invite and downloads nothing. Resolves to {ok, log}. ASCII log lines. */
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
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), what || hash, 40000);
    await sleep(300);
  }
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };
  const pw = () => 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7';
  async function signUp(name, email, password) {
    await until(() => window.UI_READY && $$('.au-card input').filter(vis).length >= 3, 'sign-up form');
    const f = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(f[0], name); type(f[1], email); type(f[2], password);
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
  }
  async function signOut() {
    await click('.anvil-role-avatar button');
    await click('.ui-menu button', 'Sign out');
    await until(() => location.hash === '#landing' && window.UI_READY, 'signed out');
  }
  const copied = [];
  try { navigator.clipboard.writeText = (t) => { copied.push(t); return Promise.resolve(); }; } catch (e) {}

  try {
    // ---- a visitor finds the team plan
    await page('#landing', () => $('.lp-teams'), 'landing');
    ok($('.lp-teams a[href="#team"]'), 'landing: "For leadership teams" links to #team');
    ok($$('.ui-nav a').some((a) => a.getAttribute('href') === '#team'), 'header: visitors see For teams');
    await page('#team', () => $('.tm-start'), 'team page (visitor)');
    ok(/Enrol your leadership team/.test(text()) && /Create your account/.test(text()), 'team page: visitors get the pitch and a sign-up button');
    await click('.tm-start a', 'Create your account');
    const boss = 'boss' + Date.now() + '@example.com', bossPw = pw();
    await signUp('Bea Manager', boss, bossPw);
    await until(() => location.hash === '#team' && window.UI_READY && vis($('.tm-start')), 'back on #team after sign-up', 40000);
    ok(true, 'sign-up from the team page comes back to #team');

    // ---- create the team and invite
    type($$('.tm-start input').find(vis), 'Northwind leaders');
    await click('button', 'Create the team');
    await until(() => vis($('.tm-stats')) && /Northwind leaders/.test($('.tm h1') ? $('.tm h1').textContent : ''), 'team created');
    ok(/No one yet/.test(text()), 'team created: stats, empty People list');
    ok($$('.tm-pick input:checked').length === 1, 'invite form: Executive Foundations ticked by default');
    const box = $$('.tm textarea').find(vis);
    type(box, 'Lea Lead, lea' + Date.now() + '@example.com\nRay Reed, ray' + Date.now() + '@example.com\nnot an email');
    const picks = $$('.tm-pick input').filter(vis);
    if (!picks[1].checked) picks[1].click();
    const emailBox = $$('.tm .anvil-role-cs-check input').filter(vis).find((i) => /Email each person/.test(i.parentElement.textContent));
    if (emailBox.checked) emailBox.click();
    await click('button', 'Create invites');
    await until(() => $$('.tm-row').length === 2, 'two invites listed');
    ok(/2 invites created/.test(text()) && /not an email address/.test(text()), 'invites: 2 created, the bad line reported');
    ok($$('.tm-row .anvil-role-badge').filter((b) => /Invite sent/.test(b.textContent)).length === 2, 'People: both show Invite sent');
    ok($$('.tm-row')[0].querySelectorAll('.tm-track').length === 2, 'People: two assigned programs per person');
    await click('.tm-row button', 'Copy invite link');
    await until(() => copied.length, 'link copied');
    const link = copied[0];
    ok(/#join\/[\w-]{10,}$/.test(link), 'Copy invite link gives a personal #join link');
    const token = link.split('#join/')[1];
    await signOut();

    // ---- the invited leader opens the link, signs up, joins
    await page('#join/' + token, () => $('.tm-join'), 'invite page');
    ok(/Join Northwind leaders/.test(text()) && /Bea Manager/.test(text()), 'invite: team and manager named');
    ok($$('.tm-join-track').length === 2 && /never|Not your written answers/i.test($('.tm-privacy').textContent), 'invite: programs + what the manager sees');
    await click('.tm-join button', 'Create your account');
    await signUp('Lea Lead', 'leader' + Date.now() + '@example.com', pw());
    await until(() => location.hash === '#join/' + token && window.UI_READY && vis(byText('.tm-join button', 'Join the team')), 'back on the invite', 40000);
    ok(true, 'after sign-up the invite opens again');
    await click('.tm-join button', 'Join the team');
    await until(() => location.hash === '#home' && window.UI_READY && vis($('.hm-team')), 'dashboard with team panel', 40000);
    ok(/Assigned by Northwind leaders/.test($('.hm-team').textContent) && $$('.hm-team .hm-track').length === 2, 'dashboard: Assigned by the team, 2 programs');
    await page('#team', () => vis($('.tm-panel')), 'member team view');
    ok(/You're a member of Northwind leaders/.test(text()), 'team page: the member sees their team and can leave');
    await page('#join/' + token, () => $('.tm-join'), 'invite again');
    ok(/already in this team/.test(text()), 'the used invite says you are already in');
    await signOut();

    // ---- the manager sees the member
    await page('#auth', () => $$('.au-card input').filter(vis).length >= 2, 'sign in');
    const li = $$('.au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(li[0], boss); type(li[1], bossPw);
    await click('.anvil-role-btn-block button', 'Sign in');
    await until(() => location.hash === '#home' && window.UI_READY, 'manager signed in', 40000);
    await page('#team', () => $$('.tm-row').length === 2, 'manager team view');
    const member = $$('.tm-row').find((r) => /Member/.test(r.textContent));
    ok(member && /Lea Lead/.test(member.textContent) && /hasn't studied yet/.test(member.textContent), 'manager: Lea is a Member, not studied yet');
    ok(/^1$/.test($('.tm-stats .anvil-role-stat-num').textContent.trim()), 'stats: 1 member');
    const ray = $$('.tm-row').find((r) => /Ray Reed/.test(r.textContent));
    const cancel = Array.from(ray.querySelectorAll('button')).find((b) => /Cancel invite/.test(b.textContent));
    cancel.click();
    const dlg = () => $$('.anvil-modal-content, .modal-content').filter(vis).pop();
    const yes = await until(() => dlg() && Array.from(dlg().querySelectorAll('button')).find((x) => x.textContent.trim() === 'Cancel invite'), 'confirm dialog');
    yes.click();
    await until(() => $$('.tm-row').length === 1, 'invite cancelled');
    ok(true, 'manager: cancelling an invite removes it');
    ok(vis(byText('button', 'Download CSV')), 'People: Download CSV is offered');

    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
