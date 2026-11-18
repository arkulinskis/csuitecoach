# C-Suite Coach

**C-Suite Coach Institute** is an executive-education and certification app for current and aspiring C-suite leaders
(CEO, CFO, COO, CHRO, CTO/CIO/CISO, CMO), plus the board's big mandates (M&A, activist investors, AI governance) and
hiring judgment. Members study research briefings and real business cases, drill what they learn
with spaced repetition (the CAF Guide method: active recall, reveal, rate yourself, Leitner boxes), practise decisions in
written boardroom challenges, sit a final examination, and earn certificates with public verification codes. The
Institute is the app's own authority: the certificates say so honestly. Built on [Anvil](https://anvil.works).

- **App repo:** github.com/arkulinskis/csuitecoach (branch `master`). Anvil pulls `master`.
- **Live:** https://csuite-coach.anvil.app
- **The research** behind the content: `RESEARCH.md` in the project folder (not synced to the repo); every module and case also lists its sources.

## What it does

**For everyone (no account needed):**
- **Landing page:** photo hero with a sample certificate, the method (4 steps), the 9 programs, Casebook teasers, good vs
  bad advice, a quote, credential verification, the Honour Roll, For leadership teams (team plan), FAQ (including "is it accredited?": no).
- **Programs** (`#tracks`, `#tracks/<id>`): 9 programs (Executive Foundations + 6 role programs + 2 specialist programs added 2026-11-18:
  **Board Mandates** (M&A deal thesis, M&A integration, activist investors, AI governance oversight, AI governance in
  practice) and **Hiring Judgment** (the selection evidence, then judging product, marketing, operations and project
  leaders)), each with modules,
  outcomes, the final examination and the Fellowship explained.
- **Module briefings** (`#module/<id>`): readable by anyone: the briefing, Do / Avoid lists, case files, sources.
- **The Casebook** (`#cases`, `#cases/<id>`): 40 real, sourced cases (Tylenol, Ford's red slide, Intel, IBM, Kodak,
  Blockbuster, Qwikster, Starbucks, Microsoft, Unilever, Wells Fargo, Boeing 737 MAX, GM, BP, Maersk, Equifax,
  CrowdStrike, Southwest, SVB, Theranos, Disney, Patagonia, PepsiCo, Teledyne; since 2026-11-18 also Disney-Pixar,
  DaimlerChrysler, AOL Time Warner, HP-Autonomy, Engine No. 1 vs Exxon, Trian vs P&G, Air Canada's chatbot, Zillow
  Offers, Amazon's hiring AI, Klarna's AI service, AI washing, J.C. Penney, Yahoo's COO, HealthCare.gov, Google's
  Project Oxygen, Tim Cook's hire at Apple), filterable by exemplary / cautionary / mixed.
- **Team plan page** (`#team`): what the team plan does, with sign-up; **team invites** (`#join/<token>`): who invited
  you, the programs, what the manager will see, then create an account or sign in and come back to join.
- **Verify a credential** (`#verify/<code>`) and **certificate pages** (`#certificate/<code>`), plus the public **Honour Roll**.

**For members:**
- **Dashboard** (`#home`): rank (Analyst → Chair) and XP, streak, drills due today, the next module, open examinations,
  every program's progress, credentials, case of the day, Honour Roll.
- **Drills** (`#study/review`, `#study/<module>`): recall cards and "advice calls" (sound advice or a trap?). Reveal, then
  Still learning / Got it (keys: space, 1, 2). Leitner boxes 0-6, due after 0/1/3/7/16/35/90 days. Missed cards return
  once at the end of the session.
- **Challenges** (`#challenge/<id>`): a scenario per module; write your decision, then compare with the examiners' model
  answer and tick the rubric criteria you covered. 70% to pass. Attempts are kept.
- **Module completion** = briefing read + every drill learned (box ≥ 1) + challenge ≥ 70%. +40 XP.
- **Final examination** (`#exam/<track>`), open when every module of the program is complete: honour code, Part I recall
  round (12 random drills from the program, 80% "Got it"), Part II capstone case (rubric, 70%). Pass → a certificate
  `CSC-<CODE>-<YEAR>-<6 chars>` (+200 XP); fail → retake after 30 minutes, missed drills go back to box 0.
- **Fellowship:** Foundations + any two other program certificates issue the Fellow of the C-Suite Coach Institute (FCSCI) certificate
  automatically (navy and gold design).
- **Credentials** (`#credentials`): certificates, the path to Fellowship, Honour Roll opt-in. Certificate pages print to
  PDF (landscape), copy the verification link, and "Add to LinkedIn" (for the holder).
- **Profile:** name (printed on future certificates), job title, Honour Roll opt-in, theme, password reset.
- **Team plan** (`#team`, 2026-11-18, free): anyone can create one team and becomes its manager. Invite leaders by
  pasting "Name, email" lines (up to 50 at a time, 200 per team), tick the programs they should complete, and each
  gets a personal link `#join/<token>` (emailed by Anvil's email service, and copyable). The invitee creates an account
  or signs in and joins; one team at a time (joining another leaves the old one). The manager sees stats (members,
  invites waiting, average progress, certificates), each person's assigned programs with modules done and progress,
  certificates, drills learned, streak and last study day, never their written answers; can change programs, email an
  invite again, cancel invites, remove members, rename or delete the team, and download a CSV. Members see
  "Assigned by <team>" on the dashboard and can leave from `#team`.

**For admins** (`#admin`; your admin email (App Secret `admin_emails`) becomes an admin on first sign-in):
- **Overview:** members, learners, teams, modules completed, challenge attempts, examinations sat, credentials issued, feedback.
- **Credentials:** search every certificate, revoke or reinstate (a revoked certificate shows a red REVOKED stamp).
- **Feedback inbox**, **Users** (make admin, disable), **Demo data**: six fictional executives with progress and
  certificates (sample records), on the Honour Roll; remove or reload.

## Setting it up in Anvil (once)

1. In the Anvil editor: **Create app → Clone from GitHub**, and paste `https://github.com/arkulinskis/csuitecoach`.
2. **Users** service: email + password and "Continue with Google", sign-up allowed (already set in `anvil.yaml`; check it).
3. Open the app in the editor. If it shows a **Schema Mismatch** alert, choose **"The schema of the source code is correct"** so Anvil creates the tables.
4. **Run** it and sign up with **your admin email** (App Secret `admin_emails`) straight away (that account becomes the admin).
5. **Publish** (Publish → public URL, or your own domain).

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [YouTube embeds](https://developers.google.com/youtube/player_parameters) | Outside web service | Plays a YouTube video inside the page (the privacy-friendlier youtube-nocookie address). |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Cormorant Garamond, Inter |

**Built into the browser:** localStorage, Clipboard.

**Anvil platform:** Anvil, Anvil Data Tables, Anvil JS bridge (anvil.js), Anvil Secrets, Anvil Users, Anvil Google service, Anvil Email, Anvil Media.

**Build and test tools (not shipped):** axe-core, Node.js, Headless Chrome (DevTools Protocol), PyYAML.

<!-- libraries:end -->

## Working on it

See `.claude/skills/csuitecoach/SKILL.md`. In short:

```
python -I tools/check.py --ui                    # syntax, server tests, headless UI tests → ALL CHECKS PASSED
python -I tools/preview/devserver.py 8765        # the app on in-memory data: http://localhost:8765/  (?as=ana#home, ?as=admin#admin)
python tools/deploy.py                           # dry run (needs PyYAML, so no -I)
python tools/deploy.py --push "Message"          # deploy: commit + push to GitHub, Anvil pulls it
```

## Project layout

```
web/            core.js/core.css (engine + Boardroom Classic tokens), app.js (header, footer, seal, icons),
                pages/_shared.html (CS helpers: drill engine, certificate, hero, cards), pages/*.html
client_code/    Main.py (the only Anvil form: bridge to the server, sign-in), legal.py
server_code/    content_core.py, content_roles_a.py, content_roles_b.py, content_cases.py (the curriculum),
                Curriculum.py, Learning.py, Exams.py, Credentials.py, Accounts.py, Admin.py, DemoData.py, Feedback.py, common.py
assets/         icon.svg + PNG icons, ph-*.jpg stock photos (Pexels licence, served at _/theme/<name>)
tools/          sync_to_anvil.py (settings + table schema), deploy.py, check.py, preview/ (dev server, UI tests, screenshots), testing/
```
