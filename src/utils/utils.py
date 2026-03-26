import numpy as np
import cv2
import yaml
import glob
import os
import re
from typing import List, Optional

def jpeg_to_img(jpeg_bytes):
    ''' 将 JPEG bytes 解码为 原始帧'''
    img_array = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR) # np.ndarray
    return img

# load yaml
def load_yaml(yml_path: str = "./config/config.yaml") -> dict:
    """
    读取 YAML 配置文件并返回 dict
    """
    with open(yml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def get_config_path(config_name: str, config_dir: Optional[str] = None) -> str:
    if config_dir is None:
        config_dir = os.path.join(get_project_root(), "config")
    return os.path.join(config_dir, f"{config_name}.yml")


def list_test_config_names(config_dir: Optional[str] = None) -> List[str]:
    if config_dir is None:
        config_dir = os.path.join(get_project_root(), "config")

    config_paths = glob.glob(os.path.join(config_dir, "test_*.yml"))
    config_names = [
        os.path.splitext(os.path.basename(config_path))[0]
        for config_path in config_paths
    ]

    def sort_key(config_name: str):
        match = re.fullmatch(r"test_(\d+)", config_name)
        if match:
            return (0, int(match.group(1)))
        return (1, config_name)

    return sorted(config_names, key=sort_key)
