# Project Status — v0.7.5 No-Actions Candidate (as of 2026-11-10)

**Current repo:** `Enochan222/sunrise-school-ai-platform` (private). The former IssacSitHk repository is abandoned as active project source and none of its history is carried forward.

| Item | Evidence-based state |
|---|---|
| Initial GitHub bootstrap PR #1 | Merged to `main` as `bfeb8d2a010c8b34f2ead71a9baa61801096ff94`; historical Actions success before Owner disabled Actions |
| Deliberate failing PR #2 | Failed as intended, closed unmerged; historical evidence only |
| `Protect main` | Active with PR/squash/no-bypass/deletion/force restrictions; no Required Status Checks after Owner chose no Actions |
| Original v0.7.5 source ZIP | SHA-256 verified, 149 entries, 148 file hashes |
| Adapted no-Actions Master Kit | **Merged via PR #8** on 2026-11-10, `main` `5506c5b9487563cf23cebcc1785061f09c12b50a`; 164/164 exact-source Git Blob/hash verification completed |
| S0 Owner architecture/signoff | PENDING |
| S1–S28 A/B/I/U runtime | NOT IMPLEMENTED / NOT DEPLOYED / NOT RUN |
| Provider API tests, real auth, real Restore, school PII | NOT RUN / NOT AUTHORIZED |

**Next:** finalise [S0 formal Owner architecture decisions](../decisions/STAGE0_APPROVAL_DECISIONS.md) and [S0 acceptance evidence](STAGE0_EVIDENCE_2026-11-10.md); import itself is **DONE**, not a blocker. S1 remains blocked until product signoff, with A-only deployment/Restore in its own Stage PR. Source audit now additionally pins the supplied upstream ZIP to official Open Notebook v1.15.1 (see S0 evidence).

The source v0.7.5 plan includes 29 Stages, 100 candidate APIs and 310 planned ATs; these are document designs and NOT LIVE tests. See [current Stage0 policy](NEW_REPO_STAGE0.md) and [Reuse-first audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md).
