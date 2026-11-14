# PR24_INDEPENDENT_CODE_REVIEW

**Verdict: SOURCE REVIEW COMPLETED WITH TEST-EXECUTION LIMITATION; NOT MERGE APPROVAL.**

Original PR24 base is PR14 HEAD `83474cf42ba899d5d0427b3b22ee16d6b74592eb`. Read original 14 changed GitHub blobs and Diff independently at fixed PR24 revision. Source repairs added a further 5 engineering files before the reporting documents. No PR14 writes or merge.

## Original 14 paths

| Path | Independent finding / proof |
|---|---|
| `apps/a-vault/ui.js` | **Critical Search deadlock repaired**: prior `clearPrivate` did not reset `state.searching`, so old pending Search prevented Search after new session hydration. Actual prior JS failed and repaired JS passed in V8 DOM-shim. Create/Upload/Archive/Switch still use existing `canWrite`/session gate. Firefox NOT_RUN |
| `docs/stage1/CHAT_ENGINEERING_COMPLETION_REPORT.md` | Report accurately distinguishes candidate Source from Runtime and formal approval; supplemental execution results provided in exact-named QA report |
| `docs/stage1/PORTABLE_STAGE1_TEST_HANDOFF.md` | Independent Ed25519 target/port observer, synthetic project, strict TLS, preserved volumes, Linux portability warning; reviewer/human attestation not created |
| `docs/stage1/WORK_OR_LOCAL_RUNTIME_HANDOFF_PROMPT.md` | No Work-to-Mac-loopback assumption, no public relay and no old frozen Docker volume reuse; coherent runtime-only handoff |
| `scripts/stage1/acceptance/http_boundaries.py` | One positive JWT plus seven non-confounded negatives, JIT private signing, strict Gateway CA, cookie-free probes, positive owned source ID/version/SHA equality; **unknown-school false PASS repaired** by requiring trusted Gateway list contain BOTH synthetic schools. Real HTTP NOT_RUN |
| `scripts/stage1/acceptance/make_synthetic_service_jwt.py` | Isolated actual producer emits 3072-bit RSA test key and fixture set; mode `0700` folder, `0600` key/token files, private key never configured in Gateway. Isolated signing tests PASS |
| `scripts/stage1/acceptance/regression.py` | Full `python -m pytest -q tests` with 600-second timeout, strict source cleanliness and SHA/tree pre/post checks. Real full suite NOT_RUN, timeout does not report PASS |
| `scripts/stage1/executed_runtime_provenance.py` | Saved SHA/tree and all three live Docker physical engines, containers/images/relays/networks/volumes/published ports cross-compared; dynamically resolves Native loopback port. Unit mocks cover wrong identity. TOCTOU cannot be excluded purely by Docker snapshots |
| `scripts/stage1/native_ack_loss_probe.py` | No 5055 default, explicit loopback Native URL, one real upstream POST before dropping downstream ACK. Actual Runtime loss scenario NOT_RUN |
| `scripts/stage1/surreal_journal_smoke.py` | Attested endpoint flows to recovery, subprocess crash, three race cases, lost-ACK and final identity guard; never claims DB-only evidence as full Native PASS |
| `scripts/stage1/wp03_races.py` | Uses explicit endpoint for all Native side effects, keeps fresh-claim uniqueness/no duplicate mapping. Race with actual SurrealDB/Native NOT_RUN |
| `tests/stage1/test_at06_native_endpoint_contract.py` | 9/9 selected mock-based endpoint checks PASS in isolated execution; one source-contract test deselected outside full checkout. Mocks are not real Docker attestations |
| `tests/stage1/test_at14_jit_service_token_claims.py` | Actual RS256 crypto checks PASS with valid, wrong-scope/school and invalid-claim cases; does not replace Gateway TLS tests |
| `tests/stage1/test_chat_at14_ui_regression_contract.py` | Static contracts now include Search reset in addition to busy guard and JWT/AT13 scope; supplemented by behavioral execution. Not Firefox |

## QA-added review targets

`scripts/stage1/acceptance/release_manifest.py`: previously rejected three valid handoff docs; now permits ONLY those three exact names, with all unlisted Stage0/governance/Workflow paths still denied. `tests/stage1/test_chat_release_scope_contract.py`: 13 isolated tests PASS (6 positive, 7 negative). `tests/stage1/acceptance/test_wp09_acceptance_gates.py`: repaired obsolete fake three-token AT14 regression to actual JIT signed 8-token test; two extracted tests PASS. `tests/stage1/test_wp03_unique_and_fault.py`: correct verified Native endpoint signature assertion. `tests/stage1/test_chat_ui_async_search_race.py`: executes true UI source in Node DOM-shim; harness itself executed in V8 with deterministic synthetic API, 5 assertions PASS; not real Firefox.

## Cross-source security and integration

- Reviewed PR14 source diff: 99 paths; PR14→PR24 engineering diff: 19 paths; **zero paths outside the exact revised release-scope allowlist**. Report-only files under `docs/stage1/evidence/` are already allowed by the unchanged original prefix.
- Source patterns for private PEM blocks, GitHub tokens, literal JWTs and personal home paths: no findings in the 19 engineering changed blobs. Not a complete secrets scanner.
- `vault_app.py` JWT verifier unchanged: verifies RS256 signature, issuer, audience, mandatory claims, scope/school, and rechecks principal before returning private data.
- No proof of absence of container identity drift exactly between check and Native POST; no real Gateway CA peer proof, Firefox/NSS, real source/restore campaign, external independent observation or Owner review.
- Verdict is strictly **source-reviewed candidate, not INTEGRATION_REVIEW_READY**, pending complete checkout regression and independent runtime QA. Maintain both PRs Draft/unmerged.
