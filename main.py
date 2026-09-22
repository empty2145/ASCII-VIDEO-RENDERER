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
    ascii_video("input.mp4", width=100, fps=24)