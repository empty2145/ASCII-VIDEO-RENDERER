import subprocess
import time
import sys

def ascii_video(video_path, width=80, fps=24):
    height = int(width / 2)

    ascii_chars = " .:-=+*#%@"

    # ask dat thing
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-r', str(fps),
        '-s', f'{width}x{height}',
        '-f', 'image2pipe',
        '-loglevel', 'quiet',
        '-'
    ]
    

if __name__ == "__main__":
    ascii_video("input.mp4", width=100, fps=24)