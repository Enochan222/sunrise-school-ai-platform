# FINAL_RUNTIME_EXECUTION_HANDOFF_PROMPT

You are the authorised **Mac Local Sunrise Stage 1 [A] synthetic runtime executor**. This handoff is for the **last missing executable tests and actual acceptance evidence only**, not architecture design or another code review. First read PR24's `PR24_FULL_NON_NATIVE_TEST_REPORT`, `PR24_INDEPENDENT_CODE_REVIEW` and `PR24_INTEGRATION_DECISION` under `docs/stage1/evidence/`. All Source fixes are only a candidate until the complete checkout regression passes. Do not assume Work Cloud Browser can connect to Mac `127.0.0.1`.

## Gate 0: Immutable source and complete Non-Native (mandatory before Runtime)

Use the **final GitHub PR24 head commit and tree reported in the frozen PR24 integration comment**, not its old `5d2dc1ee...` baseline. In a fresh **clean isolated checkout** under Python 3.11.11 with pinned requirements and Node, re-read actual GitHub PR14 base/head and inspect overlap. Run and capture actual exit codes:

```bash
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git status --porcelain
python -m compileall -q apps/a-vault scripts/stage1 tests
node --check apps/a-vault/ui.js
python -m pytest -q tests
git status --porcelain
```

If any failure: distinguish missing dependency, test defect, real Source defect, and expected negative; repair in a new forward-only isolated engineering commit, then **re-freeze SHA/tree and rerun affected plus full tests**. Do not turn NOT_RUN into PASS. Do not modify PR14 or merge either PR.

## Gate 1: Fresh exclusive synthetic physical identity

Use Open Notebook **v1.15.1** pinned commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239` and two SurrealDB **v2.3.10** physical engines. Create **a new uniquely named** `sunrise-s1-...` project with distinct A, ON, Native volumes and exactly three scoped loopback relays, private internal networks, explicit distinct loopback host ports. Check actual `docker inspect`, image digests, mapped ports, Gateway HTTPS CA/peer and instance. Never read/restart/unfreeze/delete any previously failed/frozen project, volume, archive or evidence. No `docker prune`, `down -v`, host-wide settings, public DB/Native exposure or real student data. Use private, externally stored synthetic credentials and evidence.

The independent observer must FIRST sign a genuine authenticated Mac-host identity challenge, then the operator captures a fresh Runtime Identity with `runtime_identity.py`. After capture the independent observer actually probes all three physical role port mappings from an off-host isolated network and signs `SUNRISE_S1_EXTERNAL_PORT_DENIAL_V1`, bound to exact SHA/tree/Runtime SHA/Gateway instance; freshness <=10 minutes. The observer's private signing key and separate human AT07 storage-review signing authority **must never** be held or impersonated by this runner.

## Gate 2: Real isolated acceptance (official fixed runner order)

Prepare actual synthetic two-school A/B shells, two original PDF sources, owner/rights/retention/version, Native graph and Worker searchable text, all bound to exact Source SHA/tree. Before launching Gateway configure its `VAULT_SERVICE_PUBLIC_KEY_PEM`, `VAULT_SERVICE_ISSUER`, `VAULT_SERVICE_AUDIENCE` from new private synthetic RSA fixtures. The AT14 runner signs one valid and seven negative tokens just-in-time from `VAULT_AT14_SIGNING_KEY_FILE` (regular external `0600` PEM, NEVER on Gateway), `VAULT_AT14_ISSUER`, `VAULT_AT14_AUDIENCE`.

Invoke the actual `scripts/stage1/acceptance/run_stage1.py` with a newly checked exclusive synthetic scenario, exact commit/tree and **new empty evidence directory**; default full 15-case order is:

`S1-AT02 → 03 → 06 → 07 → 08 → 09 → 10 → 11 → 14 → 15 → 04 → 05 → 12 → 01 → 13`.

The runner must actually verify:
- **AT06** independent live Native relay URL, durable Surreal Journal, fresh 8-worker races, crash child, lost TCP ACK, exactly-once mapping, marker and changed-relay rejection.
- **AT14** real pinned-CA HTTPS Gateway with cookie-free positive JWT, owned Source ID/version/SHA and seven distinguishable negative-claim tests; unknown/unprovisioned school is not a meaningful wrong-school negative.
- **Firefox** genuine pinned Playwright Firefox/NSS full Admin journey with strict TLS and School/CSRF/session hydration, Search old-response rejection, Create/Upload/Archive/Download.
- **AT02/07/09** independently signed actual off-host port denials plus real login/logout/session/security checks; AT07 needs separately signed real human synthetic-storage full-volume review, no faked signature.
- **AT04** genuine restart with source/service/relay/Gateway identity consistency, persistent sessions and original PDF SHA.
- **AT05/12** frozen cold capture, genuinely separate new clean target Docker network/three volumes, independent restore readback, source owner graph, worker search, original SHA, metadata rights/version/retention and non-destructive original volumes.
- **Remaining AT01–15 and AT13** all 14 prerequisites on same source/runtime campaign, exact-case evidence hashes, actual full `pytest -q tests`, release manifest and highest unapproved release gates.

## Gate 3: Resumability, stop conditions, evidence

Always keep an immutable output directory per attempted Runner invocation, with command, exit code, timestamps, source SHA/tree, Git Blob identities, runtime/Gateway hashes, actual port and image identity, TLS/NSS and signed observer attestation identifiers, nonsecret negative outcomes, restore SHA and all PASS/FAIL/NOT_RUN. Selected diagnostic subset exit code 2 is **not** full Stage PASS.

If a case fails before any destructive/freeze boundary and original exclusive project's actual identity/source/CA remain unchanged, investigate and selectively re-run diagnostics against that same **fresh project's still-valid state** with new separate evidence, rather than rebuilding everything. A failure that freezes the source, changes identity, requires a new Git commit or invalidates operator trust must remain preserved; restart only on a different new synthetic project, never by unfreezing an old failed/frozen project. No synthetic evidence edits to force PASS.

Stop without approval if Full Non-Native FAIL/NOT_RUN, mismatched SHA/tree, wrong TLS peer, invalid independent signature, false source owner, port drift, failed restore or any AT FAIL. Final deliverable to the independent reviewer: a 15-row AT evidence table with exact files/sha256 and statuses, complete stdout/stderr hashes, all real commands and exit codes, signed observer IDs (not secrets), and remaining blockers. **Independent Review, Owner UAT, R01 and PR14/PR24 Merge remain separately NOT APPROVED** until explicitly signed off by their real authorities.
