# Independent Backup and Restore, Early Rights Policy

**S1 A**: coordinated SurrealDB+Open Notebook/uploads/original files+Worker status backup under a consistent snapshot, filenames and SHA, secure recovery of encryption key from separate Secret Store. Real isolated A-only Restore with source version/owner/hash verification and Search/Download. Retention/AI-usage/copyright policy for school textbooks/notes/past-paper sources starts here. S2 immutable versions and cited old version retention, Archive vs Delete vs Revocation distinct; later S26 advanced Year Archive UI, NOT first rights policy decision.

**S3 B**: different database engine/credentials/network/project, its own migrations and backup/restore; Course Registry/operations must survive independent Restore. S7–S20 B artifacts, AI provider secret refs, Grade Ledger/rebuild and queue jobs backup as applicable; secret plaintext not in dumps. Later B S27 Year Close.

**S4 I**: S4 release has *minimum cross-store recovery drill*. Restore A and B **individually to isolated environments** using independent procedures, then use I API-only manifests to compare Course/Notebook/Source Hash, binding revision, operation log and epoch; mismatches fail READY and quarantine. This is not a single cross-DB atomic snapshot or authority for I to restore DBs itself. S28 extends dashboard/history only.

Rollback must consider schema compatibility: EXPAND→MIGRATE→CONTRACT and migration hashes, not assume app image downgrade works. For failures, freeze affected writes, keep last approved originals and Grade Events, reconcile forward when down migration is unsafe, record tested RPO/RTO. No invented guarantee of perfect recovery or synchronous consistent snapshots.


## S26/S27/S28 ownership clarity (v0.7.4)

A S26 `GET /vault/v1/health|backup-status` read-only with Vault service credential; B S27 `GET /core/v1/health|backup-status` separately scoped. I S28 may compare signed statuses, restore timestamps and hash manifests **only by these previously deployed APIs**. It cannot perform database Restore or store secret backup media. Owner-local actual Restore evidence remains mandatory and separate from I dashboard snapshots.
