# PR24_FULL_NON_NATIVE_TEST_REPORT

**Verdict: FULL_NON_NATIVE_REGRESSION=NOT_RUN.** No full trustworthy checkout or exact candidate CI run was available in this Chat sandbox. Focused executable checks below are evidence of only the named subsystems.

## Fixed source and execution platform

- Repository: `Enochan222/sunrise-school-ai-platform`, Draft PR #24 into the open Draft PR #14 implementation branch.
- Reviewed engineering source before this report-only commit: `5c1941db98341f7e7542411bdf24e92c5b4b9413`, Tree `92dc2f8069cb83a611b4cf017ded112b2d81a8ee`. **Pin the final source Git HEAD/tree anew after all report commits; this is not the eventual final runtime identity.**
- Verified PR14 baseline HEAD: `83474cf42ba899d5d0427b3b22ee16d6b74592eb`.
- Isolated container: Python `3.13.5`, pytest `9.0.2`, PyJWT `2.13.0`, cryptography `46.0.4`, httpx `0.28.1`, Node `v22.16.0`. Repository QA requirements declare Python `3.11.11`; the executor does **not** have that interpreter installed.
- Private GitHub source available through connected GitHub plugin; direct `git ls-remote https://github.com/Enochan222/sunrise-school-ai-platform.git HEAD` failed: `Could not resolve host: github.com`. Local full repo path was absent; no complete 278-blob private clone could be verified.

## Commands and observed results

| Command / method | Result | Scope / evidence |
|---|---|---|
| `git rev-parse HEAD`; `git rev-parse 'HEAD^{tree}'`; `git status --porcelain` | NOT_RUN | Full Checkout unavailable; SHA/tree independently read via official GitHub Git Commit API |
| `python -m compileall -q apps/a-vault scripts/stage1 tests` | NOT_RUN | Full Checkout unavailable |
| `node --check apps/a-vault/ui.js` | NOT_RUN | Full Checkout unavailable; actual production `ui.js` did compile and execute in isolated V8 DOM shim |
| `python -m pytest -q tests` | NOT_RUN | Full Checkout unavailable; **do not** infer a full regression PASS |
| `python -m pytest -q tests/stage1/test_at14_jit_service_token_claims.py tests/stage1/test_at06_native_endpoint_contract.py -k 'not no_implicit_native_port_fallback'` | **11 PASS, 1 DESELECTED, Exit 0** | Exact Git Blob content for 4 producer/test files reconstructed in isolated scratch. Three other Source files required by the deselected contract were only read via GitHub |
| `python -m pytest -q tests/stage1/test_chat_release_scope_contract.py` | **13 PASS, Exit 0** | Exact remote test content + extracted exact AT13 path helper in an isolated mini-module, not full `release_manifest.py` |
| `python -m pytest -q tests/stage1/acceptance/test_service_jwt_contract_extracted.py` | **2 PASS, Exit 0** | Actual `case_14` function extracted from GitHub (5,780 characters, FNV1a `e5fdc361`) plus exact two updated Test functions (4,103 characters, FNV1a `53d3f091`) and signer exact Git Blob `009d154fc2f9b64c2c384bd2e293ab3878d999e6`; simulated isolated Cookie-free HTTP and actual PyJWT signature/claims evaluation |
| UI JS suspended Search → revoked Session → new /auth/me → delayed response | RED old SHA, GREEN corrected SHA | Exact `ui.js` source executed under V8 mock DOM; before: `afterHydrationSearching=true`, Search disabled; after: false and enabled. New Node test harness also executed in V8 with Node module shims, 5 assertions, Exit 0; **not** real Firefox or Node CLI subprocess |
| Fresh synthetic RSA fixture CLI | PASS, Exit 0 | Actual source CLI created 3 files (private key, public key, 8 JWT env fixtures), folder mode `0700`, file modes `0600`; temporary files deleted |
| GitHub PR #24 candidate HEAD CI | **NO ASSOCIATED RUN FOUND** | Earlier PR #14 Light CI 417 passed and Mac earlier 426 passed refer to **different** source revisions, not this PR |

The three isolated pytest invocations have independent counts. They **must not be added together and presented as a full-suite result**. One deselected AT06 Source contract remains unexecuted in the micro-checkout.

## QA gates and failure attribution

`FULL_NON_NATIVE_REGRESSION=NOT_RUN` due Checkout and pinned runtime availability, **not** an asserted application PASS or FAIL. The identified stale AT14/WP03 tests and AT13 scope defects were actually repaired on the PR branch; their focused checks are recorded, but all changed files still require complete repository pytest. Strict real Docker, pinned Open Notebook, private Gateway, Firefox/NSS, external signed observer and restore acceptance remain NOT_RUN.

Gate 1 on an authorised complete Checkout: verify clean Git SHA/tree, run `python -m compileall -q apps/a-vault scripts/stage1 tests`, `node --check apps/a-vault/ui.js`, `python -m pytest -q tests`, re-check Git cleanliness and record complete raw output/exit codes. Do not label PASS unless the last command exits zero with the real complete suite. No historical or selected-case PASS may substitute.
