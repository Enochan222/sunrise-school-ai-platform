# A-owned Supabase / Vercel trial

Owner explicitly requested this adaptation and its verification on 2026-11-17,
then delegated routine implementation/testing/deployment while away. Scope is
the new IDEA `sunrise-stage1-trial` project and the matching Vercel project,
synthetic material only, no additional spend. Historical local R01 acceptance,
its Native implementation and frozen volumes remain unchanged.

This is an A-only Cloud storage/execution variant, not B's Supabase database.
It replaces the SurrealDB/Native runtime with transactional A PostgreSQL RPCs
and private encrypted originals. Notebook/Source identifiers and the existing
A HTTP/UI contracts are retained. It does not claim the original Native ATs
ran against PostgreSQL. Provider tests, restore and security evidence are
recorded independently before a release claim.

Reuse assessment: inspected Open Notebook5e285b7's
`open_notebook/graphs/source.py` and its locked content-core2.2.1
`content_core/processors/document/pdf.py`. This trial uses the same pinned
pdfplumber0.11.10 PDF parser with bounded text extraction; no external AI,
OCR, URL fetching, vector provider or new general ingestion engine. Extraction
runs synchronously within a bounded Vercel invocation. Empty/scanned PDFs fail
explicitly. Originals are preserved before an operation becomes READY.

Auth is Supabase password plus TOTP MFA, with encrypted HttpOnly cookies and
CSRF. A single server-configured Admin UUID and private DB allowlist are both
required; public signup cannot confer A access. All business tables are in an
unexposed private schema. The server verifies JWT signatures, issuer, audience, expiry and current Auth
user before using this dedicated A project’s server-only service key. Narrow
private RPCs independently check live Auth session, AAL2, active school and
rotating CSRF before touching data. Authenticated/anonymous clients cannot
execute these RPCs or query private tables. No general Notebook CRUD/global-search/delete routes.

The private Storage bucket has no anonymous/authenticated policies. The A
server inserts only reserved originals and never overwrites or deletes them. App-encrypted bytes are never served as a
public URL. Download authenticates and rechecks scope before and after fetching,
decrypts, and verifies the original SHA256 before emitting any bytes.

Trial limit:3MiB born-digital PDF,100pages,1MiB extracted text. The smaller
upload bound keeps requests within the hosting provider's payload limits.
Free-tier availability/quota and synthetic-only use must be visible in the UI.
This is not an always-on SLA or real-school-data release.

For a first deployment there is no prior verified Cloud deployment: rollback
restricts traffic to an authenticated maintenance response. Later rollback can
select the previous verified deployment. Retain all Cloud tables, originals,
keys and evidence. Never delete/reset the project, bucket, historical test data
or original Mac volumes as rollback. See EVIDENCE.md for actual completed and
pending gates; a prepared adapter is not a verified deployed website.
