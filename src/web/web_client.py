from src.base.base_client import BaseClient
import websockets.sync.client
import numpy as np
import os
import json
import struct
from src.utils.collecter import Collector

from src.serializer.json_serializer import numpy_to_json, json_to_numpy
from src.serializer import create_serializer

class WebClient(BaseClient):
    def __init__(self, packaging_type="json"):
        super().__init__()
        self.packaging_type = packaging_type
        self.collector = Collector()
        self.serializer = create_serializer(packaging_type)
        self.ws = None
        self.io_timeout = 10.0
        # self.packer = msgpack_numpy.Packer()
    
    def connect(self, host, port, connect_timeout: float | None = 10.0, io_timeout: float | None = 10.0, max_size = None):
        self.server_url = "ws://" + host + ":" + str(port)
        print(f"url:{self.server_url}")
        self.io_timeout = io_timeout if io_timeout and io_timeout > 0 else None
        open_timeout = connect_timeout if connect_timeout and connect_timeout > 0 else None
        self.ws = websockets.sync.client.connect(self.server_url, max_size = max_size, open_timeout=open_timeout)

    def _recv_msg(self):
        message = self.ws.recv(timeout=self.io_timeout)  # 阻塞等待
        data = self.serializer.deserialize(message)
        return data
    
    def _send_msg(self, payload):
        packed_payload = self.serializer.serialize(payload)
        self.ws.send(packed_payload) 

    def get_obs(self):

        data = self._recv_msg()

        if data.get("type") != "obs":
            raise ValueError("Unexpected message type")

        if self.packaging_type == "json":
            obs = json_to_numpy(data["obs"]) # json
        elif self.packaging_type == "msgpack" or self.packaging_type == "pickle":
            obs = data["obs"]  # msgpack, pickle

        return obs

    def post_action(self, action):
        # print(f"post_action: {action}")

        if self.packaging_type == "json":
            if isinstance(action, np.ndarray):
                action = action.tolist()

        if self.packaging_type == "json":
            payload = {
                "type": "action",
                "action": numpy_to_json(action) # json
            }        
        elif self.packaging_type == "msgpack" or self.packaging_type == "pickle":
            payload = {
                "type": "action",
                "action": action  # msgpack, pickle
            }
        self._send_msg(payload)


    def infer(self, obs) -> np.ndarray:
        return np.random.rand(14).astype(np.float64)

    def step(self):
        obs = self.get_obs()
        self.collector.collect(obs)
        # print(f"Received obs: {obs}")
        action = self.infer(obs)
        self.post_action(action)
        return False 

    def close(self):
        if self.ws is not None:
            self.ws.close()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_dir = os.path.join(BASE_DIR, "../../data")
        file_name = "episode0_web_client_"+ self.packaging_type +".hdf5"
        file_path = os.path.join(file_dir, file_name)

        self.collector.save_hdf5(file_path)
