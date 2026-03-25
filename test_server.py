from src.utils.utils import load_yaml, get_config_path, list_test_config_names
from src.api.run_server import run_udp, run_tcp, run_web
import asyncio
import os
import pandas as pd
import argparse
import traceback
import sys

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
    file_path = os.path.join(dir_path, f"{config_name}.csv")

    # 如果文件已存在，则对齐列后整体重写，避免新旧 schema 混乱
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        combined_columns = list(dict.fromkeys(existing_df.columns.tolist() + df.columns.tolist()))
        existing_df = existing_df.reindex(columns=combined_columns)
        df = df.reindex(columns=combined_columns)
        pd.concat([existing_df, df], ignore_index=True).to_csv(file_path, mode="w", header=True, index=False)
    else:
        df.to_csv(file_path, mode="w", header=True, index=False)


def run_single_test(config_name: str, host: str, port: int):
    config_path = get_config_path(config_name)
    print(f"Loading config from {config_path}")
    config = load_yaml(config_path)

    protocol = config["protocol"]
    packaging_type = config["packaging_type"]
    is_jpeg = config["is_jpeg"]

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
            res = run_tcp(host = host, port = port, packaging_type = packaging_type, test_file_path = file_path, is_jpeg = is_jpeg)
        elif protocol == "web":
            res = asyncio.run(
                run_web(host=host, port=port, packaging_type=packaging_type, test_file_path = file_path, is_jpeg = is_jpeg)
                )
        elif protocol == "udp": 
            res = run_udp(host = host, port = port, packaging_type = packaging_type, test_file_path = file_path, is_jpeg = is_jpeg)
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
    else:
        if args.test is None:
            config_name = "default" # 采用默认配置
            print("No test specified, using default config.")
        else:
            config_name = "test_" + args.test
        success = run_single_test(config_name, host=args.host, port=args.port)
        if not success:
            sys.exit(1)
