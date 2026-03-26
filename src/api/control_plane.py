import json
import socket
import struct

DEFAULT_DATA_PORTS = {
    "tcp": 7101,
    "web": 7102,
    "udp": 7103,
}


def send_json_message(sock: socket.socket, payload: dict) -> None:
    raw = json.dumps(payload).encode("utf-8")
    sock.sendall(struct.pack("!I", len(raw)) + raw)


def recv_json_message(sock: socket.socket) -> dict:
    raw_len = _recv_all(sock, 4)
    (msg_len,) = struct.unpack("!I", raw_len)
    data = _recv_all(sock, msg_len)
    return json.loads(data.decode("utf-8"))


def request_test_session(host: str, port: int, payload: dict, timeout: float = 10.0) -> dict:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        send_json_message(sock, payload)
        return recv_json_message(sock)


def _recv_all(sock: socket.socket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            raise ConnectionError("Socket closed while receiving control message.")
        data += packet
    return data
