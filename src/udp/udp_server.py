from src.base.base_server import BaseServer
import socket

import time
import sys
import struct
import json

from src.serializer import create_serializer
from src.udp.udp_config import *

class UDPServer(BaseServer):
    def __init__(self, host, port, packaging_type="json"):
        super().__init__()
        
        self.host = host
        self.port = port
        self.packaging_type = packaging_type
        self.serializer = create_serializer(packaging_type)
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))

        print(f"UDP Server listening on {self.host}:{self.port}")

        self.client_addr = None

        self.recv_buffer = {}

    
    def _send_msg(self, obj):

        payload = self.serializer.serialize(obj)
        
        chunks = [
            payload[i : i + MAX_CHUNK_SIZE]
            for i in range(0, len(payload), MAX_CHUNK_SIZE)
        ]

        total_chunks = len(chunks)

        msg_id = int(time.time()*1000) & 0xFFFFFFFF # use timestamp as message id, mod 2^32 to fit in 4 bytes

        if self.client_addr is None:
            raise RuntimeError("Client address unknown. Receive something first.")

        for chunk_id,chunk in enumerate(chunks):
            header = struct.pack(
                HEADER_FORMAT,
                msg_id,
                total_chunks,
                chunk_id
            )
            packet = header + chunk

            self.server_socket.sendto(packet, self.client_addr)
        
    def _recv_all(self):
        packet, addr = self.server_socket.recvfrom(65536)
        print("received packet from:", addr)

        # 收集所有分片        
        header = packet[:HEADER_SIZE] # 头部
        chunk = packet[HEADER_SIZE:] # 数据块

        msg_id, total_chunks, chunk_id = struct.unpack(HEADER_FORMAT, header)

        if msg_id not in self.recv_buffer:
            self.recv_buffer[msg_id] = {}
        self.recv_buffer[msg_id][chunk_id] = chunk

        if len(self.recv_buffer[msg_id]) < total_chunks:
            return None

        # 收集齐,则合并成原始payload
        payload = b''.join(self.recv_buffer[msg_id][i] for i in range(total_chunks))

        del self.recv_buffer[msg_id]

        msg = self.serializer.deserialize(payload)
        
        # record client address
        if self.client_addr is None:
            if isinstance(msg, dict) and msg.get("type") == "user_name":
                self.client_addr = addr
                print(f"Client {self.client_addr} registered")
                return msg
            else:
                raise ValueError(f"First message must be user_name. Received from {addr}")
        elif self.client_addr != addr:
            print(f"Received message from unknown client {addr}, expected {self.client_addr}. Ignoring.")
            return None
        else: # self.client_addr == addr
            return msg
    
    def _recv_msg(self):
        while True:
            msg = self._recv_all() # action 可能未收集齐，因此可能返回None，此时继续等待直到收集齐为止
            if msg is not None:
                break
        return msg

    def post_obs(self, obs):
        self._send_msg(obs)

    def get_action(self):
        action = self._recv_msg()
        print(f"Received action: {action}")
        return action
    
    def close(self):
        # 给 client 发送一个特殊消息，通知其关闭
        if self.client_addr is not None:
            close_msg = "close"
            self._send_msg(close_msg)
        self.server_socket.close()

    
    