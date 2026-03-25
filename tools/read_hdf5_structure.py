import h5py
import os

def print_hdf5_structure(name, obj):
    if isinstance(obj, h5py.Dataset):
        print(f"[DATASET] {name}  shape={obj.shape}  dtype={obj.dtype}")
    elif isinstance(obj, h5py.Group):
        print(f"[GROUP]   {name}")

def inspect_hdf5(file_path):
    with h5py.File(file_path, "r") as f:
        print(f"\nFile: {file_path}\n")
        f.visititems(print_hdf5_structure)

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    file_dir = os.path.join(BASE_DIR, "../data")
    # file_name = "episode0.hdf5"
    file_name = "episode0_tcp_client.hdf5"
    file_path = os.path.join(file_dir, file_name)
    
    print(f"file path: {file_path}")
    inspect_hdf5(file_path)
    