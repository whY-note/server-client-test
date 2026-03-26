from src.utils.utils import load_yaml, get_config_path, list_test_config_names
from src.api.run_client import run_client, input_user_name
from src.api.control_plane import request_test_session
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
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all ./config/test_*.yml configs in order"
    )
    parser.add_argument(
        "--user-name",
        type=str,
        required=False,
        default=None,
        help="User name sent to server"
    )
    parser.add_argument(
        "--host",
        type=str,
        required=False,
        default="localhost",
        help="Server host to connect to"
    )
    parser.add_argument(
        "--port",
        type=int,
        required=False,
        default=9000,
        help="Server control port to connect to"
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Connect directly to a pre-started data server without control plane"
    )
    parser.add_argument(
        "--jpeg-only",
        action="store_true",
        help="When used with --all, only run configs whose is_jpeg is true"
    )

    args = parser.parse_args()
    return args


def run_single_test(
    config_name: str,
    host: str,
    port: int,
    user_name: str | None = None,
    connect_retry_seconds: float = 0,
    direct: bool = False,
):
    config_path = get_config_path(config_name)
    print(f"Loading config from {config_path}")
    config = load_yaml(config_path)

    protocol = config["protocol"]
    packaging_type = config["packaging_type"]
    connect_timeout_seconds = float(config.get("connect_timeout_seconds", 10.0))
    io_timeout_seconds = float(config.get("io_timeout_seconds", 10.0))

    print("Config: ")
    print("Protocol: ", protocol)
    print("Packaging type: ", packaging_type)
    print("Host: ", host)
    print("Control port: ", port)

    if direct:
        data_port = port
    else:
        response = request_test_session(
            host,
            port,
            {
                "type": "start_test",
                "config_name": config_name,
                "config": config,
            },
        )

        if response.get("status") != "ready":
            raise RuntimeError(
                f"Control plane failed: {response.get('error_type', 'UnknownError')}: "
                f"{response.get('error_message', response)}"
            )

        data_port = response["data_port"]
        print(f"Worker ready on data port: {data_port}")

    run_client(
        protocol,
        host,
        data_port,
        packaging_type,
        user_name=user_name,
        connect_retry_seconds=connect_retry_seconds,
        connect_timeout_seconds=connect_timeout_seconds,
        io_timeout_seconds=io_timeout_seconds,
    )

if __name__ == "__main__":

    args = parse_args()

    if args.all and args.test is not None:
        raise ValueError("--all and --test cannot be used together.")

    if args.all:
        config_names = list_test_config_names()
        if not config_names:
            raise FileNotFoundError("No test configs found under ./config/test_*.yml")

        if args.jpeg_only:
            filtered_config_names = []
            for config_name in config_names:
                config = load_yaml(get_config_path(config_name))
                if config.get("is_jpeg") is True:
                    filtered_config_names.append(config_name)
            config_names = filtered_config_names

        if not config_names:
            raise FileNotFoundError("No matching test configs found for the selected filters.")

        user_name = args.user_name if args.user_name is not None else input_user_name()
        print(f"Batch mode enabled, total configs: {len(config_names)}")
        if args.jpeg_only:
            print("Filter enabled: only running configs with is_jpeg = true")

        for index, config_name in enumerate(config_names, start=1):
            print(f"\n===== [{index}/{len(config_names)}] Running {config_name} =====")
            run_single_test(
                config_name,
                host=args.host,
                port=args.port,
                user_name=user_name,
                connect_retry_seconds=30,
                direct=args.direct,
            )
    else:
        if args.test is None:
            config_name = "default" # 采用默认配置
            print("No test specified, using default config.")
        else:
            config_name = "test_" + args.test
        run_single_test(
            config_name,
            host=args.host,
            port=args.port,
            user_name=args.user_name,
            direct=args.direct,
        )
