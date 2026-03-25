from src.base.base_server import BaseServer
from websockets.server import serve
import numpy as np
import json
import asyncio
import time

import sys

from src.serializer.json_serializer import numpy_to_json, json_to_numpy
from src.serializer import create_serializer

class WebServer(BaseServer):

    def __init__(self, host="0.0.0.0", port=8000, packaging_type = "json"):
        super().__init__()
        self.host = host
        self.port = port

        self.controller_ws = None
        self.viewer_ws = set()
        self._action_queue = asyncio.Queue()
        self._msg_queue = asyncio.Queue()
        self._connected_event = asyncio.Event()

        self.packaging_type = packaging_type
        self.serializer = create_serializer(packaging_type)
        # self.packer = msgpack_numpy.Packer()

    async def start(self):
        # 启动服务器
        async def handler(websocket, path=None):
            # 处理客户端的连接和信息
            ws_path = path if path is not None else getattr(websocket, "path", "/")
            is_viewer = ("role=viewer" in ws_path) or ws_path.rstrip("/").endswith("/viewer")

            if is_viewer:
                self.viewer_ws.add(websocket)
                print(f"Viewer connected: {ws_path}")
            else:
                self.controller_ws = websocket
                print(f"Controller connected: {ws_path}")
                self._connected_event.set()  # 仅 controller 连接时通知

            try:
                # 每次收到一个message, sever就会从中解析出action并放入队列中
                async for message in websocket:
                    data = self.serializer.deserialize(message)

                    if is_viewer:
                        # viewer 只接收观测图像，忽略其上行消息
                        continue

                    # 仅当前 controller 的上行 action 生效
                    if websocket is not self.controller_ws:
                        continue

                    if data.get("type") == "action":
                        if self.packaging_type == "json":
                            action = json_to_numpy(data["action"]) # json
                        elif self.packaging_type == "pickle" or self.packaging_type == "msgpack":
                            action = data["action"]  # msgpack, pickle
                        await self._action_queue.put(action)
                    else:
                        # 其他消息
                        await self._msg_queue.put(data)


            except Exception as e:
                print("Client disconnected:", e)

            finally:
                print("Closing websocket...")
                if not websocket.closed:
                    await websocket.close()

                if websocket is self.controller_ws:
                    self.controller_ws = None
                if websocket in self.viewer_ws:
                    self.viewer_ws.discard(websocket)

                if self.controller_ws is None:
                    self._connected_event.clear()

                print("Websocket closed.")

        print(f"WebServer running on ws://{self.host}:{self.port}")
        async with serve(handler, self.host, self.port, max_size = None):
            await asyncio.Future()  # Run forever

    async def _recv_msg(self):
        # 从队列中获取消息
        data = await self._msg_queue.get()
        return data
    
    # -------------------------------------------------
    # 发送 observation
    # -------------------------------------------------
    async def post_obs(self, obs: dict) -> None:
        await self._connected_event.wait()  # 等客户端真正连接

        controller_obs = obs
        # viewer_obs = {
        #     "observation": obs.get("observation", {})
        # }
        viewer_obs = obs # viewer 也发全量 obs，方便后续扩展
        
        if self.packaging_type == "json":
            controller_payload = {
                "type": "obs",
                "obs": numpy_to_json(controller_obs) # json
            }
            viewer_payload = {
                "type": "obs",
                "obs": numpy_to_json(viewer_obs) # json
            }
        elif self.packaging_type == "msgpack" or self.packaging_type == "pickle":
            controller_payload = {
                "type": "obs",
                "obs": controller_obs  # msgpack, pickle
            }
            viewer_payload = {
                "type": "obs",
                "obs": viewer_obs  # msgpack, pickle
            }

        send_tasks = []
        if self.controller_ws is not None:
            send_tasks.append(self._send_msg(self.controller_ws, controller_payload)) # send to controller
        for ws in list(self.viewer_ws):
            send_tasks.append(self._send_msg(ws, viewer_payload)) # send to all viewers

        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)

    async def _send_msg(self, websocket, payload):
        try:
            packed_payload = self.serializer.serialize(payload)
            await websocket.send(packed_payload)

        except Exception as e:
            print("Send failed:", e)
            if websocket is self.controller_ws:
                self.controller_ws = None
            else:
                self.viewer_ws.discard(websocket)

            if self.controller_ws is None:
                self._connected_event.clear()


    async def get_action(self, timeout=None) -> np.ndarray:
        try:
            action = await asyncio.wait_for(self._action_queue.get(), timeout=timeout)
            return action
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout waiting for action")
