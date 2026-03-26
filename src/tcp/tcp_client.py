from src.base.base_client import BaseClient
import numpy as np
import os
import socket
import json
import struct
from typing import Optional
from src.utils.collecter import Collector

from src.serializer import create_serializer

class TCPClient(BaseClient):
    def __init__(self, packaging_type):
        super().__init__()
        self.packaging_type = packaging_type
        self.collector = Collector()
        self.serializer = create_serializer(packaging_type)

    def connect(self, host, port, connect_timeout: Optional[float] = 10.0, io_timeout: Optional[float] = 10.0):
        self.host = host
        self.port = port

        timeout = connect_timeout if connect_timeout and connect_timeout > 0 else None
        self.client_socket = socket.create_connection((self.host, self.port), timeout=timeout)
        if io_timeout is not None and io_timeout > 0:
            self.client_socket.settimeout(io_timeout)

        print(f"Connected to TCP Server at {self.host}:{self.port}")
        
    def _recv_all(self, size):
        data = b""
        while len(data) < size:
            try:
                packet = self.client_socket.recv(size - len(data))
            except socket.timeout as exc:
                raise TimeoutError("Timed out while receiving data from server.") from exc
            if not packet:
                raise ConnectionError("Server disconnected")
            data += packet
        return data

    def _recv_msg(self):
        raw_len = self._recv_all(4) # 前4字 bytes表示消息长度
        (msg_len,) = struct.unpack("!I", raw_len)
        data = self._recv_all(msg_len)

        return self.serializer.deserialize(data)
    
    def _send_msg(self, obj):
        payload = self.serializer.serialize(obj)
        
        msg = struct.pack("!I", len(payload)) + payload
        self.client_socket.sendall(msg)

    def get_obs(self):
        obs = self._recv_msg()
        return obs
    
    def post_action(self, action):
        if isinstance(action, np.ndarray):
            action = action.tolist()
        self._send_msg(action)

    def infer(self, obs):
        # TODO: use policy to infer action according to obs
        action = np.random.rand(14).astype(np.float64) # dummy action, (6-DoF + 1 gripper)*2
        return action

    def step(self):
        obs = self.get_obs()
        self.collector.collect(obs)
        action = self.infer(obs)
        self.post_action(action)
        return False
        
    def close(self):
        if hasattr(self, "client_socket") and self.client_socket is not None:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.client_socket.close()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_dir = os.path.join(BASE_DIR, "../../data")
        file_name = "episode0_tcp_client_"+ self.packaging_type +".hdf5"
        file_path = os.path.join(file_dir, file_name)

        self.collector.save_hdf5(file_path)
