"""S1 synthetic-only fail-start configuration. Production backend not yet verified."""
from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit
import os


@dataclass(frozen=True)
class Settings:
    admin_hash: str
    session_secret: str
    encryption_key: str
    school_id: str
    actor_id: str
    sqlite_file: str
    native_url: str
    native_password: str
    service_public_key: str = ""
    service_issuer: str = ""
    service_audience: str = ""
    session_secure: bool = False
    max_pdf_bytes: int = 8 * 1024 * 1024
    native_text_only_verified: bool = False  # Only enable after patched ON source + runtime evidence
    store_backend: str = 'surreal'  # Never default to synthetic SQLite in formal runtime
    surreal_ws_url: str = 'ws://127.0.0.1:8000/rpc'
    surreal_user: str = ''
    surreal_password: str = ''
    surreal_namespace: str = 'open_notebook'
    surreal_database: str = 'open_notebook' 

    def validate(self):
        if not self.admin_hash.startswith('$argon2id$'):
            raise ValueError('VAULT_ADMIN_PASSWORD_HASH must be a real Argon2id hash')
        if len(self.session_secret) < 32 or len(self.encryption_key) < 32:
            raise ValueError('Session and encryption secrets must each have at least 32 characters')
        if self.session_secret == self.encryption_key:
            raise ValueError('Session and encryption secrets cannot be equal')
        if not self.school_id or not self.actor_id:
            raise ValueError('Server-held school and actor identities required')
        if self.store_backend not in ('surreal','synthetic_sqlite'):
            raise ValueError('Unknown vault store backend')
        if self.store_backend == 'synthetic_sqlite':
            if not self.sqlite_file:
                raise ValueError('Synthetic journal path required')
        else:
            from surreal_store import SurrealConfig
            SurrealConfig(self.surreal_ws_url,self.surreal_user,self.surreal_password,
                self.surreal_namespace,self.surreal_database).validate()
        if not self.native_password or self.native_password in ('root','password','changeme'):
            raise ValueError('Native secret missing or unsafe')
        parsed = urlsplit(self.native_url)
        if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password or parsed.path.rstrip('/') not in ('',):
            raise ValueError('Native API must be a loopback-only local HTTP URL in synthetic mode')
        if self.max_pdf_bytes < 100 or self.max_pdf_bytes > 25 * 1024 * 1024:
            raise ValueError('Invalid PDF size limit')
        if any((self.service_public_key, self.service_issuer, self.service_audience)) and not all((self.service_public_key, self.service_issuer, self.service_audience)):
            raise ValueError('Service JWT verifier requires public key, issuer and audience together')
        return self


def from_env():
    keys=['VAULT_ADMIN_PASSWORD_HASH','VAULT_SESSION_SECRET','VAULT_ENCRYPTION_KEY',
          'VAULT_SCHOOL_ID','VAULT_ACTOR_ID','VAULT_NATIVE_URL','VAULT_NATIVE_PASSWORD']
    missing=[key for key in keys if not os.getenv(key)]
    if missing:
        raise ValueError('Missing required secrets/config: '+', '.join(missing))
    return Settings(admin_hash=os.environ['VAULT_ADMIN_PASSWORD_HASH'],session_secret=os.environ['VAULT_SESSION_SECRET'],
        encryption_key=os.environ['VAULT_ENCRYPTION_KEY'],school_id=os.environ['VAULT_SCHOOL_ID'],
        actor_id=os.environ['VAULT_ACTOR_ID'],sqlite_file=os.getenv('VAULT_SQLITE_FILE',''),
        native_url=os.environ['VAULT_NATIVE_URL'],native_password=os.environ['VAULT_NATIVE_PASSWORD'],
        service_public_key=os.environ.get('VAULT_SERVICE_PUBLIC_KEY_PEM','').replace('\\n','\n'),
        service_issuer=os.environ.get('VAULT_SERVICE_ISSUER',''),
        service_audience=os.environ.get('VAULT_SERVICE_AUDIENCE',''),
        session_secure=os.environ.get('VAULT_COOKIE_SECURE','false').lower()=='true',
        native_text_only_verified=os.environ.get('VAULT_NATIVE_TEXT_ONLY_VERIFIED','false').lower()=='true',
        store_backend=os.getenv('VAULT_STORE_BACKEND','surreal'),
        surreal_ws_url=os.getenv('VAULT_SURREAL_WS_URL','ws://127.0.0.1:8000/rpc'),
        surreal_user=os.getenv('VAULT_SURREAL_USER',''),
        surreal_password=os.getenv('VAULT_SURREAL_PASSWORD',''),
        surreal_namespace=os.getenv('VAULT_SURREAL_NAMESPACE','open_notebook'),
        surreal_database=os.getenv('VAULT_SURREAL_DATABASE','open_notebook')).validate()
