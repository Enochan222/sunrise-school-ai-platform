# Original Uploaded v0.7 → Reviewed v0.7 Stage Migration Crosswalk

**The original uploaded kit has Stage S0–S23 and 149 designed ATs. This reviewed kit has a different planned sequence.** Old IDs stay historical; GitHub work branches/Issues must be mapped by **function**, not blindly rename without owner review.

| Previous ZIP Stage | Reviewed Stage | Owner | Meaning / reason |
|---|---|---|---|
| S0 | **S0** | P | Planning Baseline & Security Decisions |
| S1 | **S1** | A | Secure Open Notebook Vault |
| S2 | **S2** | A | Versioned Content Catalog & A Contract Freeze |
| S3 | **S3** | B | Independent Academic Course & B Contract Freeze |
| S7 | **S4** | I | Course–Content Linking & Core Recovery |
| S8 | **S5** | U | Sunrise Course & Content Admin Portal |
| S9 | **S8** | B | Durable Generation Queue & Draft Review |
| S10 | **S9** | I | Version-pinned Notebook Evidence Bridge |
| S12 | **S11** | B | Mathematics Paper Builder & PDF |
| S15 | **S12** | B | Chinese Language Paper Adapter |
| S22 | **S13** | B | English Language Paper Adapter |
| S23 | **S14** | B | General Studies Paper Adapter |
| S4 | **S15** | B | Synthetic Student Roster |
| S5 | **S16** | B | Assessment & Score Drafts |
| S6 | **S17** | B | Append-only Grade Events & Corrections |
| S13 | **S18** | B | Submissions & Manual Marking |
| S14 | **S19** | B | AI-assisted Marking Benchmark & Review |
| S11 | **S20** | B | Deterministic Analytics & Weakness Keep-two |
| S16 | **S22** | B | Staff IAM, Grants & B Authorization |
| S17 | **S23** | I | Teacher Read-only Course Content |
| S18 | **S25** | B | Approved Real Student Data Gate |
| S19 | **S26** | A | Content Retention & Annual Archive Tools |
| S20 | **S27** | B | Academic Year Closing & Grade Retention |
| S21 | **S28** | I | Cross-service Health/Restore Dashboard |


New reviewed Stages without previous counterpart: **S6 B Question/Rubric Contract Studio, S7 B AI Provider/Gemini Key Settings, S10 U Generation UI, S21 U Assessment/Analytics UI, S24 U Teacher Portal**. Old S7 I becomes S4; old S8 U becomes S5; old S9 B Generation becomes S8; old S10 I Evidence becomes S9. S11–14 B launch the four distinct subject engines before Admin/Student management growth. S28 I is **Dashboard only**; minimum core reconciliation is S4.

## Prior AT mapping

See [legacy AT CSV](LEGACY_AT_MAPPING.csv). Old scenarios are carried as design intents where still valid; their Stage IDs are remapped and supplemented with new security/contract/TOCTOU/rollback cases, NOT marked executed. No evidence from original document-only 964 checks or 22 model tests transfers to real runtime acceptance.

## Safe live Repo approach

Existing `main` is v0.5; use [docs-only PR plan](GITHUB_BASELINE_PR_PLAN.md) to update current authority after reviewing live historical ADR/Issue/PR. Do not delete GitHub history or auto-merge this ZIP. Re-run CI and Owner approval.
