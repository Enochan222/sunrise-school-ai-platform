"""Synthetic RSA tokens must be minted at AT14 time, not at suite startup."""
from __future__ import annotations

import sys
from datetime import datetime,timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
from make_synthetic_service_jwt import build_tokens


def _claims(token,public,now):
    return jwt.decode(token,public,algorithms=['RS256'],
                      issuer='synthetic-issuer',audience='synthetic-audience',
                      options={'require':['sub','iss','aud','exp','iat','nbf','jti',
                                          'school_id','scope']},
                      leeway=5)


def test_just_in_time_rs256_positive_and_all_negatives():
    private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public=private.public_key().public_bytes(serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    now=int(datetime.now(timezone.utc).timestamp())
    fixture=build_tokens(private,'synthetic-issuer','synthetic-audience',
                         'synthetic-school-a','synthetic-school-b',now)
    assert len(fixture)==8
    valid=_claims(fixture['VAULT_TEST_SERVICE_A'],public,now)
    assert valid['school_id']=='synthetic-school-a'
    assert valid['scope']=='vault.materials.read'
    assert valid['exp']-valid['iat']<=300
    assert _claims(fixture['VAULT_TEST_SERVICE_WRONG_SCOPE'],public,now)['scope'] != 'vault.materials.read'
    assert _claims(fixture['VAULT_TEST_SERVICE_FOREIGN_SCHOOL'],public,now)['school_id'] != valid['school_id']
    for label in ('EXPIRED','WRONG_AUDIENCE','INVALID_SIGNATURE',
                  'NOT_YET_VALID','MISSING_CLAIMS'):
        with pytest.raises(jwt.PyJWTError):
            _claims(fixture['VAULT_TEST_SERVICE_'+label],public,now)


def test_invalid_non_synthetic_input_fails_without_tokens():
    private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    with pytest.raises(ValueError):
        build_tokens(private,'issuer','audience','real-school','synthetic-school-b',1000000)
