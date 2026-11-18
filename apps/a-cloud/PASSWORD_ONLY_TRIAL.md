# Owner-approved fixed-password synthetic trial

On 2026-11-18 Owner explicitly approved: 「批准合成試用只用固定密碼」.
This exception applies only to the IDEA Supabase project
`bnepekozzgymbvbjtltb` and Vercel `sunrise-stage1-trial`, synthetic data only.
It does not amend historical local R01 acceptance or its MFA requirements.

Password-only access requires both `CLOUD_PASSWORD_ONLY_TRIAL=1` in this
dedicated app and the scoped private Admin DB opt-in. Signed JWT verification,
live session checks, single Admin identity, school/Notebook/Source ownership,
CSRF, private encrypted originals and original-hash verification remain active.
Other project URLs, real email identities and non-synthetic scopes fail closed.
The fixed trial password is Owner managed; the UI does not require or offer a
first-login password change. No password, token or MFA seed is included in Git.

The additional migration was generated with Supabase CLI2.81.3. Owner reported
executing it successfully in the dedicated project SQL Editor. The connector
does not have management permission for the new organization; no bypass was
used. The local clean PostgreSQL/HTTP suite passed28 tests, including app-only
and DB-only opt-in rejection, wrong-project and real-email rejection, password
login without MFA, anonymous denial and CSRF denial.

Rollback: unset the app flag and redeploy to require MFA again; the original
factor remains preserved. Disable the DB opt-in as well for immediate rejection
of AAL1 business requests. Preserve all data, originals, keys and backups.

Live fixed-password verification is recorded separately after deployment.
