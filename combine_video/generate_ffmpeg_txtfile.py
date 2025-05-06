import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

BASE_DIR = "/users/xcong2/data/brics/non-pii/brics-studio"
DATE = "2025-04-23"
DATE_DIR = os.path.join(BASE_DIR, DATE)
local_save_dir = "/users/xcong2/data/users/xcong2/projects/BRICS_DataLoader/local_save_dir"
os.makedirs(local_save_dir, exist_ok=True)
idx_1 = "174562411"
idx_2 = "174562429"

cam_list = os.listdir(DATE_DIR)
valid_cam_list = {}
for cam in cam_list:
    cam_dir = os.path.join(DATE_DIR, cam)
    VIDEO_NAME = sorted([f for f in os.listdir(cam_dir) if f.endswith('.mp4')])
    VIDEO_1_path = [f for f in VIDEO_NAME if f.startswith(cam+"_"+idx_1)]
    VIDEO_2_path = [f for f in VIDEO_NAME if f.startswith(cam+"_"+idx_2)]
    if len(VIDEO_1_path) == 0 or len(VIDEO_2_path) == 0:
        print(f"--- Warning: Camera {cam} has no video files. Skipping. ---")
        continue
    VIDEO_1_path = os.path.join(cam_dir, VIDEO_1_path[0])
    VIDEO_2_path = os.path.join(cam_dir, VIDEO_2_path[0])
    save_txt_dir = os.path.join(local_save_dir, cam)
    os.makedirs(save_txt_dir, exist_ok=True)
    with open(os.path.join(save_txt_dir, VIDEO_1_path.split("/")[-1].replace(".mp4", ".txt")), "a") as f:
        f.write(f"file '{VIDEO_1_path}'\nfile '{VIDEO_2_path}'\n")
