import os
from pathlib import Path

import cv2


def video_to_snapshots(video_path: str, interval_seconds: int = 3, output_dir: str = "data/snapshots"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    interval_frames = int(fps * interval_seconds)
    count = 0
    image_files = []
    video_stem = Path(video_path).stem
    success, image = vidcap.read()
    while success:
        if int(vidcap.get(cv2.CAP_PROP_POS_FRAMES)) % interval_frames == 0:
            filename = os.path.join(output_dir, f"{video_stem}_{count}.jpg")
            cv2.imwrite(filename, image)
            image_files.append(filename)
            count += 1
        success, image = vidcap.read()
    vidcap.release()
    os.remove(video_path)
    return image_files
