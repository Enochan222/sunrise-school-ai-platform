#!/usr/bin/env python3
"""C-only synthetic loopback TCP relay (no credentials, no remote egress).

The DB and Worker stay on separate Docker *internal* networks. A disposable
relay connected to its one private network and a project publish bridge
accepts a loopback-published host port; it forwards only to its fixed target.
Never attach a database or Native process directly to the publish network.
"""
from __future__ import annotations

import argparse
import selectors
import socket
import socketserver
import threading

ENDPOINTS = {
    "a_db": ("a_db", 8000),
    "on_db": ("on_db", 8000),
    "native": ("native", 5055),
}


def validate_endpoint(role: str, listen: int) -> tuple[str, int]:
    if role not in ENDPOINTS:
        raise ValueError("Unrecognised synthetic private relay destination")
    target, port = ENDPOINTS[role]
    if type(listen) is not int or listen != port:
        raise ValueError("Unexpected private relay service port")
    return target, port


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True
    request_queue_size = 16


class Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        target_host, target_port = self.server.target
        # No TLS decryption, credential material, payload capture or logs.
        with socket.create_connection((target_host, target_port), timeout=8) as upstream:
            self.request.setblocking(False)
            upstream.setblocking(False)
            selector = selectors.DefaultSelector()
            try:
                selector.register(self.request, selectors.EVENT_READ, upstream)
                selector.register(upstream, selectors.EVENT_READ, self.request)
                while True:
                    events = selector.select(timeout=30)
                    if not events:
                        return
                    for key, _ in events:
                        received = key.fileobj.recv(65536)
                        if not received:
                            return
                        destination = key.data
                        # A bounded timeout for slow peers; no hidden retries.
                        destination.settimeout(15)
                        destination.sendall(received)
                        destination.setblocking(False)
            finally:
                selector.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=tuple(ENDPOINTS))
    parser.add_argument("--listen", required=True, type=int)
    args = parser.parse_args()
    target = validate_endpoint(args.role, args.listen)
    with TCPServer(("0.0.0.0", args.listen), Handler) as server:
        server.target = target
        server.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    main()
