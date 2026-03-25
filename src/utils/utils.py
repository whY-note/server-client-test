import numpy as np
import cv2
import yaml

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