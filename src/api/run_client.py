from src.base.base_client import BaseClient
from src.tcp.tcp_client import TCPClient
from src.web.web_client import WebClient
from src.udp.udp_client import UDPClient

from websockets.exceptions import ConnectionClosedOK
from websockets.exceptions import ConnectionClosedError

from src.utils.utils import jpeg_to_img
import re

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

        if not user_name:
            print("user_name cannot be empty.")
            continue

        if not re.fullmatch(r"[A-Za-z0-9_]+", user_name):
            print("user_name can only contain letters, numbers, and underscores.")
            continue

        break
    return user_name

def run_client(protocol, host, port, packaging_type):
    client = create_client(protocol, packaging_type)
    
    try:
        client.connect(host, port)
        print("[INFO] Connected.")

        # 等待用户在命令行输入用户名，然后发给server
        user_name = input_user_name()

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
        client.close()
        print("[INFO] Client exited.")