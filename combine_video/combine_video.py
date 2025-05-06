import os
import subprocess
import time
import concurrent.futures

local_save_dir = "/users/xcong2/data/users/xcong2/projects/BRICS_DataLoader/local_save_dir"
cam_list = os.listdir(local_save_dir)
MAX_WORKERS = os.cpu_count() or 4 # 如果 os.cpu_count() 返回 None，则默认为 4

# --- 处理单个摄像头的函数 ---
def process_camera(cam_dir):
    txt_files = [f for f in os.listdir(cam_dir) if f.endswith('.txt')]
    if not txt_files:
        return f"Error: No .txt files found in {cam_dir}."
    if len(txt_files) > 1:
        print(f"Warning: Found multiple .txt files in {cam_dir}, using the first one: {txt_files[0]}")

    txt_filename = txt_files[0]
    txt_file_path = os.path.join(cam_dir, txt_filename)
    output_filename = os.path.join(cam_dir, txt_filename.replace(".txt", ".mp4"))

    if os.path.exists(output_filename):
        return f"File already exists, skipping: {output_filename}"

    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',       # Allow using relative paths or paths with special characters
        '-i', txt_file_path,# Input text file containing the list of files to concatenate
        '-c:v', 'copy',     # Copy video stream without re-encoding (fast)
        '-an',              # Do not include audio stream
        '-y',               # Overwrite output file if it exists, without asking
        output_filename     # Output MP4 file name
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8')

    if result.returncode != 0:
        error_message = (
            f"Error processing camera {os.path.basename(cam_dir)}.\n"
            f"Command: {' '.join(command)}\n"
            f"Return code: {result.returncode}\n"
            f"FFmpeg standard error (stderr):\n{result.stderr}\n"
            f"FFmpeg standard output (stdout):\n{result.stdout}"
        )
        return error_message
    else:
        return f"Successfully created: {output_filename}"


if __name__ == "__main__":
    start_time = time.time()
    print(f"Start processing, using at most {MAX_WORKERS} threads...")

    try:
        cam_folders = [d for d in os.listdir(local_save_dir) if os.path.isdir(os.path.join(local_save_dir, d))]
        if not cam_folders:
            print(f"Error: No subdirectories found in {local_save_dir}.")
            exit()

        cam_dirs_to_process = [os.path.join(local_save_dir, cam) for cam in cam_folders]

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results_iterator = executor.map(process_camera, cam_dirs_to_process)
            for result in results_iterator:
                print(result)


    end_time = time.time()
    print(f"\nDone! Total time: {end_time - start_time:.2f} seconds")