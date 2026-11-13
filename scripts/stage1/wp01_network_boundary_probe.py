#!/usr/bin/env python3
"""WP01 independent-network negative probe · IMPLEMENTED_UNTESTED.

This probe MUST be launched from an independently isolated synthetic observer,
NOT from the Docker host or a native container. It only checks private TCP
listeners for non-reachability; it does not send secrets or privileged requests.
A PASS here is NOT sufficient to establish public ingress/firewall correctness.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from ipaddress import ip_address
import json
from pathlib import Path
import socket
import sys


def utc():
    return datetime.now(timezone.utc).isoformat()


def validate_ip(name):
    try:address=ip_address(name)
    except ValueError as e:raise ValueError('Numeric observer destination required') from e
    if address.is_loopback or address.is_unspecified or address.is_multicast or address.is_link_local:
        raise ValueError('An external isolated destination must not be loopback/metadata/link-local')
    if not address.is_private:
        raise ValueError('Only isolated private-network synthetic targets are permitted')
    return str(address)


def unreachable(ip,port,timeout):
    try:
        with socket.create_connection((ip,port),timeout=timeout):
            return False,'TCP_ACCEPTED'
    except (TimeoutError,ConnectionRefusedError,OSError) as exc:
        return True,type(exc).__name__


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--target-private-ip',required=True)
    parser.add_argument('--observer-id',required=True)
    parser.add_argument('--out',type=Path,default=Path('wp01-boundary-redacted.json'))
    parser.add_argument('--timeout',type=float,default=2.0)
    args=parser.parse_args()
    target=validate_ip(args.target_private_ip)
    if not args.observer_id.strip() or args.timeout<=0 or args.timeout>10:
        raise ValueError('Observer identity and bounded timeout required')
    import os
    if os.getenv('VAULT_OBSERVER_ISOLATED_CONFIRM')!='YES':
        print('RUNTIME_NOT_RUN: independent observer network not confirmed',file=sys.stderr)
        raise SystemExit(69)
    checks={}
    evidence={'start_utc':utc(),'classification':'WP01_EXTERNAL_NETWORK_NEGATIVE',
              'observer_identity':args.observer_id,'target_private_ip':target,
              'ports':{},'S1_AT02_07':'NOT_RUN'}
    try:
        for name,port in [('native_api',5055),('surrealdb',8000),
                          ('native_ui',8502),('gateway_local_dev',8765)]:
            denied,detail=unreachable(target,port,args.timeout)
            checks[name]=denied
            evidence['ports'][name]={'port':port,'inaccessible':denied,'reason':detail}
        evidence['status']='PASS' if all(checks.values()) else 'FAIL'
    except Exception as e:
        evidence['status']='FAIL';evidence['error_type']=type(e).__name__
        raise
    finally:
        evidence['end_utc']=utc()
        args.out.write_text(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    if evidence['status']!='PASS':
        raise SystemExit('FAIL: Native/DB/UI/Gateway port reachable from isolated observer')
    print('WP01 external-port negative PASS: still requires full HTTP/role/network provenance review')


if __name__=='__main__':
    main()
