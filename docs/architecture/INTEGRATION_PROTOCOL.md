# API-only Integration, Contract Freeze and Retry

S2 A publishes private idempotent `provision`, `manifest`, `attest`, `cutover-policy` endpoints with actual OpenAPI/Fixtures; S3 B publishes atomic `course-operations/reserve`, `finalize`, `quarantine`, `status/list`, unique binding, and Course CRUD. S4 I uses those two fixed contracts for explicit `ADOPT_EXISTING` or `CREATE_NEW` paths. I runtime cannot contain SurrealDB/Postgres root password, connection pool or DB migration. Egress firewall permits only internal HTTPS A/B hosts. Use S4 I API-level Core Reconciliation before ACTIVE, including independent A+B Restore/Status comparison. **S28 Dashboard is not a postponed consistency fix.**

S8 B generic optional Evidence acceptance and pre-use validation hook; S9 I implements bundle issuance/validation against A Source Version and B Binding. B cannot treat a signed but withdrawn/expired Source as valid; see [Evidence Bundle](EVIDENCE_BUNDLE.md). S22 B Staff Grants and revocation API; S23 I read-only Teacher A Source after per-call B Grant check and source-owner verification. A/B APIs may be called for ordinary business effects; I may never write their DB directly.

If a required API changes incompatibly: stop the I Stage, create separate earlier A or B Stage release, freeze new contract and rerun consumer tests, **then** return to I. Document status/Issue/Release Matrix rather than patch two systems inside I. No auto-delete Notebook compensation for partial creates. Use stable op key/request hash, B durable log and A creation record. See [S4 state machine](PROVISIONING_STATE_MACHINE.md).


## v0.7.4 School scope and lifecycle handoff

S4 I may only consume S2 A and S3 B contracts; read School IDs, Course grain, Group-to-Course relation, mutable operation state and Source Owner from authoritative APIs. It must reject mismatched school/stream and never auto-map same-name classes; ADOPT existing and CREATE new are separate paths. S26 A and S27 B each publish authenticated read-only Health/Backup/Restore status for I S28. I does not run a backup or SQL/SurrealDB query. Repeated Evidence validation is permitted ONLY for the same job, see [Evidence Revalidation](EVIDENCE_REVALIDATION.md).
