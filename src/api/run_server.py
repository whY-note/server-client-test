from src.tcp.tcp_server import TCPServer
from src.web.web_server import WebServer
from src.udp.udp_server import UDPServer

import time
from src.utils.utils import jpeg_to_img
import os

import asyncio
import h5py

def run_udp(host, port, packaging_type, test_file_path, is_jpeg: bool):

    server = UDPServer(host, port, packaging_type)

    user_name_dict = server._recv_msg() # 等待客户端注册

    if user_name_dict.get("type") == "user_name":
        user_name = user_name_dict.get("user_name", "unknown_user")
    else:
        print("Did not receive username, using default 'unknown_user'")
        user_name = "unknown_user"
    print(f"User: {user_name}")

    try:
        with h5py.File(test_file_path, "r") as f:
            # load data from hdf5 file
            rgb_dataset_head_camera = f["observation/head_camera/rgb"]
            rgb_dataset_left_camera = f["observation/left_camera/rgb"] 
            rgb_dataset_right_camera = f["observation/right_camera/rgb"]

            left_arm_dataset = f["joint_action/left_arm"][:]
            left_gripper_dataset = f["joint_action/left_gripper"][:]
            right_arm_dataset = f["joint_action/right_arm"][:]
            right_gripper_dataset = f["joint_action/right_gripper"][:]

            test_num = min(100, len(rgb_dataset_head_camera))
            print("test_num: ", test_num)
            decode_time = 0
            start_time = time.monotonic()

            for idx in range(test_num):
                # print("jpeg size:", len(rgb_dataset_head_camera[idx]))
                if packaging_type == "json":
                    obs = {
                            "joint_action": {
                                "left_arm": left_arm_dataset[idx],
                                "left_gripper": left_gripper_dataset[idx],
                                "right_arm": right_arm_dataset[idx],
                                "right_gripper": right_gripper_dataset[idx],
                            },
                            "observation": {
                                "head_camera": bytes(rgb_dataset_head_camera[idx]), # type(rgb_dataset_head_camera[idx]) = np.bytes, cannot be transformed to json
                                "left_camera": bytes(rgb_dataset_left_camera[idx]), 
                                "right_camera": bytes(rgb_dataset_right_camera[idx]),
                            }
                        }
                    
                elif packaging_type == "msgpack" or packaging_type == "pickle":
                    if is_jpeg:
                        # 图像使用jpeg，不转化为原始帧就传
                        obs = {
                                "joint_action": {
                                    "left_arm": left_arm_dataset[idx],
                                    "left_gripper": left_gripper_dataset[idx],
                                    "right_arm": right_arm_dataset[idx],
                                    "right_gripper": right_gripper_dataset[idx],
                                },
                                "observation": {
                                    "head_camera": bytes(rgb_dataset_head_camera[idx]), # type(rgb_dataset_head_camera[idx]) = np.bytes, cannot be transformed to json
                                    "left_camera": bytes(rgb_dataset_left_camera[idx]), 
                                    "right_camera": bytes(rgb_dataset_right_camera[idx]),
                                }
                            }
                        
                    else:
                        decode_start_time = time.monotonic()

                        # print(f"size of rgb_data: {len(rgb_dataset_head_camera[idx])} bytes")
                        
                        img_head_camera = jpeg_to_img(rgb_dataset_head_camera[idx]) # np.ndarray
                        img_left_camera = jpeg_to_img(rgb_dataset_left_camera[idx]) # np.ndarray
                        img_right_camera = jpeg_to_img(rgb_dataset_right_camera[idx]) # np.ndarray

                        # print(f"size of img: {img_head_camera.nbytes} bytes")
                
                        decode_end_time = time.monotonic()
                        decode_time += (decode_end_time - decode_start_time)

                        obs = {
                                "joint_action": {
                                    "left_arm": left_arm_dataset[idx],
                                    "left_gripper": left_gripper_dataset[idx],
                                    "right_arm": right_arm_dataset[idx],
                                    "right_gripper": right_gripper_dataset[idx],
                                },
                                "observation": {
                                    # 已经是单张图片了，不用再取索引
                                    "head_camera": img_head_camera,
                                    "left_camera": img_left_camera,
                                    "right_camera": img_right_camera,
                                } 
                            }
                    
                server.post_obs(obs)
                action = server.get_action()

            end_time = time.monotonic()

            # calculate average decode time and average round-trip time
            avg_decode_time = decode_time / test_num
            avg_RTT = (end_time - start_time - decode_time) / test_num

            print(f"Average decode time: {avg_decode_time:.4f} seconds")
            print(f"Average round-trip time: {avg_RTT:.4f} seconds")

            # ===== 构造 DataFrame =====
            result = {
                "user_name": user_name,
                "packaging_type": packaging_type,
                "test_num": test_num,
                "avg_decode_time": avg_decode_time,
                "avg_RTT": avg_RTT
            }

            return result
        
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()

def run_tcp(host, port, packaging_type, test_file_path, is_jpeg: bool):
    server = TCPServer(host, port, packaging_type)
    server.accept_connection()

    # 等待client发送用户名，并且在server端记录下来，放进result里
    user_name_dict = server._recv_msg()

    if user_name_dict.get("type") == "user_name":
        user_name = user_name_dict.get("user_name", "unknown_user")
    else:
        print("Did not receive username, using default 'unknown_user'")
        user_name = "unknown_user"
    print(f"User: {user_name}")
    try:
        with h5py.File(test_file_path, "r") as f:
            # load data from hdf5 file
            rgb_dataset_head_camera = f["observation/head_camera/rgb"]
            rgb_dataset_left_camera = f["observation/left_camera/rgb"] 
            rgb_dataset_right_camera = f["observation/right_camera/rgb"]

            left_arm_dataset = f["joint_action/left_arm"][:]
            left_gripper_dataset = f["joint_action/left_gripper"][:]
            right_arm_dataset = f["joint_action/right_arm"][:]
            right_gripper_dataset = f["joint_action/right_gripper"][:]

            test_num = min(100, len(rgb_dataset_head_camera))
            print("test_num: ", test_num)
            decode_time = 0
            start_time = time.monotonic()

            for idx in range(test_num):
                # print("jpeg size:", len(rgb_dataset_head_camera[idx]))
                if packaging_type == "json":
                    obs = {
                            "joint_action": {
                                "left_arm": left_arm_dataset[idx],
                                "left_gripper": left_gripper_dataset[idx],
                                "right_arm": right_arm_dataset[idx],
                                "right_gripper": right_gripper_dataset[idx],
                            },
                            "observation": {
                                "head_camera": bytes(rgb_dataset_head_camera[idx]), # type(rgb_dataset_head_camera[idx]) = np.bytes, cannot be transformed to json
                                "left_camera": bytes(rgb_dataset_left_camera[idx]), 
                                "right_camera": bytes(rgb_dataset_right_camera[idx]),
                            }
                        }
                    
                elif packaging_type == "msgpack" or packaging_type == "pickle":
                    if is_jpeg:
                        # 图像使用jpeg，不转化为原始帧就传
                        obs = {
                                "joint_action": {
                                    "left_arm": left_arm_dataset[idx],
                                    "left_gripper": left_gripper_dataset[idx],
                                    "right_arm": right_arm_dataset[idx],
                                    "right_gripper": right_gripper_dataset[idx],
                                },
                                "observation": {
                                    "head_camera": bytes(rgb_dataset_head_camera[idx]), # type(rgb_dataset_head_camera[idx]) = np.bytes, cannot be transformed to json
                                    "left_camera": bytes(rgb_dataset_left_camera[idx]), 
                                    "right_camera": bytes(rgb_dataset_right_camera[idx]),
                                }
                            }
                        
                    else:
                        decode_start_time = time.monotonic()

                        # print(f"size of rgb_data: {len(rgb_dataset_head_camera[idx])} bytes")
                        
                        img_head_camera = jpeg_to_img(rgb_dataset_head_camera[idx]) # np.ndarray
                        img_left_camera = jpeg_to_img(rgb_dataset_left_camera[idx]) # np.ndarray
                        img_right_camera = jpeg_to_img(rgb_dataset_right_camera[idx]) # np.ndarray

                        # print(f"size of img: {img_head_camera.nbytes} bytes")
                
                        decode_end_time = time.monotonic()
                        decode_time += (decode_end_time - decode_start_time)

                        obs = {
                                "joint_action": {
                                    "left_arm": left_arm_dataset[idx],
                                    "left_gripper": left_gripper_dataset[idx],
                                    "right_arm": right_arm_dataset[idx],
                                    "right_gripper": right_gripper_dataset[idx],
                                },
                                "observation": {
                                    # 已经是单张图片了，不用再取索引
                                    "head_camera": img_head_camera,
                                    "left_camera": img_left_camera,
                                    "right_camera": img_right_camera,
                                } 
                            }
                        
                server.post_obs(obs)
                action = server.get_action()

            end_time = time.monotonic()

            # calculate average decode time and average round-trip time
            avg_decode_time = decode_time / test_num
            avg_RTT = (end_time - start_time - decode_time) / test_num

            print(f"Average decode time: {avg_decode_time:.4f} seconds")
            print(f"Average round-trip time: {avg_RTT:.4f} seconds")

            # ===== 构造 DataFrame =====
            result = {
                "user_name": user_name,
                "packaging_type": packaging_type,
                "test_num": test_num,
                "avg_decode_time": avg_decode_time,
                "avg_RTT": avg_RTT
            }

            return result

    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()

async def run_web(host, port, packaging_type, test_file_path, is_jpeg: bool):

    server = WebServer(host, port, packaging_type)

    # 启动 WebSocket 服务器
    server_task = asyncio.create_task(server.start())

    print("Waiting for client...")
    await server._connected_event.wait()
    print("Client connected!")

    # 等待client发送用户名，并且在server端记录下来，放进result里
    user_name_dict = await server._recv_msg()

    if user_name_dict.get("type") == "user_name":
        user_name = user_name_dict.get("user_name", "unknown_user")
    else:
        print("Did not receive user name, using default 'unknown_user'")
        user_name = "unknown_user"
    print("User: ", user_name)
    # 模拟机器人控制循环
    try:
        with h5py.File(test_file_path, "r") as f:
            # load data from hdf5 file
            rgb_dataset_head_camera = f["observation/head_camera/rgb"]
            rgb_dataset_left_camera = f["observation/left_camera/rgb"] 
            rgb_dataset_right_camera = f["observation/right_camera/rgb"]

            left_arm_dataset = f["joint_action/left_arm"][:]
            left_gripper_dataset = f["joint_action/left_gripper"][:]
            right_arm_dataset = f["joint_action/right_arm"][:]
            right_gripper_dataset = f["joint_action/right_gripper"][:]

            # test_num = min(100, len(rgb_dataset_head_camera))
            test_num = len(rgb_dataset_head_camera)
            print("test_num: ", test_num)
            decode_time = 0
            start_time = time.monotonic()

            for idx in range(test_num):
                if packaging_type == "json":
                    obs = {
                        "joint_action": {
                            "left_arm": left_arm_dataset[idx],
                            "left_gripper": left_gripper_dataset[idx],
                            "right_arm": right_arm_dataset[idx],
                            "right_gripper": right_gripper_dataset[idx],
                        },
                        "observation": {
                            "head_camera": bytes(rgb_dataset_head_camera[idx]), # type(rgb_dataset_head_camera[idx]) = np.bytes, cannot be transformed to json
                            "left_camera": bytes(rgb_dataset_left_camera[idx]), 
                            "right_camera": bytes(rgb_dataset_right_camera[idx]),
                        }
                    }
                elif packaging_type == "msgpack" or packaging_type == "pickle":
                    if is_jpeg:
                        # 图像使用jpeg，不转化为原始帧就传
                        obs = {
                                "joint_action": {
                                    "left_arm": left_arm_dataset[idx],
                                    "left_gripper": left_gripper_dataset[idx],
                                    "right_arm": right_arm_dataset[idx],
                                    "right_gripper": right_gripper_dataset[idx],
                                },
                                "observation": {
                                    "head_camera": bytes(rgb_dataset_head_camera[idx]), # type(rgb_dataset_head_camera[idx]) = np.bytes, cannot be transformed to json
                                    "left_camera": bytes(rgb_dataset_left_camera[idx]), 
                                    "right_camera": bytes(rgb_dataset_right_camera[idx]),
                                }
                            }
                        
                    else:
                        decode_start_time = time.monotonic()

                        # print(f"size of rgb_data: {len(rgb_dataset_head_camera[idx])} bytes")
                        
                        img_head_camera = jpeg_to_img(rgb_dataset_head_camera[idx]) # np.ndarray
                        img_left_camera = jpeg_to_img(rgb_dataset_left_camera[idx]) # np.ndarray
                        img_right_camera = jpeg_to_img(rgb_dataset_right_camera[idx]) # np.ndarray
                        
                        # print(f"size of img: {img_head_camera.nbytes} bytes")
                
                        decode_end_time = time.monotonic()
                        decode_time += (decode_end_time - decode_start_time)

                        obs = {
                                "joint_action": {
                                    "left_arm": left_arm_dataset[idx],
                                    "left_gripper": left_gripper_dataset[idx],
                                    "right_arm": right_arm_dataset[idx],
                                    "right_gripper": right_gripper_dataset[idx],
                                },
                                "observation": {
                                    # 已经是单张图片了，不用再取索引
                                    "head_camera": img_head_camera,
                                    "left_camera": img_left_camera,
                                    "right_camera": img_right_camera,
                                } 
                            }

                await server.post_obs(obs)

                try:
                    action = await server.get_action(timeout=10)
                    print("Received action:", action)
                except TimeoutError:
                    print("No action received (timeout)")
                
                # await asyncio.sleep(0.5) # just for web test
            end_time = time.monotonic()

            # calculate average decode time and average round-trip time
            avg_decode_time = decode_time / test_num
            avg_RTT = (end_time - start_time - decode_time) / test_num

            print(f"Average decode time: {avg_decode_time:.4f} seconds")
            print(f"Average round-trip time: {avg_RTT:.4f} seconds")
            
            # ===== 构造 DataFrame =====
            result = {
                "user_name": user_name,
                "packaging_type": packaging_type,
                "test_num": test_num,
                "avg_decode_time": avg_decode_time,
                "avg_RTT": avg_RTT
            }

            return result

    except KeyboardInterrupt:
        print("Shutting down server...")
        server_task.cancel()
