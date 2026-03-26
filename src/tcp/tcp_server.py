import numpy as np
import socket
import json
import struct
from src.base.base_server import BaseServer

import time
import sys
from src.serializer import create_serializer

class TCPServer(BaseServer):
    def __init__(self, host = "0.0.0.0", port = 12000, packaging_type="json", io_timeout: float | None = 10.0, accept_timeout: float | None = None):
        super().__init__()
        self.host = host
        self.port = port
        self.packaging_type = packaging_type
        self.serializer = create_serializer(packaging_type)
        self.io_timeout = io_timeout

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if accept_timeout is not None and accept_timeout > 0:
            self.server_socket.settimeout(accept_timeout)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        print(f"TCP Server listening on {self.host}:{self.port}")

        self.conn = None
        self.addr = None

    def accept_connection(self):
        print("Waiting for a client to connect...")
        try:
            self.conn, self.addr = self.server_socket.accept()
        except socket.timeout as exc:
            raise TimeoutError("Timed out while waiting for client connection.") from exc

        if self.io_timeout is not None and self.io_timeout > 0:
            self.conn.settimeout(self.io_timeout)
        print(f"Client connected from {self.addr}")

    def _recv_all(self, size):
        data = b''
        while len(data) < size:
            try:
                packet = self.conn.recv(size - len(data))
            except socket.timeout as exc:
                raise TimeoutError("Timed out while receiving data from client.") from exc
            if not packet:
                raise ConnectionError("Client disconnected")
            data += packet
        return data
    
    def _send_msg(self, obj):
        payload = self.serializer.serialize(obj)

        msg = struct.pack('!I', len(payload)) + payload # '!I' means big-endian unsigned int
        # print("msg size:", len(msg))
        self.conn.sendall(msg)

    def _recv_msg(self):
        raw_len = self._recv_all(4)
        msg_len = struct.unpack('!I', raw_len)[0]
        data = self._recv_all(msg_len)

        return self.serializer.deserialize(data)

    def post_obs(self, obs: dict) -> None:
        self._send_msg(obs)
    
    def get_action(self):
        action = self._recv_msg()
        print(f"Received action: {action}")
        return action
        
    def close(self):
        if self.conn:
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.conn.close()
        self.server_socket.close()
