from src.base.base_server import BaseServer
import socket

import time
import sys
import struct
import json
from src.utils.json_numpy import numpy_to_json, json_to_numpy
from src.utils import msgpack_numpy
import pickle

class UDPServer(BaseServer):
    def __init__(self, host, port, packaging_type="json"):
        super().__init__()
        
        self.host = host
        self.port = port
        self.packaging_type = packaging_type
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))

        print(f"UDP Server listening on {self.host}:{self.port}")

        self.client_addr = None

    
    def _send_msg(self, obj):
        if self.packaging_type == "json":
            payload = numpy_to_json(obj).encode("utf-8") # json
        elif self.packaging_type == "msgpack":
            payload = msgpack_numpy.packb(obj) # msgpack
        elif self.packaging_type == "pickle":
            payload = pickle.dumps(obj) # pickle
        else:
            raise ValueError("Unsupported packaging type")
        
        print("payload size:", len(payload))

        if self.client_addr is None:
            raise RuntimeError("Client address unknown. Receive something first.")

        self.server_socket.sendto(payload, self.client_addr)

    def _recv_msg(self):
        data, addr = self.server_socket.recvfrom(65536)

        # record client address
        if self.client_addr is None:
     
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                print(f"Invalid registration message from {addr}")
                return None
            
            if isinstance(msg, dict) and msg.get("type") == "register":
                self.client_addr = addr
                print(f"Client registered: {self.client_addr}")
                return None
            else:
                print(f"First message must be register. Received from {addr}")
                return None
        elif self.client_addr != addr:
            print(f"Received message from unknown client {addr}, expected {self.client_addr}. Ignoring.")
            return None

        if self.packaging_type == "json":
            return json_to_numpy(data.decode("utf-8")) # json
        elif self.packaging_type == "msgpack":
            return msgpack_numpy.unpackb(data) # msgpack
        elif self.packaging_type == "pickle":
            return pickle.loads(data) # pickle
        else:
            raise ValueError("Unsupported packaging type")
        
    def post_obs(self, obs):
        self._send_msg(obs)

    def get_action(self):
        action = self._recv_msg()
        print(f"Received action: {action}")
        return action
    
    def close(self):
        self.server_socket.close()

    
    