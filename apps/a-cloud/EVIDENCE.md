# Current fixed-password Cloud trial — 2026-11-18

Owner explicitly approved password-only login for this dedicated synthetic
trial. Owner reported applying the scoped SQL opt-in. Runtime source:
`1355d31a74d15c39a323bcfd9796c901d6d005f7`; Vercel deployment:
`dpl_48uJ1UbuNtct3VKLNwVpANnLF1zi`.

URL: https://sunrise-stage1-trial.vercel.app

Live HTTPS checks PASS: fixed password directly opens the library without MFA
or forced password change, existing Shell/Notebook visibility, Chinese scoped
search, original PDF SHA256, wrong-password/anonymous/CSRF rejection, logout
and stale-cookie rejection. See [live evidence](evidence/20261118/fixed-password-live.json)
and [28-test local result](evidence/20261118/fixed-password-tests.log).
No credential values are included. The access handoff file is private, outside
Git. This is synthetic single-Admin trial usability, not a formal Native R01
rerun, hosted Auth DR or permission to use real school/student data.

The following section is the historical preparation snapshot. Its earlier
NOT_RUN/approval-pending statements do not describe this deployed trial.

---

# Cloud trial preparation — 2026-11-17

Tested implementation revision: `10c0e69a8329953aa6d2763228b791da97934445`.
Base main: `fbc25e365955170ef9c4d00200f1e148b3ea1148`.
Source hashes: [manifest](evidence/20261117/tested-files-sha256.json).
Owner authorized the separate A-only, synthetic, zero-incremental-cost
Supabase/Vercel adaptation and routine implementation/deployment decisions.
This does not amend historical local Native acceptance or its formal ATs.

| Gate | Result | Observed evidence |
| --- | --- | --- |
| Dedicated IDEA Supabase project | PASS | `sunrise-stage1-trial`, `bnepekozzgymbvbjtltb`, FREE; preflight zero business tables/buckets/storage policies; pgcrypto in extensions; one newly created synthetic Auth user |
| Schema and single Admin binding | PASS | Transactional migration applied in authenticated project SQL editor; success; one private Admin, two synthetic scopes; Data API enabled; public/anonymous signups disabled |
| Python3.12 adapter tests | PASS | [25 tests](evidence/20261117/test-cloud-final.log), actual PostgreSQL17 policy/RPC fixture under service_role, PDF parser, HTTP pipeline, races, integrity and negatives |
| Previous Stage1 regression | PASS | [496 tests](evidence/20261117/regression.log) |
| Manual documents/contracts/mutations | PASS | [QA result](evidence/20261117/manual-qa-r2.log) |
| Real Supabase provider flow | PASS | [25 observed steps](evidence/20261117/hosted-provider-smoke.json), 2026-11-17T10:54:13Z–10:55:09Z: password, TOTP, Shell/Notebook, encrypted original, scoped search, original SHA, logout/relogin and MFA |
| Revoked cookie replay | PASS | Actual old cookie replay denied403; pending MFA business request denied401; final logout200 |
| Anonymous bypass negatives | PASS | [Direct provider evidence](evidence/20261117/provider-direct-negatives.json): tables404, RPC401, authenticated/public original requests400 |
| Limited A logical restore | PASS | [Restore](evidence/20261117/logical-restore.json): one hosted Shell/Source snapshot, saved encrypted blob and saved key/config reloaded, restored into separate local PostgreSQL database; same IDs/hash/rights/search |
| Vercel deployment and HTTPS runtime | NOT_RUN | No deployment or usable public URL yet; exact project secret-export approval pending |
| Actual browser full workflow | NOT_RUN | No deployed browser JavaScript, QR, cookie transport, upload/download evidence yet |
| Real password change / activation | NOT_RUN | Forms and handlers implemented; provider positive/negative/relogin tests remain |
| Hosted Auth disaster recovery | NOT_VERIFIED | Local restore reconstructs simplified Auth fixture and synthetic session; not provider Auth DR or full project restore |
| Original accepted Mac runtime | PRESERVED | Read-only container check: original six containers remain Exited; no start/rebuild/reinitialization, volume/key/backup changes |

The provider smoke uses the local FastAPI TestClient calling **real** Supabase
Auth/PostgREST/Storage. It does not prove Vercel ingress, serverless execution,
runtime payload/resource limits or browser behavior. The logical restore covers
the named earlier recovery point, not all records later added by repeated smoke
runs. Historical R01/15-case results are neither rerun nor relabeled.

One actual provider defect was found by stale-cookie replay: a numeric Auth
error code caused TypeError. The adapter now preserves denial for numeric,
string, null and non-object error bodies; four regression cases and a real
replay403 verify the correction. Independent sequential code and evidence
reviews found no remaining P1/P2 in the reviewed preparation scope; reviewers
did not claim independently rerunning hosted mutations.

## Executed commands

Private test root: `/private/tmp/sunrise-supabase-cloud-20261117` (`T` below).
Private configuration, passwords, MFA secrets, original bytes and keys are
outside Git with restricted permissions; no secret values are in this record.

```sh
CLOUD_TEST_DSN="host=$T/socket port=60437 dbname=sunrise_cloud_test_final" "$T/venv312/bin/python" -m pytest apps/a-cloud/test_cloud.py -q
/private/tmp/sunrise-final-r01-repaired-20261115/product/bin/python -m pytest tests/stage1 -q
"$T/venv312/bin/python" scripts/run_qa_no_actions.py
"$T/venv312/bin/python" apps/a-cloud/verify_hosted.py "$T/private"
"$T/venv312/bin/python" apps/a-cloud/verify_restore.py "$T/private" "host=$T/socket port=60437 dbname=sunrise_cloud_real_restore_r3"
docker ps -a --filter label=com.docker.compose.project=sunrise-s1-final-r01-f58c825fd9 --format '{{.ID}} {{.Names}} {{.Status}}'
```

PostgreSQL test service is private Unix socket only, TCP disabled, separate
directories/databases. Each SQL campaign/restore used a fresh database and
preserved previous artifacts. No original runtime service was started.

## Deployment blocker and rollback

Vercel project `prj_6eqjMLg2zXquX2LvAhw2dNvNPUmJ` has not received the
new trial provider service credential or Cloud encryption key. Automatic
approval review explicitly rejected that export pending specific Owner
authorization. Do not bypass via CLI/browser or deploy a placeholder.

Before publication, finish Vercel/runtime/browser/password gates and save a
current recovery point. On the first deployment there is no earlier verified
Cloud deployment: rollback must restrict traffic to an authenticated maintenance
response while retaining project/data/keys. Later rollback may select the prior
verified deployment. Never reset/delete tables, originals or historical Mac
volumes. Main integration remains blocked by applicable NOT_RUN gates.

Overall hosted trial verdict: **NOT_VERIFIED**. No public usable URL is claimed.
