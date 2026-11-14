#!/usr/bin/env python3
"""Generate ephemeral synthetic RS256 Service JWT fixtures for S1-AT14.

Must run BEFORE starting the synthetic Gateway. Never commit the output.
Nothing sensitive is printed to stdout. All generated files are mode 0600.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def build_tokens(key, issuer: str, audience: str, school_a: str,
                 school_b: str, now: int) -> dict[str,str]:
    """Fresh synthetic claims, signed at actual AT14 execution, never logged."""
    if (not issuer or not audience or school_a == school_b
            or not all(s.startswith('synthetic-') for s in (school_a,school_b))):
        raise ValueError('Invalid synthetic JWT identity fixture')
    other = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    base = dict(sub='synthetic-at14-service', iss=issuer, aud=audience,
                exp=now+240, iat=now-10, nbf=now-10,
                jti='synthetic-at14-'+str(now), school_id=school_a,
                scope='vault.materials.read')
    def sign(modifications=None, omit=(), signing_key=key):
        claims = {**base, **(modifications or {})}
        for name in omit:
            claims.pop(name, None)
        private = signing_key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        return jwt.encode(claims, private, algorithm='RS256')
    return dict(
        VAULT_TEST_SERVICE_A=sign(),
        VAULT_TEST_SERVICE_WRONG_SCOPE=sign({'scope':'vault.materials.write'}),
        VAULT_TEST_SERVICE_FOREIGN_SCHOOL=sign({'school_id':school_b}),
        VAULT_TEST_SERVICE_EXPIRED=sign({'iat':now-400,'nbf':now-400,'exp':now-160}),
        VAULT_TEST_SERVICE_WRONG_AUDIENCE=sign({'aud':audience+'-wrong'}),
        VAULT_TEST_SERVICE_INVALID_SIGNATURE=sign(signing_key=other),
        VAULT_TEST_SERVICE_NOT_YET_VALID=sign({'nbf':now+120}),
        VAULT_TEST_SERVICE_MISSING_CLAIMS=sign(omit=('jti',)),
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', required=True, type=Path)
    p.add_argument('--issuer', required=True)
    p.add_argument('--audience', required=True)
    p.add_argument('--school-a', required=True)
    p.add_argument('--school-b', required=True)
    args = p.parse_args()
    if (not args.issuer.strip() or not args.audience.strip()
            or args.school_a == args.school_b
            or not all(x.startswith('synthetic-') for x in (args.school_a,args.school_b))):
        p.error('Explicit synthetic issuer/audience and distinct schools required')
    out = args.out_dir
    if out.exists():
        p.error('Refuse to reuse or overwrite any existing fixture directory')
    out.mkdir(mode=0o700, parents=False)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    pem = key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    def save(name: str, data: bytes):
        fd = os.open(out/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as file:
            file.write(data)
    save('service_test_private.pem', pem)
    save('service_test_public.pem', public)
    now = int(datetime.now(timezone.utc).timestamp())
    tokens = build_tokens(key, args.issuer, args.audience, args.school_a, args.school_b, now)
    save('service_test_tokens.env', ''.join(k+'='+v+'\n' for k,v in tokens.items()).encode())
    print('SYNTHETIC_AT14_FIXTURES_CREATED; tokens and keys withheld from stdout')


if __name__ == '__main__':
    main()
