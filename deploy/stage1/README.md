# Private GitHub Codespaces Stage 1 trial ingress

This is a temporary Owner-only Cloud trial adapter, not an always-running public
service or a new R01 acceptance campaign. Keep port 8000 **Private** in GitHub
Codespaces. GitHub authenticates access to that private forwarded port; the
unchanged A Gateway still owns its password/session/CSRF and Shell/Source rules.
Never publish the database, Native, relay or loopback Gateway ports.

The adapter requires `SUNRISE_TRIAL_HOST` set to the exact Codespaces HTTPS
port-8000 hostname and `VAULT_GATEWAY_CA_FILE` pointing to the newly generated
Cloud Gateway CA. It connects only to `https://127.0.0.1:18916`, verifies that CA,
rejects foreign Host/Origin/Fetch-Site before translating the approved Origin,
and forwards only Sunrise cookies. It preserves backend statuses, multiple
Set-Cookie headers, security policy, CSRF and idempotency headers. HTML labels
are changed from local synthetic to Cloud synthetic trial; no uploaded material
or original PDF bytes are changed. No GitHub/tunnel credential is forwarded to A.
Authorization headers are stripped; this Owner-only trial exposes Admin session
flows, not A ServiceToken integrations through the Cloud adapter.

The verified Codespaces tunnel rewrites Host to `localhost:8000` and supplies
the external hostname in `X-Forwarded-Host`. This form is accepted only from
the actual TCP loopback peer with exactly one approved forwarded hostname and
HTTPS protocol. Uvicorn proxy-header processing must stay disabled; arbitrary
forwarded headers, non-loopback peers and foreign browser origins are denied.

Run with the pinned A product environment:

```sh
python -m uvicorn codespaces_gateway:application --factory --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

Use the existing pinned-source A bootstrap only in a new, exclusive synthetic
Cloud project with its own fresh keys, three persistent Docker volumes and two
private networks. Preserve the original frozen Mac acceptance environment. Keep
secrets outside Git, mode 0600, in a mode-0700 directory on the Codespace's
persistent `/workspaces` filesystem. Do not print Docker Env/Args or credentials.
Record the application revision, ingress revision/hash, pinned Native source,
actual image digests, container/mount identities, UTC commands and smoke results.

Before delivery, verify private port visibility and actual authenticated login,
Shell/Notebook creation, PDF upload/worker completion, scoped search, downloaded
original SHA256 and logout/login. Include negative ownership/CSRF/origin checks,
Cloud regression, persistence and recovery evidence appropriate to this trial.
Unit tests with fake transport are ingress checks, never Native runtime proof.
Original formal S1-AT01–15 and Owner signoff remain bound to their historic SHA.

Codespaces can stop on idle and is constrained by the Owner's included compute
and storage. Preserve the existing $0 Codespaces budget/Stop Usage; do not enable
paid usage, keep-alive automation, Copilot, extra Actions workflows or auto-merge.
This ingress has **no independent public authentication**: public port visibility
is prohibited by this adapter's deployment contract. Public or end-customer
hosting requires separately reviewed authentication/MFA, durability and budget.

Rollback: stop this adapter and its exact new trial processes/containers. Retain
volumes, credentials and evidence; do not delete the Codespace or data by default.
