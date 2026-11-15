# Native CI / PR28 — UID/GID caller boundary repair evidence

Tested workflow repair revision: `61fc42a0c24fdcfdfb0c958f707337486cbdb65f`, tree `b4c4e3c9fa7063cf3cf254b7e885493c21b4070a` (same content as local ebc61609591343449e0ad17634ace8b99e340f4a). Parent main: c278ec600754fdb002ae1fb3a3959c54898922b5. These are tested source identities, not this evidence document's Final PR Head. Keep this workflow repair separate from PR14. No main overwrite, auto-merge, budget change or hosted deployment.

## Reproduction and correction

Bootstrap exports image UID/GID only in its child shell. Subsequent caller relay verification therefore cannot parse Compose. Actual pinned-image boundary comparison reproduced original exit1, fixed exit0; wrong digest was rejected exit1. The correction resolves the exact image ID in the caller via the existing digest-attested image-account verifier and exports all four A/ON UID/GID values before bootstrap. Missing runtime/verifier files, invalid identity and unsafe digest fail closed.

## Actual checks

- Product Python 3.11.11 `-m pytest -q scripts/test_stage1_native_workflow.py scripts/test_stage1_ci_policy.py`: 54 passed, exit0 (10 Native +44 existing Light policy cases).
- Fresh-context independent agent: Product Python `-m pytest scripts/test_stage1_native_workflow.py tests/stage1/test_surreal_image_user_contract.py -q`: 40 passed, exit0. Both actual workflow run-blocks passed `bash -n`. Removing A or ON caller exports was detected by actual positive contract tests. [Raw contract output](artifacts/pr28-contract-tests.log).
- Fresh reviewer inspected main-only/manual dispatch, exact SHA/digest validation, read-only token, no persisted checkout credential, synthetic masked secrets, upstream source/tree pin and private/loopback relay boundaries. No new confidence>=80 actionable issue in reviewed diff. This is agent technical review, not human GitHub approval.
- Earlier actual Mac Docker workflow tail, extracted from repaired YAML: caller exports -> dual DB bootstrap -> three loopback relay checks -> Native health -> synthetic PDF/worker/extraction/original hash/scoped BM25/Chinese search/foreign-notebook denial PASS, exit0. Local adaptations were explicit Docker context, unique project/paths and installed pinned driver requirements. This was not the GitHub-hosted Ubuntu job.
- Combined integration Tested Revision a547e089cae027999fb2854837b533ede24d05b6, tree5c7260fee0e7486861de015085bc97c90410165f: 490 full pytest,476 Stage1,54 workflow; Governance/verify_kit/compile/Node/dependencies/diff-check all exit0.

## Bounds and current state

Exactly the existing Native workflow, caller regression and manifest are repaired; this later evidence-only publication adds this report/log and their manifest entries. No executable source changes are introduced by the evidence update. Light trigger, Native manual dispatch, token permissions, timeout, Owner $0 budget/Stop Usage and no-delete-volume boundary stay intact.

GitHub-hosted Native execution **NOT_RUN**. Native smoke cannot stand in for formal S1-AT01–15, Gateway TLS/observer, ACK-loss, cold restore, Owner UAT or R01. Owner accepted a separate local integration UAT in the Codex chat; it does not authorize this PR's merge or hosted workflow dispatch. Human release review remains PENDING; R01 NOT_APPROVED. No full private logs, keys, credentials, backups or user PDFs are uploaded here.

This is a source-dependent workflow: if selected target_ref lacks PR14 dual-DB runtime files, it must fail closed; main alone at this baseline is not assumed to contain them. A reviewer must choose the exact authorized runtime source only after source/patch/dependency checks. No fallback to the obsolete single DB path.
