import os
import subprocess
import multiprocessing
from functools import partial
import torch
from torchcodec.decoders import VideoDecoder
from PIL import Image

DATA_DIR = "/users/xcong2/data/brics/non-pii/brics-studio"
DATE = "2025-04-10"
SEQ_IDX = 1

LOCAL_SAVE_BASE_DIR = "/users/xcong2/data/users/xcong2/projects/BRICS_DataLoader/local_test"
os.makedirs(LOCAL_SAVE_BASE_DIR, exist_ok=True)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AVLTREE_PATH = os.path.join(CURRENT_DIR, "avltree")

CAMERA_LIST = os.listdir(os.path.join(DATA_DIR, DATE))
CAMERA_LIST = [camera for camera in CAMERA_LIST if 'cam' in camera]

def Build_AVLtree():
    if not os.path.exists(AVLTREE_PATH):
        print(f"Error: AVLTree executable not found at {AVLTREE_PATH}")
        return
    avl_save_dir = os.path.join(LOCAL_SAVE_BASE_DIR, DATE, f"SEQ_IDX_{SEQ_IDX:04d}")
    os.makedirs(avl_save_dir, exist_ok=True)

    for camera in CAMERA_LIST:
        print(" --------------------------------------------- ")
        timecode_txt = sorted([f for f in os.listdir(os.path.join(DATA_DIR, DATE, camera)) if f.endswith('.txt')])[SEQ_IDX]
        txt_path = os.path.join(DATA_DIR, DATE, camera, timecode_txt)
        
        camera_save_dir = os.path.join(avl_save_dir, camera)
        if os.path.exists(camera_save_dir):
            print(f"Warning: Camera save directory already exists at {camera_save_dir}")
            continue
        os.makedirs(camera_save_dir, exist_ok=True)
        try:
            process = subprocess.Popen(
                [AVLTREE_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=CURRENT_DIR
            )
            
            process.stdin.write(f"{txt_path}\n")
            process.stdin.flush()
            
            process.stdin.write(f"{camera_save_dir}\n")
            process.stdin.flush()
            
            process.stdin.write("0\n")
            process.stdin.flush()
            
            stdout, stderr = process.communicate()
            
            # print("Program output:")
            # if stdout:
            #     print(stdout)
            if stderr:
                print("Errors:", stderr)

            if process.returncode == 0:
                print(f"Successfully built AVL tree for camera {camera}")

                expected_bin = os.path.join(camera_save_dir, os.path.splitext(timecode_txt)[0] + ".bin")
                if os.path.exists(expected_bin):
                    print(f"Verified: Binary file created at {expected_bin}")
                else:
                    print(f"Warning: Binary file not found at {expected_bin}")
            else:
                print(f"Error: AVLTree program returned code {process.returncode}")
        except Exception as e:
            print(f"Failed to execute avltree for camera {camera}: {str(e)}")
    
    return avl_save_dir

def Load_txt_File(txt_path):
    with open(txt_path, 'r') as f:
        frameinfo = [line.strip() for line in f.readlines()]
    return frameinfo

def extract_frame_info(output_str):
    # Search "line in txt file: "
    start_marker = "line in txt file: "
    start_pos = output_str.find(start_marker)
    if start_pos == -1:
        return None
    
    # Start from the marker position, find the end of this line
    start_pos += len(start_marker)
    end_pos = output_str.find('\n', start_pos)
    if end_pos == -1:
        frame_info = output_str[start_pos:]
    else:
        frame_info = output_str[start_pos:end_pos]
    
    return frame_info.strip()


def Search_AVLtree(avl_save_dir, camera, timecode, threshold):
    avl_tree_name = os.listdir(os.path.join(avl_save_dir, camera))[0]
    assert avl_tree_name.endswith('.bin')
    avl_tree_path = os.path.join(avl_save_dir, camera, avl_tree_name)
    if not os.path.exists(avl_tree_path):
        print(f"Error: AVL tree not found at {avl_tree_path}")
        return -1
    # search the avl tree
    if not os.path.exists(AVLTREE_PATH):
        print(f"Error: AVLTree executable not found at {AVLTREE_PATH}")
        return -1
    try:
        process = subprocess.Popen(
            [AVLTREE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=CURRENT_DIR
        )
        
        process.stdin.write(f"{avl_tree_path}\n")
        process.stdin.flush()
        
        process.stdin.write(f"{timecode}\n")
        process.stdin.flush()
        
        process.stdin.write(f"{threshold}\n")
        process.stdin.flush()
        
        stdout, stderr = process.communicate()
        
        if stderr:
            print("Errors:", stderr)
        
        if process.returncode == 0:
            # print(f"Successfully searched nearest timecode")

            frame_info = extract_frame_info(stdout)
            if frame_info:
                return frame_info
            else:
                print("No nearest timecode found")
                return 0
        else:
            print(f"Error: AVLTree program returned code {process.returncode}")
    except Exception as e:
        print(f"Failed to search nearest timecode: {str(e)}")
    
    return -1

def process_camera(args):
    avl_save_dir, camera, timecode, threshold, reference_camera = args
    if camera == reference_camera:
        return None
    
    result = Search_AVLtree(avl_save_dir, camera, timecode, threshold)
    if result == 0:
        print(f"Failed to search nearest timecode for camera {camera} at timecode {timecode}")
        return None
    elif result == -1:
        print(f"Error in camera {camera}!")
        return None
    
    return (camera, result)

def Search_Synced_Frames(REFERENCE_CAMERA, avl_save_dir, THRESHOLD):
    REFERENCE_TXT = sorted([f for f in os.listdir(os.path.join(DATA_DIR, DATE, REFERENCE_CAMERA)) if f.endswith('.txt')])[SEQ_IDX]
    REFERENCE_TXT_PATH = os.path.join(DATA_DIR, DATE, REFERENCE_CAMERA, REFERENCE_TXT)

    frameinfo = Load_txt_File(REFERENCE_TXT_PATH)
    
    timecode_frameidx = {
        "timecode": [],
        "frameidx": []
    }

    for info in frameinfo:
        timecode, frameidx = info.split("_")[1:]
        timecode_frameidx["timecode"].append(timecode)
        timecode_frameidx["frameidx"].append(frameidx)

    syncd_info = {}
    
    # parallel processing
    num_processes = min(len(CAMERA_LIST), multiprocessing.cpu_count())
    pool = multiprocessing.Pool(processes=num_processes)
    
    print(f"Using {num_processes} processes for parallel processing")

    for timecode in timecode_frameidx["timecode"]:
        syncd_info[timecode] = {}
        
        camera_args = [(avl_save_dir, camera, timecode, THRESHOLD, REFERENCE_CAMERA) 
                      for camera in CAMERA_LIST if camera != REFERENCE_CAMERA]
        
        results = pool.map(process_camera, camera_args)
        
        for result in results:
            if result is not None:
                camera, frame_info = result
                syncd_info[timecode][camera] = frame_info

    pool.close()
    pool.join()

    return syncd_info

def Save_Synced_Frames(syncd_info):

    # # torchcodec can only decode video in format yuv420p. However, BRICS videos are stored in yuvj422p.
    # # So we first try cpu version.
    # decoder = VideoDecoder(
    #     video_path,
    #     device='cpu',
    # )
    # frame = decoder[0]
    # print(f"Frame shape: {frame.shape}")

    SAVE_DIR = os.path.join(LOCAL_SAVE_BASE_DIR, f'{DATE}_synced_frames', f"SEQ_IDX_{SEQ_IDX:04d}")
    os.makedirs(SAVE_DIR, exist_ok=True)
    for timecode, syncd_frames in syncd_info.items():
        save_dir = os.path.join(SAVE_DIR, timecode)
        os.makedirs(save_dir, exist_ok=True)
        for camera, frame_info in syncd_frames.items():
            frame_path = os.path.join(save_dir, f"{camera}_{frame_info}.png")
            if os.path.exists(frame_path):
                print(f"Frame already exists at {frame_path}")
                continue
            
            frame_num = int(frame_info.split("_")[-1])
            VIDEO_NAME = sorted([f for f in os.listdir(os.path.join(DATA_DIR, DATE, camera)) if f.endswith('.mp4')])[SEQ_IDX]
            video_path = os.path.join(DATA_DIR, DATE, camera, VIDEO_NAME)
            video_decoder = VideoDecoder(video_path, device='cpu')
            frame = video_decoder[frame_num]
            print(f"Frame shape: {frame.shape}")

            frame_np = frame.numpy() # (3, H, W)
            frame_np = frame_np.transpose(1, 2, 0) # (H, W, 3)
            Image.fromarray(frame_np).save(frame_path)


if __name__ == "__main__":
    avl_save_dir = Build_AVLtree()
    print(f"AVL trees save directory: {avl_save_dir}!")

    REFERENCE_CAMERA = "bric-rev1-001_cam0"
    THRESHOLD = 50000
    syncd_info = Search_Synced_Frames(REFERENCE_CAMERA, avl_save_dir, THRESHOLD)
    print("Done for searching synced frames!")

    Save_Synced_Frames(syncd_info)
    print("Done for saving synced frames!")