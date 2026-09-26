"""Minimal RCON client for scripting/testing a Minecraft (Fabric) dev server.

No external dependencies - uses only the standard library (socket/struct).
Implements the Source RCON protocol used by Minecraft's remote console.

Usage:
    python rcon_client.py "<command 1>" "<command 2>" ...

Each command is sent in order over a single RCON connection, and the
server's response to each is printed. See README.md in this folder for
setup instructions and examples.

Configuration (edit below, or override via environment variables):
    RCON_HOST      default: 127.0.0.1
    RCON_PORT      default: 25575
    RCON_PASSWORD  default: (must be set - see README.md)
"""

import os
import socket
import struct
import sys

HOST = os.environ.get("RCON_HOST", "127.0.0.1")
PORT = int(os.environ.get("RCON_PORT", "25575"))
PASSWORD = os.environ.get("RCON_PASSWORD", "")

SERVERDATA_AUTH = 3
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_RESPONSE_VALUE = 0


def send_packet(sock, request_id, packet_type, payload):
    body = struct.pack("<ii", request_id, packet_type) + payload.encode("utf8") + b"\x00\x00"
    sock.send(struct.pack("<i", len(body)) + body)


def read_packet(sock):
    length_bytes = sock.recv(4)
    if len(length_bytes) < 4:
        raise ConnectionError("Connection closed by server while reading packet length")
    length = struct.unpack("<i", length_bytes)[0]
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by server while reading packet body")
        data += chunk
    request_id, packet_type = struct.unpack("<ii", data[:8])
    payload = data[8:-2].decode("utf8", errors="replace")
    return request_id, packet_type, payload


def run_commands(commands, host=HOST, port=PORT, password=PASSWORD, quiet=False):
    """Connects, authenticates, and runs each command in order.

    Returns a list of (command, response_text) tuples.
    """
    if not password:
        raise ValueError(
            "No RCON password configured. Set the RCON_PASSWORD environment "
            "variable, or edit the PASSWORD constant in this script."
        )

    results = []
    sock = socket.create_connection((host, port), timeout=10)
    try:
        send_packet(sock, 1, SERVERDATA_AUTH, password)
        request_id, _packet_type, _payload = read_packet(sock)
        if request_id == -1:
            raise PermissionError("RCON authentication failed - check RCON_PASSWORD / rcon.password")

        for i, cmd in enumerate(commands):
            send_packet(sock, 100 + i, SERVERDATA_EXECCOMMAND, cmd)
            _request_id, _packet_type, payload = read_packet(sock)
            results.append((cmd, payload))
            if not quiet:
                print(f">>> {cmd}")
                print(payload)
    finally:
        sock.close()

    return results


def main():
    commands = sys.argv[1:]
    if not commands:
        print("Usage: python rcon_client.py \"<command 1>\" \"<command 2>\" ...")
        sys.exit(1)

    try:
        run_commands(commands)
    except Exception as exc:
        print(f"RCON error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
