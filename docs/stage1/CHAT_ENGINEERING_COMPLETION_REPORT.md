# CHAT_ENGINEERING_COMPLETION_REPORT

**Status: engineering source candidate committed; full runtime acceptance not approved.**
Repository: `Enochan222/sunrise-school-ai-platform`
Independent branch: `stage1/chat-at06-at14-contract-20261114`
Review Draft PR: https://github.com/Enochan222/sunrise-school-ai-platform/pull/24
Parent PR14 verified baseline: `83474cf42ba899d5d0427b3b22ee16d6b74592eb`, tree `3fdbdbcdd7cb466829d5c189c12beb46794af934`.
For current changed HEAD/tree read PR24 live GitHub; do not mistake baseline for updated candidate.

## Stage-by-stage disposition

| Stage | Source work | Status / limitation |
|---|---|---|
| 1: Baseline | PR14/PR22 heads, parent drift, CI and owner writer permission read. Old UI hydration work already incorporated at PR14; no duplicate PR22 merge. | PASS for source-level baseline only |
| 2: AT06 | New verified endpoint resolver invokes real Docker `load_containers`, matches all three service containers, relays, network IDs, immutable images, volumes and published ports with captured provenance. Journal, race, crash child and lost ACK share the explicit URL; no fallback `5055`. Tests cover changed port, relay, project, network, image, volume, stale digest and source contract. | SOURCE_FIX_COMMITTED; RUNTIME_RETEST_REQUIRED |
| 3: AT14 | Synthetic RSA fixture generator (3072-bit private/public keys, never committed); new signing function builds one positive and seven negatives at AT14 case time; no stale 4-minute positive JWT after earlier acceptance. A fresh cookie-free HTTPS client, exact subject/source IDs/version/SHA comparison and independently checked negative claims prevent common false PASS. | SOURCE_FIX_COMMITTED; real HTTP NOT_RUN |
| 4: UI/Acceptance | Search disabled/rejected while session hydration is busy; initial Create/etc hydration fix already upstream; AT13 regression executor broadened to `pytest -q tests` rather than stage1-only. | SOURCE_FIX_COMMITTED; Firefox and full regression NOT_RUN |
| 5: Observer/Transferability | Added `PORTABLE_STAGE1_TEST_HANDOFF.md` and `WORK_OR_LOCAL_RUNTIME_HANDOFF_PROMPT.md`. Observer schema, independent signed host attestation, real port denials and human AT07 storage review documented; Mac `ifconfig -a` Linux portability remains unverified. | SOURCE_DOCS_COMMITTED; external evidence NOT_RUN |
| 6: Integration | All candidate changes confined to separate forward-only branch and Draft PR24. PR14 kept Draft/unmerged; no Stage status/UAT/R01 updates. | REVIEW_PENDING; no formal acceptance |

## SOURCE_FIX_AND_TEST_MATRIX

| Fix | Producer | Consumer | Positive / negative proof added | Executed evidence |
|---|---|---|---|---|
| AT06 native URL | `executed_runtime_provenance.py`; `surreal_journal_smoke.py`; `wp03_races.py`; `native_ack_loss_probe.py` | AT06 journal report + `run_stage1.py` | dynamic loopback URL; wrong host port, relay/container/image/project/network/volume, stale identity reject; child/proxy same endpoint | GitHub source readback/static assertions only, real Docker NOT_RUN |
| AT14 JWT | `make_synthetic_service_jwt.py`; `http_boundaries.py` | AT14 service material endpoint and original A Gateway verifier | RS256 valid + 7 negatives; just-in-time expiry/no confounded negatives; cookie-free pinned CA; source ID/version/SHA | GitHub source readback/static assertions only, actual HTTP NOT_RUN |
| UI | `ui.js` | Browser contract + UI tests | `sessionBusy` blocks search control and submit; previous Create hydration remains unmodified | Static source check, Firefox NOT_RUN |
| AT13 | `acceptance/regression.py` | `run_stage1.py` final case | invokes full `tests` directory | Source contract check, full pytest NOT_RUN |
| Independent observer | Original `external_target_attestation.py` and `security_at.py` unchanged | AT02/07/09 | documented actual signatures, independent vantage, freshness and real human AT07 attestation | external observer NOT_RUN |
| Portability | two new handoff Markdown files | second authorised executor | detailed per-host setup and exact runtime-only prompt | document source readback; Linux runtime NOT_RUN |

## Verification and current limits

At independent candidate review, 14/14 narrowly targeted GitHub Git Blob source assertions passed, including changed Native endpoint propagation, JWT negative matrix and JIT signer, UI lock, and AT13 scope. These are **static inspections**, not executions of the repository pytest suite. An attempted external Python executor returned only an interactive “will execute in browser” preview, **no execution output**; the standalone container has no DNS access to the private GitHub repository (`Could not resolve host: github.com`). Therefore no exact candidate pytest count, Python compileall count, Node syntax check, actual Docker test, signed observer or Firefox PASS may be reported from this Chat. PR24 CI run may also be absent because the existing workflow targets PR14/main; always re-query.

The old PR14 Light CI 417 passing and Owner Mac 426 passing were run against **earlier commits**. Those results are not transplanted to this branch.

**Final gate:** Source candidate committed, static contract review PASS_WITH_LIMITATION, non-native regression BLOCKED/NOT_RUN, runtime tests BLOCKED/NOT_RUN, full formal Stage 1 acceptance NOT APPROVED, UAT NOT APPROVED, R01 NOT APPROVED, all merges BLOCKED pending independent review.

## Next dominant blocker

A checkout of the exact PR24 candidate in a trusted executor with `pytest -q tests` and the actual Docker/runtime identity; then independent observer and a fresh full 15-case campaign with the same immutable SHA/tree. Do not execute any previously frozen project or substitute another candidate's evidence.
