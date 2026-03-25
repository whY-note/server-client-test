import h5py
import numpy as np
import os
import cv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_dir = os.path.join(BASE_DIR, "../data")
file_name = "episode0.hdf5"
file_path = os.path.join(file_dir, file_name)
print(f"file path: {file_path}")

with h5py.File(file_path, "r") as f:

    left_arm = f["joint_action/left_arm"][:]          # (678,6)
    print(left_arm.shape)
    print(type(left_arm))
    left_gripper = f["joint_action/left_gripper"][:]  # (678,)
    print(left_gripper.shape)
    print(type(left_gripper))
    
    rgb_bytes = f["observation/head_camera/rgb"][0]  # 第0帧
    
    print(type(rgb_bytes)) # type: np.bytes_
    # ⚠ 这是 bytes，不是图像

    img_array = np.frombuffer(rgb_bytes, dtype=np.uint8)

    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR) # 这是图像
    if img is None:
        raise ValueError("图像解码失败，无法进行通道转换")

    # OpenCV 解码结果默认是 BGR(历史遗留问题)，这里做通道反转（BGR --> RGB）
    # img_reversed = img[:, :, ::-1] # 方法一：切片反转
    img_reversed = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # 方法二：OpenCV 提供的颜色空间转换函数 （更清晰）

    print(type(img)) # type: np.ndarray
    print(img.shape)

    # 保存图像
    cv2.imwrite("frame0.png", img)
    cv2.imwrite("frame0_reversed.png", img_reversed)