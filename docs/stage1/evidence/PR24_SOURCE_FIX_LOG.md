# PR24_SOURCE_FIX_LOG

**Scope: forward-only QA repairs on PR24 branch; PR14 untouched.** These Source/Test changes were made after initial candidate `5d2dc1ee7c51f1ccaa10a5423aad4090a7464586`, whose original 14 changed files were independently inspected. The final Git SHA/tree must be read again after all evidence-only commits; immutable Git Blob identities below are independent of later Markdown commits.

## TDD defect ledger

| Defect, reproduction (RED) | Minimal fix (GREEN) | Git commits |
|---|---|---|
| AT13 release allowlist rejected all three new legitimate `docs/stage1/*.md` reports; direct GitHub-source scope check returned allowed=0/3 | Added 13-case path test first, then exact three-file exception and `allowed_stage1_change()`, without accepting unrelated Stage0, workflow or generic docs | RED `793fa0b15cc63a141283f211cd61c56b5d1ecbce`; GREEN `db514396be623b98eb176c2e56e9b7586bdbbdb6` |
| Existing AT14 WP09 cookie-free test relied on old 3 env tokens `synthetic-allow`; revised source requires JIT RSA PEM, actual issuer/audience and 8 token cases | Updated existing regression to sign/verify real synthetic RS256, compare owner source metadata, check all eight HTTP statuses without carrying Admin cookie | `253c9274220087e0e9b90ed13ab719c89dedc93e` |
| Original WP03 source assertion still searched for old `first_reservation_races(configuration,actor,secret)` | Updated assertion to actual verified `native_endpoint` call and lost-ACK signature | `3f07554eea3bdf2bbba5c383f6088fdc27f7f36e` |
| Suspended Search + session clear + /auth/me rehydration: old actual JS `state.searching=true`, Search permanently disabled | RED contract committed, `clearPrivate()` now resets `state.searching=false`, new runnable Node DOM-shim regression added. Old V8 code RED, new GREEN, stale result ignored | RED `da6d32500d4498a188662ccd3c443edb7721b1f2`; source GREEN `c956fe0152c749118f9da46f59bd2f86ea8922ac`; dynamic test `297331b699a10a8f361f2fd26b68fa1ecd407aa4` |
| AT14 wrong-school negative could pass because foreign school was not actually permitted/provisioned | RED negative test added and Case 14 now requires authoritative `available_schools` contain BOTH different synthetic A/B schools before JWT probes | RED `b1ddd292c86b8aa61d7d643a013f3f418db75b73`; source GREEN `5c1941db98341f7e7542411bdf24e92c5b4b9413` |

## Changed Git Blobs after repairs (for reviewer verification)

| File | Git Blob SHA-1 |
|---|---|
| `apps/a-vault/ui.js` | `4d52e058c1141cbc4e176f9da46f59bd2f86ea8922ac` |
| `scripts/stage1/acceptance/http_boundaries.py` | `b61f9bfc2cdc7875f2b12239e798b16a2090aee4` |
| `scripts/stage1/acceptance/release_manifest.py` | `9d346aee58ac383f20b1f58298dd26b81685fa97` |
| `tests/stage1/acceptance/test_wp09_acceptance_gates.py` | `8439dbccd7cee207bb882b14c02f392f15e3e8b2` |
| `tests/stage1/test_wp03_unique_and_fault.py` | `aac736b47d35204c4eb5d31f61eca5b00f094247` |
| `tests/stage1/test_chat_at14_ui_regression_contract.py` | `d86744d7740c6d24c1304e1228909fba7a4304c4` |
| `tests/stage1/test_chat_release_scope_contract.py` | `955bae5a6315eded3ba015b5d86ebfe18eeaa778` |
| `tests/stage1/test_chat_ui_async_search_race.py` | `ebef48069f546367ac98c4151611819588a3f7ba` |

Unmodified original AT06 producer/consumer blobs remain as recorded in `PR24_INDEPENDENT_CODE_REVIEW`. Targeted executed evidence: 11 PASS +1 DESELECTED on exact original AT06/AT14 producer blobs; 13 PASS exact AT13 helper/test extraction; 2 PASS exact AT14 consumer function/test extraction; V8 actual UI before/after RED/GREEN plus Node harness exercised. No fresh full `pytest -q tests`, Node CLI or Docker/Firefox Runtime execution on the current complete PR Source.

All writes forward-only to the isolated PR24 branch; no rebases, force pushes, staged Registry changes, PR14 head updates, Docker access or merges.
