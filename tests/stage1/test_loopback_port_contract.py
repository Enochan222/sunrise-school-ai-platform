"""Port publication/physical network contract regressions (no Docker runtime).

Synthetic inspect dictionaries only. These tests cannot count as Mac TCP,
actual Docker Compose mapping, dual-DB RPC, Worker or Stage 1 Acceptance PASS.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/"scripts/stage1/loopback_port_contract.py"
IMAGE="sha256:"+"a"*64
PROJECT="sunrise-s1-safe-test123"


def load():
    spec=importlib.util.spec_from_file_location("stage1_loopback_port",MODULE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(service="a_db"):
    names={"a_db":("a_relay","a_db_private",8000),
           "on_db":("on_relay","on_db_private",8000),
           "native":("native_relay","on_db_private",5055)}
    relay,leaf,port=names[service]
    private=PROJECT+"_"+leaf
    publish=PROJECT+"_loopback_publish"
    project_label="com.docker.compose.project"
    service_label="com.docker.compose.service"
    def base(name,container_id):
        return {
            "Id":container_id,
            "State":{"Running":True},
            "Config":{"Labels":{project_label:PROJECT,service_label:name}},
            "NetworkSettings":{"Networks":{},"Ports":{}},
            "HostConfig":{"PortBindings":{}},
        }
    backend=base(service,"b"*64)
    backend["Config"]["User"]="65532:65532"
    backend["NetworkSettings"]["Networks"]={private:{"NetworkID":"c"*64}}
    relay_doc=base(relay,"d"*64)
    relay_doc["Image"]=IMAGE
    relay_doc["Config"]["User"]="65532:65532"
    relay_doc["NetworkSettings"]["Networks"]={
        private:{"NetworkID":"c"*64},
        publish:{"NetworkID":"e"*64}}
    relay_doc["NetworkSettings"]["Ports"]={
        f"{port}/tcp":[{"HostIp":"127.0.0.1","HostPort":"48920"}]}
    relay_doc["HostConfig"].update({
        "PortBindings":{f"{port}/tcp":[{"HostIp":"127.0.0.1","HostPort":"48920"}]},
        "ReadonlyRootfs":True,
        "SecurityOpt":["no-new-privileges:true"],
        "CapDrop":["ALL"],
    })
    relay_doc["Config"].update({
        "Entrypoint":["/app/.venv/bin/python","-I","/relay.py"],
        "Cmd":["--role",service,"--listen",str(port)],
    })
    relay_doc["Mounts"]=[{"Type":"bind","Destination":"/relay.py","RW":False}]
    return backend,relay_doc


@pytest.mark.parametrize("service",("a_db","on_db","native"))
def test_only_loopback_relay_published_and_private_service_unpublished(service):
    mod=load()
    backend,relay=fixture(service)
    result=mod.inspect_port_pair(service,backend,relay,PROJECT,IMAGE)
    assert result["port"]==48920
    assert result["relay_container_id"]=="d"*64
    assert result["private_network_id"]=="c"*64


@pytest.mark.parametrize("change",(
    "public_host","no_host_port","extra_host_port","missing_host_port",
    "backend_published","backend_hostconfig_binding",
    "wrong_private_network","backend_on_publish_network",
    "relay_off_private_network","relay_wrong_private_network_id",
    "relay_wrong_publishing_network","relay_wrong_image",
    "relay_wrong_project","relay_wrong_destination",
    "relay_root_writable","relay_volume_mount","relay_script_writable",
    "relay_capabilities","relay_wrong_entrypoint",
    "relay_wrong_service","relay_root","relay_wrong_gid","relay_no_nnp",
    "backend_stopped","relay_stopped",
))
def test_host_port_identity_and_network_fail_closed(change):
    mod=load()
    backend,relay=fixture()
    private=PROJECT+"_a_db_private"
    pub=PROJECT+"_loopback_publish"
    port="8000/tcp"
    if change=="public_host":
        relay["NetworkSettings"]["Ports"][port][0]["HostIp"]="0.0.0.0"
    elif change=="no_host_port":
        relay["NetworkSettings"]["Ports"][port]=[]
    elif change=="extra_host_port":
        relay["NetworkSettings"]["Ports"]["5055/tcp"]=[{"HostIp":"127.0.0.1","HostPort":"48001"}]
    elif change=="missing_host_port":
        relay["NetworkSettings"]["Ports"][port][0]["HostPort"]=""
    elif change=="backend_published":
        backend["NetworkSettings"]["Ports"][port]=[{"HostIp":"127.0.0.1","HostPort":"48920"}]
    elif change=="backend_hostconfig_binding":
        backend["HostConfig"]["PortBindings"][port]=[{"HostIp":"127.0.0.1","HostPort":"0"}]
    elif change=="wrong_private_network":
        backend["NetworkSettings"]["Networks"]={PROJECT+"_other":{"NetworkID":"c"*64}}
    elif change=="backend_on_publish_network":
        backend["NetworkSettings"]["Networks"][pub]={"NetworkID":"e"*64}
    elif change=="relay_off_private_network":
        relay["NetworkSettings"]["Networks"].pop(private)
    elif change=="relay_wrong_private_network_id":
        relay["NetworkSettings"]["Networks"][private]["NetworkID"]="f"*64
    elif change=="relay_wrong_publishing_network":
        relay["NetworkSettings"]["Networks"]={private:{"NetworkID":"c"*64},
                                              PROJECT+"_other":{"NetworkID":"e"*64}}
    elif change=="relay_wrong_image":
        relay["Image"]="sha256:"+"f"*64
    elif change=="relay_wrong_project":
        relay["Config"]["Labels"]["com.docker.compose.project"]="other"
    elif change=="relay_wrong_destination":
        relay["Config"]["Cmd"]=["--role","on_db","--listen","8000"]
    elif change=="relay_root_writable":
        relay["HostConfig"]["ReadonlyRootfs"]=False
    elif change=="relay_volume_mount":
        relay["Mounts"]=[{"Type":"volume","Destination":"/mydata","RW":True}]
    elif change=="relay_script_writable":
        relay["Mounts"][0]["RW"]=True
    elif change=="relay_capabilities":
        relay["HostConfig"]["CapDrop"]=[]
    elif change=="relay_wrong_entrypoint":
        relay["Config"]["Entrypoint"]=["/bin/sh"]
    elif change=="relay_wrong_service":
        relay["Config"]["Labels"]["com.docker.compose.service"]="other"
    elif change=="relay_root":
        relay["Config"]["User"]="0:0"
    elif change=="relay_wrong_gid":
        relay["Config"]["User"]="65532:1000"
    elif change=="relay_no_nnp":
        relay["HostConfig"]["SecurityOpt"]=[]
    elif change=="backend_stopped":
        backend["State"]["Running"]=False
    elif change=="relay_stopped":
        relay["State"]["Running"]=False
    else:
        raise AssertionError(change)
    with pytest.raises(RuntimeError):
        mod.inspect_port_pair("a_db",backend,relay,PROJECT,IMAGE)


def test_relay_endpoint_is_not_arbitrary_host_or_internal_port():
    path=ROOT/"scripts/stage1/loopback_relay.py"
    spec=importlib.util.spec_from_file_location("stage1_scoped_relay",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate_endpoint("a_db",8000)==("a_db",8000)
    assert module.validate_endpoint("on_db",8000)==("on_db",8000)
    assert module.validate_endpoint("native",5055)==("native",5055)
    for role,port in (("a_db",5055),("native",8000),("foreign",8000)):
        with pytest.raises(ValueError):
            module.validate_endpoint(role,port)
