from src.utils.utils import load_yaml
from src.api.run_client import run_client
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
    host = config["client"]["host"]
    port = config["client"]["port"]

    print("Config: ")
    print("Protocol: ", protocol)
    print("Packaging type: ", packaging_type)
    print("Host: ", host)
    print("Port: ", port)

    run_client(protocol, host, port, packaging_type)
