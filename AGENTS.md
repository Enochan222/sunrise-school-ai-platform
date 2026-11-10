# Sunrise AI Development Rules — Stage 0

1. Read README.md, stage0/STAGE0_BASELINE.json, docs/delivery/STAGE0_CHECKLIST.md. The v0.7.5 Master Kit is NOT yet present; never infer its 149 files from earlier chat messages or substitute an older v0.7 ZIP.
2. Use ONLY `Enochan222/sunrise-school-ai-platform`; never import the old IssacSitHk repository history.
3. Stage S0 is documents only. Later stages have one runtime owner each (A, B, I, U). A uses existing Open Notebook document processing/search with added school-scope policy; B owns official school records/grade ledger/AI jobs; I uses APIs only; U is an API consumer.
4. AI may draft and test code, push a feature branch and open a PR. There is no required human code review, but the GitHub Actions check must actually execute and pass. Never claim tests, Restore or a deployment succeeded without recorded evidence.
5. Do not directly push to main, bypass rules, use `pull_request_target` on untrusted code, expose service keys, import student data or charge paid cloud services without the owner's specific approval.
6. CI green in `BOOTSTRAP_ONLY` is NOT Master Kit acceptance. Actual v0.7.5 archive must be imported/verified, its full tests run, and required status checks enforce before individual PR auto-merge is enabled.
7. The owner makes product, school privacy, legal, budget and irreversible-release decisions, not technical code reviews.
