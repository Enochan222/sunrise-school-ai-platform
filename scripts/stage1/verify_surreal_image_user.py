#!/usr/bin/env python3
"""Attest non-root effective UID:GID against exact local SurrealDB image.

A Docker image can declare Config.User as UID-only (e.g. 65532); Docker's
primary group for that UID MUST be read from the pinned image's /etc/passwd,
not guessed as equal to the UID or replaced by root. This probes no volume,
runs no DB process, and only removes its own never-started probe container.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import tarfile
import uuid

IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
ACCOUNT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*\Z")
NUMBER = re.compile(r"(0|[1-9][0-9]*)\Z")


def parse_identity(config_user: str, passwd: bytes, group: bytes) -> tuple[int, int]:
    """Reject ambiguous/malformed image accounts and any root UID/GID."""
    if not isinstance(config_user, str) or not config_user:
        raise ValueError("Missing image Config.User")
    if b"\x00" in passwd or b"\x00" in group:
        raise ValueError("NUL in image identity files")
    records = []
    for raw in passwd.decode("utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split(":")
        if len(parts) != 7 or not NUMBER.fullmatch(parts[2]) or not NUMBER.fullmatch(parts[3]):
            raise ValueError("Malformed /etc/passwd record")
        records.append((parts[0], int(parts[2]), int(parts[3])))
    if ":" in config_user:
        name, configured_gid = config_user.split(":", 1)
        if not NUMBER.fullmatch(configured_gid):
            raise ValueError("Explicit Docker user GID must be numeric")
        gid = int(configured_gid)
    else:
        name, gid = config_user, None
    if not (NUMBER.fullmatch(name) or ACCOUNT.fullmatch(name)):
        raise ValueError("Unsupported Image Config.User")
    is_uid = bool(NUMBER.fullmatch(name))
    matches = [row for row in records if (row[1] == int(name) if is_uid else row[0] == name)]
    if len(matches) != 1:
        raise ValueError("Image identity missing or ambiguous in /etc/passwd")
    _, uid, primary_gid = matches[0]
    if gid is None:
        gid = primary_gid
    # An explicit override contradicting the image account is an unsupported
    # configuration; we need the exact image primary identity for new volumes.
    if gid != primary_gid or not (0 < uid <= 65534 and 0 < gid <= 65534):
        raise ValueError("Root/invalid or mismatched primary non-root identity")
    groups = []
    for raw in group.decode("utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split(":")
        if len(parts) != 4 or not NUMBER.fullmatch(parts[2]):
            raise ValueError("Malformed /etc/group record")
        groups.append(int(parts[2]))
    if groups.count(gid) != 1:
        raise ValueError("Primary GID not independently present in image /etc/group")
    return uid, gid


def run(*args: str, timeout: int = 30) -> str:
    output = subprocess.run(list(args), capture_output=True, text=True,
                            check=True, timeout=timeout)
    return output.stdout.strip()


def image_file(context: str, cid: str, name: str) -> bytes:
    output = subprocess.run(["docker", "--context", context, "cp",
                             cid + ":/etc/" + name, "-"],
                            capture_output=True, check=True, timeout=30)
    if len(output.stdout) > 262144:
        raise ValueError("Oversized image account file")
    with tarfile.open(fileobj=io.BytesIO(output.stdout), mode="r:") as bundle:
        entries = bundle.getmembers()
        if len(entries) != 1 or not entries[0].isfile() or entries[0].size > 65536:
            raise ValueError("Untrusted Docker account file archive")
        stream = bundle.extractfile(entries[0])
        if stream is None:
            raise ValueError("Missing account file")
        return stream.read(65537)


def verify(context: str, image: str, digest: str) -> tuple[int, int]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", context):
        raise ValueError("Invalid explicit Docker context")
    if not IMAGE_ID.fullmatch(image) or not DIGEST.fullmatch(digest):
        raise ValueError("Expected exact immutable image ID and registry digest")
    info = json.loads(run("docker", "--context", context, "image", "inspect", image))
    if len(info) != 1 or info[0].get("Id") != image:
        raise ValueError("Image identity changed")
    if not any(isinstance(item, str) and item.endswith("@" + digest)
               for item in info[0].get("RepoDigests", [])):
        raise ValueError("Image registry digest does not match pinned release")
    declared = info[0].get("Config", {}).get("User")
    # Docker create (never start) avoids shell/id assumptions in distroless
    # images. A random probe name cannot collide with project volumes.
    name = "sunrise-image-identity-" + uuid.uuid4().hex
    cid = run("docker", "--context", context, "create", "--name", name,
              "--network", "none", "--entrypoint", "/surreal", image,
              "version")
    if not re.fullmatch(r"[a-f0-9]{64}", cid):
        raise ValueError("Unverifiable temporary image container identity")
    try:
        passwd = image_file(context, cid, "passwd")
        group = image_file(context, cid, "group")
        return parse_identity(declared, passwd, group)
    finally:
        # Only the unique never-started container created above; no prune,
        # volume mount, process execution, or destructive project operation.
        subprocess.run(["docker", "--context", context, "rm", cid],
                       capture_output=True, check=True, timeout=30)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--digest", required=True)
    args = parser.parse_args()
    uid, gid = verify(args.context, args.image, args.digest)
    print(f"{uid}:{gid}")


if __name__ == "__main__":
    main()
