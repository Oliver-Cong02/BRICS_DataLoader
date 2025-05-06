import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

BASE_DIR = "/users/xcong2/data/brics/non-pii/brics-studio"
DATE = "2025-04-23"
DATE_DIR = os.path.join(BASE_DIR, DATE)
local_save_dir = "/users/xcong2/data/users/xcong2/projects/BRICS_DataLoader/mydata/2025-04-23"
os.makedirs(local_save_dir, exist_ok=True)
idx_1 = "174562411"
idx_2 = "174562429"

cam_list = os.listdir(DATE_DIR)
valid_cam_list = {}
for cam in cam_list:
    cam_dir = os.path.join(DATE_DIR, cam)
    txt_list = sorted([f for f in os.listdir(cam_dir) if f.endswith('.txt')])
    txt_1_path = [f for f in txt_list if f.startswith(cam+"_"+idx_1)]
    txt_2_path = [f for f in txt_list if f.startswith(cam+"_"+idx_2)]
    if len(txt_1_path) == 0 or len(txt_2_path) == 0:
        print(f"--- Warning: Camera {cam} has no video files. Skipping. ---")
        continue

    txt_1_path = os.path.join(cam_dir, txt_1_path[0])
    txt_2_path = os.path.join(cam_dir, txt_2_path[0])

    # combine txt_1 and txt_2
    with open(txt_1_path, "r") as f:
        txt_1 = f.read()
    with open(txt_2_path, "r") as f:
        txt_2 = f.read()
    with open(os.path.join(local_save_dir, cam, txt_1_path.split("/")[-1]), "w") as f:
        f.write(txt_1)
        if txt_1.endswith("\n"):
            f.write(txt_2)
        else:
            f.write("\n"+txt_2)
    
