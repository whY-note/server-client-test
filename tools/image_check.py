import numpy as np


def compute_mse(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    计算 Mean Squared Error
    img1, img2: numpy array, shape 相同
    MSE 越小表示两张图像越相似，MSE=0 表示完全相同
    """
    if img1.shape != img2.shape:
        raise ValueError("两张图像尺寸必须相同")

    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    return mse

def compute_psnr(img1: np.ndarray, img2: np.ndarray, max_pixel: float = 255.0) -> float:
    """
    计算 Peak Signal-to-Noise Ratio, PSNR
    PSNR 越大表示两张图像越相似，PSNR=inf 表示完全相同
    """
    mse = compute_mse(img1, img2)

    if mse == 0:
        return float("inf")

    psnr = 10 * np.log10((max_pixel ** 2) / mse)
    return psnr


from skimage.metrics import structural_similarity as ssim
def compute_ssim(img1, img2):
    """
    计算 Structural Similarity Index
    支持彩色图像
    SSIM 越接近 1 表示两张图像越相似，SSIM=1 表示完全相同
    """
    if img1.shape != img2.shape:
        raise ValueError("两张图像尺寸必须相同")

    score = ssim(img1, img2, channel_axis=-1)
    return score

import cv2
def decode_jpeg(jpeg_bytes):
    """
    JPEG bytes -> numpy image
    """
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def compare_camera(h5_file1, h5_file2, cam_name):
    """
    比较某个 camera 的所有帧
    """

    rgb1 = h5_file1[f"observation/{cam_name}/rgb"]
    rgb2 = h5_file2[f"observation/{cam_name}/rgb"]

    n = min(len(rgb1), len(rgb2))

    mse_list = []
    psnr_list = []
    ssim_list = []

    for i in range(n):

        img1 = decode_jpeg(rgb1[i])
        img2 = decode_jpeg(rgb2[i])

        mse = compute_mse(img1, img2)
        psnr = compute_psnr(img1, img2)
        ssim_score = compute_ssim(img1, img2)

        mse_list.append(mse)
        psnr_list.append(psnr)
        ssim_list.append(ssim_score)

        # print(f"{cam_name} frame {i}:")
        # print(f"  MSE  = {mse:.4f}")
        # print(f"  PSNR = {psnr:.4f}")
        # print(f"  SSIM = {ssim_score:.4f}")

    print("\n===== SUMMARY =====")
    print(f"{cam_name}")
    print(f"Mean MSE  : {np.mean(mse_list):.4f}")
    print(f"Mean PSNR : {np.mean(psnr_list):.4f}")
    print(f"Mean SSIM : {np.mean(ssim_list):.4f}")
    print()

    return mse_list, psnr_list, ssim_list

if __name__ == "__main__":
    PROTOCOL = "web" # "tcp" or "web"
    PACKAGING_TYPE = "pickle" # "json", "msgpack" or "pickle"
    print("PROTOCOL: ", PROTOCOL)
    print("PACKAGING_TYPE: ", PACKAGING_TYPE)

    import h5py
    hdf5_file1 = "./data/episode0.hdf5" # origin
    hdf5_file2 = "./data/episode0_"+ PROTOCOL +"_client_"+ PACKAGING_TYPE +".hdf5" # recorded by tcp client or web client

    with h5py.File(hdf5_file1, "r") as f1, h5py.File(hdf5_file2, "r") as f2:

        for cam in ["head_camera", "left_camera", "right_camera"]:

            print("\n==============================")
            print(f"Comparing camera: {cam}")
            print("==============================")

            compare_camera(f1, f2, cam)