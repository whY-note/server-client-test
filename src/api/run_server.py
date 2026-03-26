from src.tcp.tcp_server import TCPServer
from src.web.web_server import WebServer
from src.udp.udp_server import UDPServer

from src.serializer import create_serializer
from src.serializer.json_serializer import numpy_to_json
from src.udp.udp_config import HEADER_SIZE, MAX_CHUNK_SIZE
from src.utils.utils import jpeg_to_img

import asyncio
import h5py
import math
import numpy as np
import time
from typing import Dict, List


def _build_obs(
    packaging_type,
    is_jpeg: bool,
    rgb_dataset_head_camera,
    rgb_dataset_left_camera,
    rgb_dataset_right_camera,
    left_arm_dataset,
    left_gripper_dataset,
    right_arm_dataset,
    right_gripper_dataset,
    idx: int,
):
    decode_time = 0.0

    if packaging_type == "json":
        obs = {
            "joint_action": {
                "left_arm": left_arm_dataset[idx],
                "left_gripper": left_gripper_dataset[idx],
                "right_arm": right_arm_dataset[idx],
                "right_gripper": right_gripper_dataset[idx],
            },
            "observation": {
                "head_camera": bytes(rgb_dataset_head_camera[idx]),
                "left_camera": bytes(rgb_dataset_left_camera[idx]),
                "right_camera": bytes(rgb_dataset_right_camera[idx]),
            },
        }
        return obs, decode_time

    if packaging_type == "msgpack" or packaging_type == "pickle":
        if is_jpeg:
            obs = {
                "joint_action": {
                    "left_arm": left_arm_dataset[idx],
                    "left_gripper": left_gripper_dataset[idx],
                    "right_arm": right_arm_dataset[idx],
                    "right_gripper": right_gripper_dataset[idx],
                },
                "observation": {
                    "head_camera": bytes(rgb_dataset_head_camera[idx]),
                    "left_camera": bytes(rgb_dataset_left_camera[idx]),
                    "right_camera": bytes(rgb_dataset_right_camera[idx]),
                },
            }
            return obs, decode_time

        decode_start_time = time.monotonic()

        img_head_camera = jpeg_to_img(rgb_dataset_head_camera[idx])
        img_left_camera = jpeg_to_img(rgb_dataset_left_camera[idx])
        img_right_camera = jpeg_to_img(rgb_dataset_right_camera[idx])

        decode_time = time.monotonic() - decode_start_time

        obs = {
            "joint_action": {
                "left_arm": left_arm_dataset[idx],
                "left_gripper": left_gripper_dataset[idx],
                "right_arm": right_arm_dataset[idx],
                "right_gripper": right_gripper_dataset[idx],
            },
            "observation": {
                "head_camera": img_head_camera,
                "left_camera": img_left_camera,
                "right_camera": img_right_camera,
            },
        }
        return obs, decode_time

    raise NotImplementedError(f"Unsupported packaging type: {packaging_type}")


def _wrap_web_payload(message_type: str, packaging_type: str, data):
    if packaging_type == "json":
        wrapped_data = numpy_to_json(data)
    else:
        wrapped_data = data

    if message_type == "obs":
        return {"type": "obs", "obs": wrapped_data}
    if message_type == "action":
        return {"type": "action", "action": wrapped_data}
    raise ValueError(f"Unsupported message type: {message_type}")


def _estimate_serialized_sizes(
    protocol: str,
    packaging_type: str,
    serializer,
    message_type: str,
    data,
):
    if protocol == "web":
        payload_obj = _wrap_web_payload(message_type, packaging_type, data)
    else:
        payload_obj = data

    payload_bytes = len(serializer.serialize(payload_obj))

    if protocol == "tcp":
        wire_bytes = payload_bytes + 4
    elif protocol == "udp":
        total_chunks = max(1, math.ceil(payload_bytes / MAX_CHUNK_SIZE))
        wire_bytes = payload_bytes + total_chunks * HEADER_SIZE
    elif protocol == "web":
        # WebSocket frame overhead is not tracked here, so this is app-layer bytes.
        wire_bytes = payload_bytes
    else:
        raise NotImplementedError(f"Unsupported protocol: {protocol}")

    return payload_bytes, wire_bytes


def _safe_stats(samples: List[float], prefix: str) -> Dict:
    if not samples:
        return {
            f"total_{prefix}": 0.0,
            f"avg_{prefix}": 0.0,
            f"min_{prefix}": 0.0,
            f"p50_{prefix}": 0.0,
            f"p95_{prefix}": 0.0,
            f"max_{prefix}": 0.0,
        }

    arr = np.asarray(samples, dtype=np.float64)
    return {
        f"total_{prefix}": float(arr.sum()),
        f"avg_{prefix}": float(arr.mean()),
        f"min_{prefix}": float(arr.min()),
        f"p50_{prefix}": float(np.percentile(arr, 50)),
        f"p95_{prefix}": float(np.percentile(arr, 95)),
        f"max_{prefix}": float(arr.max()),
    }


def _build_result(
    user_name: str,
    packaging_type: str,
    protocol: str,
    test_num: int,
    decode_time_total: float,
    total_elapsed_time: float,
    rtt_samples: List[float],
    obs_payload_samples: List[float],
    obs_wire_samples: List[float],
    action_payload_samples: List[float],
    action_wire_samples: List[float],
    timeout_count: int,
):
    rtt_array = np.asarray(rtt_samples, dtype=np.float64) if rtt_samples else np.asarray([], dtype=np.float64)
    total_round_trip_time = float(rtt_array.sum()) if len(rtt_array) else 0.0
    avg_decode_time = decode_time_total / test_num if test_num else 0.0
    avg_rtt = total_round_trip_time / test_num if test_num else 0.0
    successful_action_count = len(action_payload_samples)

    result = {
        "user_name": user_name,
        "packaging_type": packaging_type,
        "test_num": test_num,
        "avg_decode_time": avg_decode_time,
        "avg_RTT": avg_rtt,
        "total_decode_time": decode_time_total,
        "total_elapsed_time": total_elapsed_time,
        "total_round_trip_time": total_round_trip_time,
        "avg_step_time": (total_elapsed_time / test_num) if test_num else 0.0,
        "min_RTT": float(rtt_array.min()) if len(rtt_array) else 0.0,
        "p50_RTT": float(np.percentile(rtt_array, 50)) if len(rtt_array) else 0.0,
        "p95_RTT": float(np.percentile(rtt_array, 95)) if len(rtt_array) else 0.0,
        "max_RTT": float(rtt_array.max()) if len(rtt_array) else 0.0,
        "std_RTT": float(rtt_array.std()) if len(rtt_array) else 0.0,
        "fps": (test_num / total_round_trip_time) if total_round_trip_time > 0 else 0.0,
        "timeout_count": timeout_count,
        "successful_action_count": successful_action_count,
        "action_success_rate": (successful_action_count / test_num) if test_num else 0.0,
        "decode_time_ratio": (decode_time_total / total_elapsed_time) if total_elapsed_time > 0 else 0.0,
    }

    result.update(_safe_stats(obs_payload_samples, "obs_payload_bytes"))
    result.update(_safe_stats(obs_wire_samples, "obs_wire_bytes_est"))
    result.update(_safe_stats(action_payload_samples, "action_payload_bytes"))
    result.update(_safe_stats(action_wire_samples, "action_wire_bytes_est"))

    total_payload_bytes = result["total_obs_payload_bytes"] + result["total_action_payload_bytes"]
    total_wire_bytes_est = result["total_obs_wire_bytes_est"] + result["total_action_wire_bytes_est"]

    result["total_payload_bytes"] = total_payload_bytes
    result["total_wire_bytes_est"] = total_wire_bytes_est
    result["avg_total_payload_bytes"] = (total_payload_bytes / test_num) if test_num else 0.0
    result["avg_total_wire_bytes_est"] = (total_wire_bytes_est / test_num) if test_num else 0.0
    result["goodput_mbps"] = (total_payload_bytes * 8 / total_round_trip_time / 1e6) if total_round_trip_time > 0 else 0.0
    result["wire_goodput_mbps"] = (total_wire_bytes_est * 8 / total_round_trip_time / 1e6) if total_round_trip_time > 0 else 0.0

    print(f"Average decode time: {avg_decode_time:.4f} seconds")
    print(f"Average round-trip time: {avg_rtt:.4f} seconds")
    print(f"P95 RTT: {result['p95_RTT']:.4f} seconds")
    print(f"Estimated goodput: {result['goodput_mbps']:.4f} Mbps")
    print(f"Action success rate: {result['action_success_rate']:.2%}")

    return result


def _run_sync_test(
    server,
    protocol: str,
    packaging_type: str,
    test_file_path,
    is_jpeg: bool,
):
    serializer = create_serializer(packaging_type)
    user_name = "unknown_user"

    try:
        user_name_dict = server._recv_msg()

        if user_name_dict.get("type") == "user_name":
            user_name = user_name_dict.get("user_name", "unknown_user")
        else:
            print("Did not receive username, using default 'unknown_user'")
        print(f"User: {user_name}")

        with h5py.File(test_file_path, "r") as f:
            rgb_dataset_head_camera = f["observation/head_camera/rgb"]
            rgb_dataset_left_camera = f["observation/left_camera/rgb"]
            rgb_dataset_right_camera = f["observation/right_camera/rgb"]

            left_arm_dataset = f["joint_action/left_arm"][:]
            left_gripper_dataset = f["joint_action/left_gripper"][:]
            right_arm_dataset = f["joint_action/right_arm"][:]
            right_gripper_dataset = f["joint_action/right_gripper"][:]

            test_num = min(100, len(rgb_dataset_head_camera))
            print("test_num: ", test_num)

            decode_time_total = 0.0
            rtt_samples = []
            obs_payload_samples = []
            obs_wire_samples = []
            action_payload_samples = []
            action_wire_samples = []
            timeout_count = 0
            start_time = time.monotonic()

            for idx in range(test_num):
                obs, decode_time = _build_obs(
                    packaging_type,
                    is_jpeg,
                    rgb_dataset_head_camera,
                    rgb_dataset_left_camera,
                    rgb_dataset_right_camera,
                    left_arm_dataset,
                    left_gripper_dataset,
                    right_arm_dataset,
                    right_gripper_dataset,
                    idx,
                )
                decode_time_total += decode_time

                obs_payload_bytes, obs_wire_bytes = _estimate_serialized_sizes(
                    protocol,
                    packaging_type,
                    serializer,
                    "obs",
                    obs,
                )
                obs_payload_samples.append(obs_payload_bytes)
                obs_wire_samples.append(obs_wire_bytes)

                round_trip_start = time.monotonic()
                server.post_obs(obs)
                action = None
                try:
                    action = server.get_action()
                except TimeoutError:
                    timeout_count += 1
                    print("No action received (timeout)")
                round_trip_duration = time.monotonic() - round_trip_start
                rtt_samples.append(round_trip_duration)

                if action is not None:
                    action_payload_bytes, action_wire_bytes = _estimate_serialized_sizes(
                        protocol,
                        packaging_type,
                        serializer,
                        "action",
                        action,
                    )
                    action_payload_samples.append(action_payload_bytes)
                    action_wire_samples.append(action_wire_bytes)

            total_elapsed_time = time.monotonic() - start_time

            return _build_result(
                user_name=user_name,
                packaging_type=packaging_type,
                protocol=protocol,
                test_num=test_num,
                decode_time_total=decode_time_total,
                total_elapsed_time=total_elapsed_time,
                rtt_samples=rtt_samples,
                obs_payload_samples=obs_payload_samples,
                obs_wire_samples=obs_wire_samples,
                action_payload_samples=action_payload_samples,
                action_wire_samples=action_wire_samples,
                timeout_count=timeout_count,
            )
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()


def run_udp(host, port, packaging_type, test_file_path, is_jpeg: bool, io_timeout_seconds: float = 10.0):
    server = UDPServer(host, port, packaging_type, io_timeout=io_timeout_seconds)
    return _run_sync_test(server, "udp", packaging_type, test_file_path, is_jpeg)


def run_tcp(
    host,
    port,
    packaging_type,
    test_file_path,
    is_jpeg: bool,
    io_timeout_seconds: float = 10.0,
    accept_timeout_seconds: float = 0.0,
):
    server = TCPServer(
        host,
        port,
        packaging_type,
        io_timeout=io_timeout_seconds,
        accept_timeout=(accept_timeout_seconds if accept_timeout_seconds and accept_timeout_seconds > 0 else None),
    )
    try:
        server.accept_connection()
    except Exception:
        server.close()
        raise
    return _run_sync_test(server, "tcp", packaging_type, test_file_path, is_jpeg)


async def run_web(
    host,
    port,
    packaging_type,
    test_file_path,
    is_jpeg: bool,
    action_timeout_seconds: float = 10.0,
    connection_timeout_seconds: float = 30.0,
):
    server = WebServer(host, port, packaging_type)
    serializer = create_serializer(packaging_type)
    user_name = "unknown_user"

    server_task = asyncio.create_task(server.start())

    try:
        print("Waiting for client...")
        await asyncio.wait_for(server._connected_event.wait(), timeout=connection_timeout_seconds)
        print("Client connected!")

        user_name_dict = await asyncio.wait_for(server._recv_msg(), timeout=action_timeout_seconds)

        if user_name_dict.get("type") == "user_name":
            user_name = user_name_dict.get("user_name", "unknown_user")
        else:
            print("Did not receive user name, using default 'unknown_user'")
        print("User: ", user_name)

        with h5py.File(test_file_path, "r") as f:
            rgb_dataset_head_camera = f["observation/head_camera/rgb"]
            rgb_dataset_left_camera = f["observation/left_camera/rgb"]
            rgb_dataset_right_camera = f["observation/right_camera/rgb"]

            left_arm_dataset = f["joint_action/left_arm"][:]
            left_gripper_dataset = f["joint_action/left_gripper"][:]
            right_arm_dataset = f["joint_action/right_arm"][:]
            right_gripper_dataset = f["joint_action/right_gripper"][:]

            test_num = min(100, len(rgb_dataset_head_camera))
            print("test_num: ", test_num)

            decode_time_total = 0.0
            rtt_samples = []
            obs_payload_samples = []
            obs_wire_samples = []
            action_payload_samples = []
            action_wire_samples = []
            timeout_count = 0
            start_time = time.monotonic()

            for idx in range(test_num):
                obs, decode_time = _build_obs(
                    packaging_type,
                    is_jpeg,
                    rgb_dataset_head_camera,
                    rgb_dataset_left_camera,
                    rgb_dataset_right_camera,
                    left_arm_dataset,
                    left_gripper_dataset,
                    right_arm_dataset,
                    right_gripper_dataset,
                    idx,
                )
                decode_time_total += decode_time

                obs_payload_bytes, obs_wire_bytes = _estimate_serialized_sizes(
                    "web",
                    packaging_type,
                    serializer,
                    "obs",
                    obs,
                )
                obs_payload_samples.append(obs_payload_bytes)
                obs_wire_samples.append(obs_wire_bytes)

                round_trip_start = time.monotonic()
                await server.post_obs(obs)

                action = None
                try:
                    action = await server.get_action(timeout=action_timeout_seconds)
                    print("Received action:", action)
                except TimeoutError:
                    timeout_count += 1
                    print("No action received (timeout)")

                round_trip_duration = time.monotonic() - round_trip_start
                rtt_samples.append(round_trip_duration)

                if action is not None:
                    action_payload_bytes, action_wire_bytes = _estimate_serialized_sizes(
                        "web",
                        packaging_type,
                        serializer,
                        "action",
                        action,
                    )
                    action_payload_samples.append(action_payload_bytes)
                    action_wire_samples.append(action_wire_bytes)

            total_elapsed_time = time.monotonic() - start_time

            return _build_result(
                user_name=user_name,
                packaging_type=packaging_type,
                protocol="web",
                test_num=test_num,
                decode_time_total=decode_time_total,
                total_elapsed_time=total_elapsed_time,
                rtt_samples=rtt_samples,
                obs_payload_samples=obs_payload_samples,
                obs_wire_samples=obs_wire_samples,
                action_payload_samples=action_payload_samples,
                action_wire_samples=action_wire_samples,
                timeout_count=timeout_count,
            )
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
