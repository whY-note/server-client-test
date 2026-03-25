from src.utils.utils import load_yaml
from src.api.run_server import run_udp, run_tcp, run_web
import asyncio
import os
import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Test server script")

    parser.add_argument(
        "--test",
        type=str,
        required=False,
        default=None,
        help="Test number"
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

    # 如果文件已存在就追加
    if os.path.exists(file_path):
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        df.to_csv(file_path, mode="w", header=True, index=False)


if __name__ == "__main__":

    args = parse_args()

    if args.test is None:
        config_name = "default" # 采用默认配置
        print("No test specified, using default config.")
    else:
        config_name = "test_" + args.test
    config_path = "./config/"+ config_name +".yml"
    print(f"Loading config from {config_path}")
    config = load_yaml(config_path)

    protocol = config["protocol"]
    packaging_type = config["packaging_type"]
    host = config["server"]["host"]
    port = config["server"]["port"]
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
    
    res["protocol"] = protocol
    res["config"] = config_name
    res["is_jpeg"] = is_jpeg
    
    # 保存结果
    record_result(res, config_name)
    


