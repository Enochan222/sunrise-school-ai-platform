#!/usr/bin/env python3
"""Prove a dynamic host loopback relay, not a direct DB/Worker publish.

Pure inspect-contract validator plus a CLI querying the selected Compose project.
No Docker secrets/Env/Args are written to evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess

TARGETS = {
    "a_db": ("a_relay", "8000/tcp", "a_db_private", 8000),
    "on_db": ("on_relay", "8000/tcp", "on_db_private", 8000),
    "native": ("native_relay", "5055/tcp", "on_db_private", 5055),
}
SHA = re.compile(r"sha256:[a-f0-9]{64}\Z")
CID = re.compile(r"[a-f0-9]{64}\Z")


def require(value, message):
    if not value:
        raise RuntimeError(message)


def inspect_port_pair(service, backend, relay, project, native_image):
    """Reject public bindings, backend publish, wrong networks and foreign relay."""
    require(service in TARGETS, "Unexpected service name")
    relay_name, port_name, private_leaf, port = TARGETS[service]
    network = project + "_" + private_leaf
    publishing = project + "_loopback_publish"
    require(isinstance(backend, dict) and isinstance(relay, dict),
            "Malformed Docker identity")
    for name, item in ((service, backend), (relay_name, relay)):
        label = item.get("Config", {}).get("Labels", {})
        require(label.get("com.docker.compose.project") == project
                and label.get("com.docker.compose.service") == name,
                "Foreign Docker project/service identity")
        require(CID.fullmatch(str(item.get("Id", ""))) is not None,
                "Missing actual Docker container ID")
        require(item.get("State", {}).get("Running") is True,
                "Expected running private service/relay")
    backend_networks = backend.get("NetworkSettings", {}).get("Networks") or {}
    relay_networks = relay.get("NetworkSettings", {}).get("Networks") or {}
    require(set(backend_networks) == {network}
            and set(relay_networks) == {network, publishing},
            "Private DB/Native network isolation changed")
    require(backend_networks[network].get("NetworkID")
            == relay_networks[network].get("NetworkID"),
            "Relay connected to wrong private engine")
    require(not any(x for x in (backend.get("NetworkSettings", {}).get("Ports") or {}).values() if x),
            "DB/Native service directly published a host port")
    require(not any(x for x in (backend.get("HostConfig", {}).get("PortBindings") or {}).values() if x),
            "DB/Native has unexpected host port binding configured")
    require(relay.get("Image") == native_image
            and SHA.fullmatch(str(native_image)) is not None,
            "Relay image differs from pinned built Native image")
    require(relay.get("HostConfig", {}).get("ReadonlyRootfs") is True
            and relay.get("HostConfig", {}).get("SecurityOpt") is not None,
            "Relay not running with immutable filesystem/security controls")
    require(relay.get("Config", {}).get("Entrypoint")
            == ["/app/.venv/bin/python", "-I", "/relay.py"],
            "Unexpected relay executable")
    require(relay.get("Config", {}).get("Cmd")
            == ["--role", service, "--listen", str(port)],
            "Unexpected relay destination/command")
    require(not any(x.get("Type") == "volume" for x in relay.get("Mounts", [])),
            "Relay must not inherit database or Native volumes")
    bindings = relay.get("NetworkSettings", {}).get("Ports") or {}
    require(set(k for k,v in bindings.items() if v) == {port_name},
            "Relay missing/extra dynamic host binding")
    record = bindings[port_name]
    require(isinstance(record, list) and len(record) == 1,
            "Relay host port ambiguous")
    require(record[0].get("HostIp") == "127.0.0.1"
            and re.fullmatch(r"[0-9]{4,5}",str(record[0].get("HostPort", ""))),
            "Relay published outside exact IPv4 loopback")
    host_port = int(record[0]["HostPort"])
    require(1024 <= host_port <= 65535,
            "Relay mapped invalid host port")
    hc = relay.get("HostConfig", {}).get("PortBindings") or {}
    require(set(hc) == {port_name}
            and isinstance(hc[port_name],list) and len(hc[port_name]) == 1
            and hc[port_name][0].get("HostIp") == "127.0.0.1",
            "Configured relay host binding differs from runtime")
    return {"service":service,"relay":relay_name,"port":host_port,
            "relay_container_id":relay["Id"],"relay_image_id":relay["Image"],
            "private_network_id":relay_networks[network]["NetworkID"],
            "publish_network_id":relay_networks[publishing]["NetworkID"]}


def run(context, *args):
    return subprocess.run(["docker","--context",context,*args],capture_output=True,
                          text=True,check=True,timeout=30).stdout.strip()


def verify(context,project,compose_file,service):
    require(re.fullmatch(r"[A-Za-z0-9_.-]{1,64}",context) is not None,
            "Invalid Docker context")
    require(re.fullmatch(r"sunrise-s1-[a-z0-9-]{8,40}",project) is not None,
            "Foreign synthetic Compose project")
    require(service in TARGETS,"Unknown host port request")
    relay, _, private_leaf, _ = TARGETS[service]
    cmd=("compose","-p",project,"-f",str(compose_file))
    backend_id=run(context,*cmd,"ps","-q",service)
    relay_id=run(context,*cmd,"ps","-q",relay)
    require(CID.fullmatch(backend_id) and CID.fullmatch(relay_id),
            "Missing real Compose backend/relay container")
    backend,relay_item=json.loads(run(context,"inspect",backend_id,relay_id))
    native_image=run(context,"image","inspect",
                     "sunrise-on-s1-v1.15.1-text-only:local","--format","{{.Id}}")
    proof=inspect_port_pair(service,backend,relay_item,project,native_image)
    for leaf, internal in ((private_leaf,True),("loopback_publish",False)):
        name=project+"_"+leaf
        network=json.loads(run(context,"network","inspect",name))[0]
        require(network.get("Name")==name
                and network.get("Internal") is internal
                and network.get("Driver")=="bridge"
                and network.get("Labels",{}).get("com.docker.compose.project")==project,
                "Wrong private/publish Docker network")
        expected=proof["private_network_id" if internal else "publish_network_id"]
        require(network.get("Id")==expected,"Network ID mismatch")
    compose_port=run(context,*cmd,"port",relay,str(TARGETS[service][3]))
    require(compose_port=="127.0.0.1:"+str(proof["port"]),
            "Compose port differs from actual inspected binding")
    return proof


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--context",required=True)
    parser.add_argument("--project",required=True)
    parser.add_argument("--compose-file",required=True)
    parser.add_argument("--service",choices=tuple(TARGETS),required=True)
    args=parser.parse_args()
    proof=verify(args.context,args.project,args.compose_file,args.service)
    print(json.dumps(proof,sort_keys=True))


if __name__=="__main__":
    main()
