# R01 — Owner-approved local synthetic acceptance closeout

**Approval recorded:** 2026-11-15 15:45:45 UTC, separate human chat receipt.  **Scope:** R01 Stage 1 [A] **local isolated synthetic acceptance only**.

## Immutable payload and separated authorization

- [Original owner-approved release manifest](R01-release-manifest.json): SHA256 `7b335b921a9d08c26341b1099875bc7721af5edb0ace03dbebde9c351c52220d`. **Unmodified byte-for-byte**, including its earlier `AWAITING_OWNER` fields as a historical pre-signature state.
- [Original accepted operating policy receipt](R01-operating-policy-receipt.json): SHA256 `4156005350d0001dec7722821be0b4dc0762e159d5a89e553505b408227ab95b`.
- [Subsequent explicit Owner approval](R01-owner-human-signoff.json): a **human chat receipt**, not a cryptographic signature or proof of Windows private-key possession. The approval is bound to the two SHA256 values and the tested implementation.
- Tested implementation: `7ebe3d89e49ca5623030427c73804da12021552b`, tree `658d687edd7f63139db5750d0b8aea06b091acdd`.
- Docs-only publication baseline: `b024b12202400e142970b676d1dd24b05af7eaf4`, tree `a8617d094e4a74072ac50b1bc1b4036d701bc1c6` (PR #31).

## Technical and operational decision

The [source-bound technical acceptance report](../evidence/FINAL_ACCEPTANCE_MAIN_7ebe3d89.md) records actual S1-AT01–15 **15/15 PASS**, full pytest **500 PASS**, dedicated Stage 1 **486 PASS**, workflow contracts **54 PASS**, independent agent evidence review and real dual-DB/original restore. Earlier 14-PASS/AT13-FAIL is preserved; PR #30 repaired the validator and the latest full campaign passed. The latest Owner UAT was separately accepted. This documents **Owner GO for local synthetic R01 acceptance closeout**, not authorization to operate public, production or hosted services.

Bounded local operating conditions: existing Owner-managed Mac/private LAN in Hong Kong; $0; external AI OFF; synthetic data only; complete cold backup before acceptance mutations; retain evidence/volumes until separate deletion authorization; keys separate from backups/outside Git; restore latest verified cold snapshot. The observed **13.700125 seconds** measures DB restore through Native readback only, **not** complete Gateway availability RTO/SLA.

**Excluded / NOT AUTHORIZED:** hosted Native workflow dispatch (NOT_RUN), deployment/public hosting, paid resources, real school/student data, off-host disaster recovery, production service-level claims, and automatic Stage 2 authorization. The local Native image is an immutable local image ID, not a claimed registry digest. B/I/U remain unimplemented and unchanged.

## Review and merge controls

The source/candidate publication was independently reviewed as described in [PR #31](https://github.com/Enochan222/sunrise-school-ai-platform/pull/31), but **independent agent review is not human GitHub approval**. This signoff publication requires its **own** docs-only diff, manifest hash/coverage verification, pinned governance QA and `verify_kit.py`, reviewer decision and normal protected manual squash merge. No native runtime re-execution is claimed for documentation-only changes; raw evidence remains in the private Owner archive. Keep Issue #29's historical dated snapshot unchanged and attach the actual publication PR result there only after verification.
