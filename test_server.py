from src.utils.utils import load_yaml, get_config_path, list_test_config_names
from src.api.run_server import run_udp, run_tcp, run_web
from src.api.control_plane import recv_json_message, send_json_message, DEFAULT_DATA_PORTS
import asyncio
import os
import pandas as pd
import argparse
import traceback
import sys
import socket
import threading

def parse_args():
    parser = argparse.ArgumentParser(description="Test server script")

    parser.add_argument(
        "--test",
        type=str,
        required=False,
        default=None,
        help="Test number"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all ./config/test_*.yml configs in order"
    )
    parser.add_argument(
        "--host",
        type=str,
        required=False,
        default="0.0.0.0",
        help="Server bind host"
    )
    parser.add_argument(
        "--port",
        type=int,
        required=False,
        default=9000,
        help="Server bind port"
    )

    args = parser.parse_args()
    return args

def record_result(res, config_name):
    user_name = res.get("user_name", "unknown_user")

    user_name = user_name.replace(" ", "_") # 替换空格为下划线，避免文件路径问题

    # 创建用户目录
    dir_path = os.path.join("result", user_name)
    os.makedirs(dir_path, exist_ok=True)

    # 转成 DataFrame
    df = pd.DataFrame([res])

    # CSV 路径
    file_path = os.path.join(dir_path, "all_tests.csv")

    # 如果文件已存在，则对齐列后整体重写，避免新旧 schema 混乱
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        combined_columns = list(dict.fromkeys(existing_df.columns.tolist() + df.columns.tolist()))
        existing_df = existing_df.reindex(columns=combined_columns)
        df = df.reindex(columns=combined_columns)
        pd.concat([existing_df, df], ignore_index=True).to_csv(file_path, mode="w", header=True, index=False)
    else:
        df.to_csv(file_path, mode="w", header=True, index=False)


def run_single_test(config_name: str, host: str, port: int, config_override: dict | None = None):
    if config_override is None:
        config_path = get_config_path(config_name)
        print(f"Loading config from {config_path}")
        config = load_yaml(config_path)
    else:
        print(f"Loading config from client payload for {config_name}")
        config = config_override

    protocol = config["protocol"]
    packaging_type = config["packaging_type"]
    is_jpeg = config["is_jpeg"]
    io_timeout_seconds = float(config.get("io_timeout_seconds", 10.0))
    action_timeout_seconds = float(config.get("action_timeout_seconds", io_timeout_seconds))
    accept_timeout_seconds = float(config.get("accept_timeout_seconds", 0.0))
    connection_timeout_seconds = float(config.get("connection_timeout_seconds", 30.0))

    print("Config: ")
    print("Protocol: ", protocol)
    print("Packaging type: ", packaging_type)
    print("Host: ", host)
    print("Port: ", port)
    print("is_jpeg: ", is_jpeg)

    test_file_name = config["test_file_name"]
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_dir = os.path.join(BASE_DIR, "data")
    file_path = os.path.join(file_dir, test_file_name)
    print(f"Test file path: {file_path}")

    try:
        if protocol == "tcp":
            res = run_tcp(
                host = host,
                port = port,
                packaging_type = packaging_type,
                test_file_path = file_path,
                is_jpeg = is_jpeg,
                io_timeout_seconds = io_timeout_seconds,
                accept_timeout_seconds = accept_timeout_seconds,
            )
        elif protocol == "web":
            res = asyncio.run(
                run_web(
                    host=host,
                    port=port,
                    packaging_type=packaging_type,
                    test_file_path = file_path,
                    is_jpeg = is_jpeg,
                    action_timeout_seconds=action_timeout_seconds,
                    connection_timeout_seconds=connection_timeout_seconds,
                )
                )
        elif protocol == "udp": 
            res = run_udp(
                host = host,
                port = port,
                packaging_type = packaging_type,
                test_file_path = file_path,
                is_jpeg = is_jpeg,
                io_timeout_seconds = io_timeout_seconds,
            )
        else:
            raise NotImplementedError(f"Unsupported protocol: {protocol}")

        res["status"] = "success"
        success = True
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"[ERROR] {config_name} failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        res = {
            "user_name": "unknown_user",
            "packaging_type": packaging_type,
            "test_num": 0,
            "status": "failed",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
        success = False

    res["protocol"] = protocol
    res["config"] = config_name
    res["is_jpeg"] = is_jpeg

    # 保存结果
    record_result(res, config_name)
    return success


def control_server(host: str, control_port: int, worker_host: str = "0.0.0.0"):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, control_port))
    server_socket.listen(5)

    print(f"Control server listening on {host}:{control_port}")

    try:
        while True:
            print("Waiting for control client...")
            conn, addr = server_socket.accept()
            print(f"Control client connected from {addr}")

            with conn:
                try:
                    request = recv_json_message(conn)
                    if request.get("type") != "start_test":
                        raise ValueError(f"Unsupported control message: {request.get('type')}")

                    config_name = request["config_name"]
                    config = request["config"]
                    protocol = config["protocol"]

                    if protocol not in DEFAULT_DATA_PORTS:
                        raise NotImplementedError(f"Unsupported protocol: {protocol}")
                    data_port = DEFAULT_DATA_PORTS[protocol]

                    worker = threading.Thread(
                        target=run_single_test,
                        args=(config_name, worker_host, data_port, config),
                        daemon=True,
                    )
                    worker.start()

                    send_json_message(
                        conn,
                        {
                            "status": "ready",
                            "data_port": data_port,
                            "protocol": protocol,
                            "config_name": config_name,
                        },
                    )

                    worker.join()
                except Exception as exc:
                    print(f"[ERROR] Control request failed: {type(exc).__name__}: {exc}")
                    traceback.print_exc()
                    try:
                        send_json_message(
                            conn,
                            {
                                "status": "error",
                                "error_type": type(exc).__name__,
                                "error_message": str(exc),
                            },
                        )
                    except Exception:
                        pass
    except KeyboardInterrupt:
        print("\nControl server stopped.")
    finally:
        server_socket.close()


if __name__ == "__main__":

    args = parse_args()

    if args.all and args.test is not None:
        raise ValueError("--all and --test cannot be used together.")

    if args.all:
        config_names = list_test_config_names()
        if not config_names:
            raise FileNotFoundError("No test configs found under ./config/test_*.yml")

        print(f"Batch mode enabled, total configs: {len(config_names)}")
        failed_configs = []
        for index, config_name in enumerate(config_names, start=1):
            print(f"\n===== [{index}/{len(config_names)}] Running {config_name} =====")
            success = run_single_test(config_name, host=args.host, port=args.port)
            if not success:
                failed_configs.append(config_name)

        if failed_configs:
            print("\nBatch finished with failures:")
            for config_name in failed_configs:
                print(f"- {config_name}")
        else:
            print("\nBatch finished successfully.")
    elif args.test is not None:
        config_name = "test_" + args.test
        success = run_single_test(config_name, host=args.host, port=args.port)
        if not success:
            sys.exit(1)
    else:
        control_server(host=args.host, control_port=args.port)
