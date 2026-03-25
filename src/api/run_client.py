from src.base.base_client import BaseClient
from src.tcp.tcp_client import TCPClient
from src.web.web_client import WebClient
from src.udp.udp_client import UDPClient

from websockets.exceptions import ConnectionClosedOK
from websockets.exceptions import ConnectionClosedError

from src.utils.utils import jpeg_to_img
import re
import time

def create_client(protocol, packaging_type) -> BaseClient:
    if protocol == "tcp":
        return TCPClient(packaging_type=packaging_type)
    elif protocol == "web":
        return WebClient(packaging_type=packaging_type)
    elif protocol == "udp":
        return UDPClient(packaging_type=packaging_type)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")

def input_user_name() -> str:
    while True:
        user_name = input("Please enter your user_name (only contain letters, numbers, and underscores.) : ").strip()

        try:
            return validate_user_name(user_name)
        except ValueError as exc:
            print(exc)

def validate_user_name(user_name: str) -> str:
    if not user_name:
        raise ValueError("user_name cannot be empty.")

    if not re.fullmatch(r"[A-Za-z0-9_]+", user_name):
        raise ValueError("user_name can only contain letters, numbers, and underscores.")

    return user_name

def connect_with_retry(client, host, port, connect_retry_seconds: float, retry_interval: float):
    deadline = time.monotonic() + connect_retry_seconds
    attempt = 0

    while True:
        attempt += 1
        try:
            client.connect(host, port)
            return
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if connect_retry_seconds <= 0 or time.monotonic() >= deadline:
                raise exc

            remaining = max(0.0, deadline - time.monotonic())
            sleep_seconds = min(retry_interval, remaining)
            print(
                f"[INFO] Connect attempt {attempt} failed: {exc}. "
                f"Retrying in {sleep_seconds:.1f} seconds..."
            )
            time.sleep(sleep_seconds)


def run_client(
    protocol,
    host,
    port,
    packaging_type,
    user_name: str | None = None,
    connect_retry_seconds: float = 0,
    retry_interval: float = 1.0,
):
    client = create_client(protocol, packaging_type)
    connected = False
    
    try:
        connect_with_retry(
            client,
            host,
            port,
            connect_retry_seconds=connect_retry_seconds,
            retry_interval=retry_interval,
        )
        connected = True
        print("[INFO] Connected.")

        # 等待用户在命令行输入用户名，然后发给server
        if user_name is None:
            user_name = input_user_name()
        else:
            user_name = validate_user_name(user_name)

        client._send_msg({"type": "user_name", "user_name": user_name})
    
        while True:
            finished = client.step()
            if finished:
                break
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
    except ConnectionError:
        print("[INFO] Server exited.")
    except ConnectionClosedOK:
        print("[INFO] Connection closed by server.")
    except ConnectionClosedError as e:
        print(f"[ERROR] Connection closed with error: {e}")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        print("[INFO] Closing connection.")
        if connected:
            client.close()
        else:
            print("[INFO] Connection was not established.")
        print("[INFO] Client exited.")
