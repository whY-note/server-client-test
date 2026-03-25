from src.base.base_client import BaseClient
import numpy as np
import os
import socket
import json

from src.utils.collecter import Collector
from src.utils.json_numpy import numpy_to_json, json_to_numpy
from src.utils import msgpack_numpy
import pickle

class UDPClient(BaseClient):
    def __init__(self, packaging_type):
        super().__init__()
        self.packaging_type = packaging_type
        self.collector = Collector()

    def connect(self, host, port, max_size = None):
        # 这里并不是真正的连接，因为UDP是无连接的协议，但我们需要记录服务器的地址以便发送数据
        self.server_addr = (host, port) # 打包成二元组
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"UDP Client ready to send to {host}:{port}")

        # 发送第一条信息给服务器，触发服务器记录客户端地址
        hello_msg = {
            "type": "register"
        }

        payload = json.dumps(hello_msg).encode("utf-8")
        self.client_socket.sendto(payload, self.server_addr)


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

        self.client_socket.sendto(payload, self.server_addr)

    def _recv_msg(self):
        data, addr = self.client_socket.recvfrom(65536)

        if self.packaging_type == "json":
            return json_to_numpy(data.decode("utf-8")) # json
        elif self.packaging_type == "msgpack":
            return msgpack_numpy.unpackb(data) # msgpack
        elif self.packaging_type == "pickle":
            return pickle.loads(data) # pickle
        else:
            raise ValueError("Unsupported packaging type")
    
    def get_obs(self):
        obs = self._recv_msg()
        return obs
    
    def post_action(self, action):
        if isinstance(action, np.ndarray):
            action = action.tolist()
        self._send_msg(action)

    def infer(self, obs):
        # TODO: use policy to infer action according to obs
        action = np.zeros(14, dtype=np.float64) # dummy action, (6-DoF + 1 gripper)*2
        return action
    
    def step(self):
        obs = self.get_obs()
        print(f"[Client] Received obs: {obs}")
        # self.collector.collect(obs)

        action = self.infer(obs)

        self.post_action(action)

    def close(self):
        self.client_socket.close()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_dir = os.path.join(BASE_DIR, "../../data")
        file_name = "episode0_udp_client_" + self.packaging_type + ".hdf5"
        file_path = os.path.join(file_dir, file_name)

        # self.collector.save_hdf5(file_path)