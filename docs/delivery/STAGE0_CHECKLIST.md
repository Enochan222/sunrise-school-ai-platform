# Stage 0 — current acceptance state (no GitHub Actions)

- [x] Private fresh `Enochan222/sunrise-school-ai-platform`; old history not copied.
- [x] `Protect main` Active: PR-only/squash, no bypass, block deletion and force push.
- [x] Required GitHub Actions status check disabled per Owner decision; no GitHub Copilot.
- [x] Prior PR #1 passed actual historical GitHub Actions tests; prior deliberate negative PR #2 failed and was closed. **These are historic bootstrap observations, not a current automated gate.**
- [x] Exact original v0.7.5 archive verified locally; No-Actions adaptation built and local static QA passed.
- [ ] Entire adapted Master Kit actually imported into GitHub preserving paths and hashes.
- [ ] Full GitHub imported source verified again independently and 16 static test groups rerun against the exact PR commit.
- [ ] Pinned Docker QA container actually built and executed (not possible in current GPT sandbox without Docker).
- [ ] Owner confirms Course/TeachingGroup, A school ownership, S1 Gemini optional vs B S7, S4 Cutover, security/privacy, and cost boundaries.
- [ ] Stage0 product acceptance recorded with real evidence in Issue. **Stage 1 NOT STARTED.**

**Limit:** With no GitHub Actions or external CI, no server-enforced PR tests or automatic GPT trigger exist. Never claim a passing GPT comment automatically protects merges.
