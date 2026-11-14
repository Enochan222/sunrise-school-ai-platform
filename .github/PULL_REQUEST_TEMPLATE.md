# Sunrise PR — Evidence, source identity and manual release controls

**Stage / single P-A-B-I-U owner:**  
**Explicit Owner authorization / active writer lease:**  
**User-visible scope and acceptance IDs:**  
**Base branch and exact Base Commit SHA:**  
**PR HEAD SHA / Git Tree SHA / changed Git Blob SHA:**  
**Tested Revision (exact full SHA):**  
**Workflow checkout SHA (PR merge-result if applicable, NOT interchangeable with Head):**  
**After authorized squash: main merge Commit / Tree (fill only after real merge):**  

## True test provenance
| Test category | Command or Workflow / Run / Job | Tested revision and environment | Observed result / exit code | PASS / FAIL / NOT_RUN | Redacted evidence |
|---|---|---|---|---|---|
| Documentation, links, manifest, static QA | | | | NOT_RUN | |
| Stage1 Light non-native `pytest tests/stage1` | | | | NOT_RUN | |
| Complete `pytest tests` regression | | | | NOT_RUN | |
| Real Native API, Dual-DB, HTTPS, Browser | | | | NOT_RUN | |
| Auth/CSRF/JWT, same-Gateway School/Source IDOR negatives | | | | NOT_RUN | |
| Cold Backup and independent Restore | | | | NOT_RUN | |
| Formal S1-AT01–15 | | | | NOT_RUN | |
| Independent Review / Owner UAT / R01 | | | | NOT_RUN | |

**CI scope:** Original Stage0 no-Actions D08 is historical. ONLY `stage1-light.yml` (eligible same-repository `main`-target PRs, Draft allowed, path-filtered, non-native only) and manual `stage1-native-integration.yml` are authorized. Cite actual Run ID / Job ID, workflow event, tested checkout SHA and separate PR HEAD; a missing/skipped/blocked run is NOT_RUN, never PASS. Do not assume that a workflow on `main` exists on an old implementation branch. No GitHub Copilot, new workflow, paid runner or billing change.

**Provenance / security / privacy:** Exact diff paths, source/image/runtime/TLS peer hashes, dependency/contract changes, negative tests and forward-fix plan. No credentials, `.env`, session/JWT/CSRF values, Mac private paths, student content, licensed originals, raw evidence or backup keys in public PR, history, Actions logs or artifacts. Follow [SECURITY.md](../SECURITY.md).

- [ ] Current Owner approvals and merged policy verified; D01–D08 original record unchanged
- [ ] Exact source blobs, Owner scope, tested revision and separate PR Head identified
- [ ] Applicable QA, regressions, native/IDOR/Restore/AT truthfully PASS or NOT_RUN
- [ ] Independent reviewer and Owner high-risk release authorizations independently recorded
- [ ] No auto-merge, bypass, force push or paid/public deployment
- [ ] Manual squash-only PR Merge is separately authorized, then re-read `main` commit/tree/blobs

**Formal R01 and Owner UAT cannot be inferred from green CI or a completed PR.**
