# Sunrise Stage 1 [A] — Owner UAT Worksheet

**SOURCE TEMPLATE ONLY — NOT_RUN — NO OWNER SIGNOFF.** Fill privately after formal QA/reviewer authorisation, **never** with real student names/records, passwords, signed Cookies, JWTs or raw API responses.

## Run provenance

| Field | Value |
|---|---|
| Tested SHA (40 chars) | NOT_RUN |
| Git Tree (40 chars) | NOT_RUN |
| Review approval reference | NOT_RUN |
| Pinned ON commit/tree | `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239` / `2d101001de594c7d6a0e4aaeb8e85ac4c52980af` |
| SurrealDB version, image ID and immutable digest | NOT_RUN |
| Private Compose project/context/DB identity | NOT_RUN |
| Gateway SHA / Native patch SHA256 | NOT_RUN |
| Synthetic fixture manifest SHA256 | NOT_RUN |
| UTC start / end | NOT_RUN / NOT_RUN |
| Owner/reviewer reference (non-sensitive) | NOT_ASSIGNED |

## Owner observation checklist

| Check | Expected | Actual status (NOT_RUN/PASS/FAIL) | Redacted evidence filename or issue ID |
|---|---|---|---|
| Admin login/logout and anonymous denial | Session protected and revoked correctly | NOT_RUN | — |
| School A selector / Shell / unique Notebook | One trusted School and unique mapping | NOT_RUN | — |
| School A original PDF upload, Worker extraction | Hash retained, READY only if independently confirmed | NOT_RUN | — |
| A scoped English + Traditional Chinese text search | Only A Source result | NOT_RUN | — |
| Extended-Han text/no-vector overflow | Correct scoped fallback or explicit error, no embedding | NOT_RUN | — |
| Original download & archive | Original SHA matches; no hard delete | NOT_RUN | — |
| School B switch with CSRF rotation | Active School from server; old CSRF denied | NOT_RUN | — |
| B own Shell/Source and A/B reciprocal IDOR negatives | B cannot read A; A cannot read B | NOT_RUN | — |
| SourceOwner/Native Graph | Verified per School/Shell/Notebook/Source | NOT_RUN | — |
| DB+Worker restart | Same journal, source and original/readable index | NOT_RUN | — |
| Consistent Backup and isolated Restore | New target only; counts/keys/graph/bytes match | NOT_RUN | — |
| Raw Native/DB inaccessible outside private network | Negative test + identity proof | NOT_RUN | — |
| Service JWT allow, wrong Scope and wrong School deny | Independent signed fixture tokens | NOT_RUN | — |

## Issue record (repeat per failure)

- **Issue ID:** NOT_ASSIGNED
- **UTC timestamp:** NOT_RUN
- **Test step / School Context:** NOT_RUN
- **Exact tested SHA:** NOT_RUN
- **Expected observable result:** NOT_RUN
- **Actual result / HTTP status (no response secrets):** NOT_RUN
- **Minimal synthetic reproduction:** NOT_RUN
- **Redacted evidence filename + SHA256:** NOT_RUN
- **Severity (CRITICAL/HIGH/MEDIUM/LOW):** NOT_CLASSIFIED
- **Stop affected function?** UNDECIDED
- **Builder fix PR/Commit:** NONE
- **Independent retest result and revision:** NOT_RUN
- **Reviewer disposition:** PENDING

## Final Owner feedback

- **Usability of Admin Dashboard:** NOT_RUN
- **School switch clarity:** NOT_RUN
- **Search and PDF workflow clarity:** NOT_RUN
- **Unexpected duplicate/error/foreign data:** NOT_RUN
- **Owner UAT decision:** PENDING / NOT_RUN
- **Integration Reviewer formal AT status:** NOT_RUN
- **R01:** NOT_APPROVED

Owner UAT feedback is distinct from security, runtime, backup, restore and release acceptance. Do not copy this template's expected outcomes into a PASS result.
