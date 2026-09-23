import subprocess
import time
import sys
import shutil
import json

def aspect_ratio(video_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        video_path
    ]

def ascii_video(video_path, fps=24):
    term_cols, term_lines = shutil.get_terminal_size()

    max_height = term_lines - 1
    max_width = term_cols

    aspect_ratio = 16 / 9

    calc_width = max_width
    calc_height = int((calc_width / aspect_ratio) / 2)

    if calc_height > max_height:
        calc_height = max_height
        calc_width = int(calc_height * 2 * aspect_ratio)

    width = calc_width
    height = calc_height

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

    process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

    frame_size = width * height * 3
    frame_duration = 1.0 / fps

    sys.stdout.write('\033[2J')

    try:
        while True:
            start_time = time.time()

            raw_frame = process.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break

            output_buffer = ['\033[H']

            for y in range(height):
                for x in range(width):
                    idx = (y * width + x) * 3
                    r, g, b = raw_frame[idx], raw_frame[idx+1], raw_frame[idx+2]

                    luminance = int(0.299*r + 0.587*g + 0.114*b)
                    char_idx = int((luminance / 255.0) * (len(ascii_chars) - 1))
                    char = ascii_chars[char_idx]

                    output_buffer.append(f'\033[38;2;{r};{g};{b}m{char}')

                output_buffer.append('\n')

            sys.stdout.write(''.join(output_buffer))
            sys.stdout.flush()

            elapsed = time.time() - start_time
            sleep_time = frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\n')
        process.terminate()


if __name__ == "__main__":
    ascii_video("badapple.mp4", fps=24)