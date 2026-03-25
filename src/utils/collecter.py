import h5py
import numpy as np

class Collector:

    def __init__(self):

        # joint_action buffer
        self.joint_action = {
            "left_arm": [],
            "left_gripper": [],
            "right_arm": [],
            "right_gripper": []
        }

        # observation buffer
        self.observation = {
            "head_camera": {"rgb": []},
            "left_camera": {"rgb": []},
            "right_camera": {"rgb": []}
        }

    def collect(self, obs):
        """
        每收到一帧 obs 调用一次
        """

        # -------------------------
        # joint_action
        # -------------------------
        ja = obs["joint_action"]

        self.joint_action["left_arm"].append(ja["left_arm"])
        self.joint_action["left_gripper"].append(ja["left_gripper"])
        self.joint_action["right_arm"].append(ja["right_arm"])
        self.joint_action["right_gripper"].append(ja["right_gripper"])

        # -------------------------
        # observation
        # -------------------------
        ob = obs["observation"]

        for cam in ["head_camera", "left_camera", "right_camera"]:
            self.observation[cam]["rgb"].append(
                ob[cam]
            )

    def save_hdf5(self, hdf5_path):

        with h5py.File(hdf5_path, "w") as f:

            # =========================
            # joint_action
            # =========================
            g_action = f.create_group("joint_action")

            for key, value in self.joint_action.items():

                g_action.create_dataset(
                    key,
                    data=np.array(value)
                )

            # =========================
            # observation
            # =========================
            g_obs = f.create_group("observation")

            for cam in self.observation:

                g_cam = g_obs.create_group(cam)

                rgb_list = self.observation[cam]["rgb"]
                rgb_np = [np.bytes_(b) for b in rgb_list] # 转换为 np.bytes_ 类型，适合存储在 HDF5 中

                g_cam.create_dataset(
                    "rgb",
                    data=rgb_np
                )

        print(f"HDF5 saved to {hdf5_path}")