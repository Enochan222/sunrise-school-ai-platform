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
| AT06 native URL | `executed_runtime_provenance.py`; `surreal_journal_smoke.py`; `wp03_races.py`; `native_ack_loss_probe.py` | AT06 journal report + `run_stage1.py` | dynamic loopback URL; wrong host port, relay/container/image/project/network/volume, stale identity reject; child/proxy same endpoint | GitHub exact-blob isolated AT06 tests: 9 passed, 1 source-contract deselected; real Docker NOT_RUN |
| AT14 JWT | `make_synthetic_service_jwt.py`; `http_boundaries.py` | AT14 service material endpoint and original A Gateway verifier | RS256 valid + 7 negatives; just-in-time expiry/no confounded negatives; cookie-free pinned CA; source ID/version/SHA | GitHub exact-blob isolated signed JWT tests: 2 passed; generator CLI and private permissions PASS; actual HTTP NOT_RUN |
| UI | `ui.js` | Browser contract + UI tests | `sessionBusy` blocks search control and submit; previous Create hydration remains unmodified | Static source check, Firefox NOT_RUN |
| AT13 | `acceptance/regression.py` | `run_stage1.py` final case | invokes full `tests` directory | Source contract check, full pytest NOT_RUN |
| Independent observer | Original `external_target_attestation.py` and `security_at.py` unchanged | AT02/07/09 | documented actual signatures, independent vantage, freshness and real human AT07 attestation | external observer NOT_RUN |
| Portability | two new handoff Markdown files | second authorised executor | detailed per-host setup and exact runtime-only prompt | document source readback; Linux runtime NOT_RUN |

## Verification and current limits

**Executable isolated non-native tests, exact remote Git blobs:** the connected GitHub Plugin fetched four file contents: `make_synthetic_service_jwt.py` (blob `009d154fc2f9b64c2c384bd2e293ab3878d999e6`), `test_at14_jit_service_token_claims.py` (blob `98bdbebf59b5366b1184afe12a1efd86a055cd33`), `executed_runtime_provenance.py` (blob `789732f795004df3185be678b8712b6e56f29979`), and `test_at06_native_endpoint_contract.py` (blob `8181ba8a10b7028d0418c9d1fabcddf58183b945`). An isolated scratch test tree was populated with exactly the remote content; independent Git blob hashing matched every corresponding SHA. Executed `python -m pytest -q /tmp/sunrise-source-qa/tests/stage1/test_at14_jit_service_token_claims.py /tmp/sunrise-source-qa/tests/stage1/test_at06_native_endpoint_contract.py -k 'not no_implicit_native_port_fallback'`: **11 passed, 1 deselected, 0 failed, 0.59s**. The deselected test needs three additional production script files absent from this isolated mini-checkout; the three source files had previously been verified by individual GitHub static reads for the obsolete URL. **Never describe this as a full repository checkout or full pytest pass.**

Also actually executed the exact-blob AT14 synthetic RSA fixture CLI under a newly generated disposable scratch folder. It produced three private files (signing PEM, public PEM, eight token fixture values), verified directory mode `0700`, all files mode `0600`, exactly eight distinct expected fixture names. No tokens or keys were printed or committed. Scratch fixture directory was removed after the test; historical Docker/evidence/volumes untouched. In addition, **14/14 source-level GitHub Blob assertions** passed at code review stage, checking endpoint propagation, JWT negative cases, busy guard and full regression scope; subsequent code edits were separately fetched and reviewed.

**Limits:** GitHub Light CI `417 passed` and Owner Mac `426 passed` are on earlier commits, so cannot be reused for this candidate. This Chat cannot perform a full private repository clone because its sandbox DNS cannot resolve `github.com`. The Code Tytor executor returned an interactive browser execution preview, not completed Python logs. Therefore *full* `pytest -q tests`, `compileall` against all repository paths, Firefox, actual Docker/SurrealDB/Native journal, strict HTTPS Gateway AT14, signed independent observer, cold restore and formal AT01–15 are **NOT_RUN on this candidate**. A Draft PR and individual passing tests do not approve formal acceptance.

**Final gate:** SOURCE_FIX_COMMITTED=YES; STATIC_CONTRACT_CHECK_PASS=YES within cited inspected paths; TARGETED_NON_NATIVE_UNIT=11_PASS_1_DESELECTED; FULL_NON_NATIVE_REGRESSION=NOT_RUN; RUNTIME_RETEST_REQUIRED=YES; FORMAL_AT_NOT_APPROVED=YES; OWNER_UAT/R01=NOT_APPROVED; PR14/PR24=UNMERGED.

## Next dominant blocker

A checkout of the exact PR24 candidate in a trusted executor with `pytest -q tests` and the actual Docker/runtime identity; then independent observer and a fresh full 15-case campaign with the same immutable SHA/tree. Do not execute any previously frozen project or substitute another candidate's evidence.
