from src.base.base_client import BaseClient
import numpy as np
import os
import socket
import time
import json
from typing import Optional

from src.utils.collecter import Collector

from src.serializer import create_serializer

from src.udp.udp_config import *

class UDPClient(BaseClient):
    def __init__(self, packaging_type):
        super().__init__()
        self.packaging_type = packaging_type
        self.collector = Collector()

        self.recv_buffer = {}
        self.serializer = create_serializer(packaging_type)

    def connect(self, host, port, connect_timeout: Optional[float] = None, io_timeout: Optional[float] = 10.0, max_size = None):
        # 这里并不是真正的连接，因为UDP是无连接的协议，但我们需要记录服务器的地址以便发送数据
        self.server_addr = (host, port) # 打包成二元组
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if io_timeout is not None and io_timeout > 0:
            self.client_socket.settimeout(io_timeout)
        print(f"UDP Client ready to send to {host}:{port}")

        # # 发送第一条信息给服务器，触发服务器记录客户端地址
        # hello_msg = {
        #     "type": "register"
        # }

        # payload = json.dumps(hello_msg).encode("utf-8")
        # self.client_socket.sendto(payload, self.server_addr)
        # print("Sent registration message to server")


    def _send_msg(self, obj):
        payload = self.serializer.serialize(obj)
        
        chunks = [
            payload[i : i + MAX_CHUNK_SIZE]
            for i in range(0, len(payload), MAX_CHUNK_SIZE)
        ]

        total_chunks = len(chunks)

        msg_id = int(time.time()*1000) & 0xFFFFFFFF # use timestamp as message id, mod 2^32 to fit in 4 bytes

        for chunk_id, chunk in enumerate(chunks):
            header = struct.pack(
                HEADER_FORMAT,
                msg_id,
                total_chunks,
                chunk_id
            )
            packet = header + chunk
            self.client_socket.sendto(packet, self.server_addr)

    def _recv_all(self):
        try:
            packet, addr = self.client_socket.recvfrom(65536)
        except socket.timeout as exc:
            raise TimeoutError("Timed out while waiting for UDP server data.") from exc

        header = packet[:HEADER_SIZE]
        chunk = packet[HEADER_SIZE:]

        msg_id, total_chunks, chunk_id = struct.unpack(
            HEADER_FORMAT,header
        )

        if msg_id not in self.recv_buffer:
            self.recv_buffer[msg_id] = {}
        self.recv_buffer[msg_id][chunk_id] = chunk

        if len(self.recv_buffer[msg_id]) < total_chunks:
            return None
        
        payload = b''.join(
            self.recv_buffer[msg_id][i]
            for i in range(total_chunks)
        )
        del self.recv_buffer[msg_id]

        return self.serializer.deserialize(payload)
    
    def _recv_msg(self):
        while True:
            msg = self._recv_all() # action 可能未收集齐，因此可能返回None，此时继续等待直到收集齐为止
            if msg is not None:
                break
        return msg
    
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
        if obs is None:
            print("Failed to receive complete message. Skipping this step.")
            return False
        elif obs == "close":
            print("Received close signal from server. Shutting down client.")
            return True
        self.collector.collect(obs)
        action = self.infer(obs)
        self.post_action(action)
        return False

    def close(self):
        if hasattr(self, "client_socket") and self.client_socket is not None:
            self.client_socket.close()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_dir = os.path.join(BASE_DIR, "../../data")
        file_name = "episode0_udp_client_" + self.packaging_type + ".hdf5"
        file_path = os.path.join(file_dir, file_name)

        self.collector.save_hdf5(file_path)