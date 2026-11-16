# Stage 1 A teaching-library UI refresh — candidate evidence

This candidate improves the existing protected A workspace: clearer login purpose, subject/grade collection cards, search and download before upload, expandable provenance and responsive reading order. It uses UI/UX Pro Max guidance, not new product capabilities. No backend, API, schema, authentication, dependency, Docker, workflow or accepted runtime configuration changed.

## Source and design provenance

- Base main: `35e3e25d11b2e5ae52caf2b5599e19417a6b87e9`.
- Tested Revision: `3f61a4e199808e770d7a192bd9964817e9c30f95`; Git tree `986ffc7d3d69065bc811dc114443a8e5c7c08ea4`.
- Later evidence-only commit is not a new runtime test campaign.
- Requested skill: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill ; inspected skill revision `e59ff376a41f7ca47b7541ad5c116495cbade3ee`.
- Read `.claude/skills/ui-ux-pro-max/SKILL.md` and professional rules. Executed search.py `education content library dashboard --design-system -p "Sunrise Vault"`; retained its minimal grid and education palette direction. Its children's font suggestion did not suit administrators. Narrower `professional knowledge dashboard` confirmed professional typography direction; final implementation uses local system/CJK fonts and darker green for contrast. No remote fonts, npm packages or CDN assets.
- Existing pinned Open Notebook notebook page/CreateNotebookDialog were inspected. Their raw notebook create API is incompatible with A policy; preserve the existing secure wrapper rather than exposing native UI or adding a second ingestion engine.

## Executed checks

Browser started `2026-11-16T16:54:19.361665+00:00`; finished `2026-11-16T16:54:21.541848+00:00` (UTC).

| Check | Observed result |
| --- | --- |
| Existing regression suite | PASS — `python -B -m pytest -q tests`: 510 passed, one existing Starlette/AnyIO deprecation warning |
| Governance QA | PASS — `python -B scripts/run_qa_no_actions.py`: 16 commands exit 0 |
| Wrong password | PASS — POST /auth/login 401 and visible error |
| Login and session | PASS — POST /auth/login 200, /admin 200, /auth/me 200 |
| Collection/material visibility | PASS — 3 synthetic collections, selected material; GET shells/detail/materials 200 |
| Scoped search | PASS — POST selected-shell/search 200; result visible |
| Original PDF | PASS — GET selected-material/download 200; browser attachment saved; SHA256 matched displayed metadata |
| Create, upload, archive | PASS — actual Gateway requests 201/201/200; new collection selected, upload listed, archive removes upload and retains material visibility |
| Logout and login again | PASS — logout 200; login 200; four fixture collections retained |
| Responsive workspace | PASS — no document horizontal overflow at 375/768/1024/1440px; desktop/mobile screenshots inspected |
| Keyboard/reduced motion | PASS — keyboard submit/focus and disclosure; reduced-motion transitions disabled; mobile selected content precedes create form |

Tested source file SHA256:

- `apps/a-vault/templates/admin.html`: `33df983083c19a026384e2e5c9e8a3579f6b4796423576444f4a9717987b25ad`
- `apps/a-vault/templates/login.html`: `44ba8a8eda57fafd82f717bc6ad60283ba02ee13f0be34fffe319c02c8d71592`
- `apps/a-vault/style.css`: `93bd562cb9bd119fcedd2fe38e9ddd56041ecba978f6806c0fea16f1507de98a`
- `apps/a-vault/ui.js`: `7e99c7082ba295f350a5e35de3765484c36a59f0d99cf5058bde9e305f30bff1`

## Evidence and limits

Local evidence directory: `/private/tmp/sunrise-ux-20261117/`. Contains `preview.py`, `browser_check.py`, `accessibility_check.py`, actual response status timeline in `browser-result.json`, `accessibility-result.json`, source hashes, screenshots, full regression/governance logs and server logs. Python executable: `/private/tmp/sunrise-final-r01-repaired-20261115/product/bin/python`; governance executable is its sibling `governance/bin/python`. Browser commands use `python -B` followed by those recorded script paths. Preview is loopback-only and separately labelled synthetic; its password is generated into a private mode-0600 file and is excluded from public artifacts.

This is a real Chromium UI journey against the real FastAPI Gateway and a **separate synthetic SQLite fixture with a fake Native adapter**. It is not a SurrealDB/Native worker, HTTPS deployment, independent restore or new formal S1-AT01–15 PASS. Original frozen acceptance services, keys, volumes and backups were not operated on. Existing R01 evidence stays source-bound. No claim of commercial usability validation or human product approval is made; Owner review of appearance/workflow remains open. New UI is a feature-branch candidate, not main/deployment acceptance. Rollback is to keep/revert the four frontend files; no data migration is involved.
