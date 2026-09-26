import numpy as np
import argparse
import subprocess
import time
import sys
import shutil
import json

def get_aspect_ratio(video_path):
    # print only critical errors
    # tell ffprobe to noly look at the video stream and niot the audio and subtitles stream
    # fetch only width and height 
    # output format json
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        video_path
    ]
    try:
        # await, pipe the output and error, convert the raw data into python string
        # take the json and turn into dictionary(object in js)

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)
        width = info['streams'][0]['width']
        height = info['streams'][0]['height']
        return width / height
    except Exception as e:
        return 16 / 9

def ascii_video(video_path, fps=24, pixel_mode=False):
    aspect_ratio = get_aspect_ratio(video_path)

    # take the width and height of the terminal
    # leave a row empty at the bottom to remove the jumping
    term_cols, term_lines = shutil.get_terminal_size()
    max_height = term_lines - 1
    max_width = term_cols


    font_ratio = 2

    calc_width = max_width
    calc_height = int((calc_width / aspect_ratio) / font_ratio)

    if calc_height > max_height:
        calc_height = max_height
        calc_width = int(calc_height * font_ratio * aspect_ratio)

    width = calc_width
    height = calc_height

    ascii_chars = " .:-=+*#%@"
    ascii_chars_array = np.array(list(ascii_chars))
    char_count = len(ascii_chars) - 1

    start_time = time.time()
    frame_index = 0


    # separate vidoe but dont display
    # when the audio trach ends exit
    # silence all output
    audio_command = [
        'ffplay',
        '-nodisp',
        '-autoexit',
        '-loglevel', 'quiet',
        video_path
    ]

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

    audio_process = subprocess.Popen(audio_command)
    video_process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

    frame_size = width * height * 3
    frame_duration = 1.0 / fps

    sys.stdout.write('\033[2J')

    try:
        while True:
            raw_frame = video_process.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break

            frame_index += 1
            expected_time = start_time + (frame_index * frame_duration)
            if time.time() > expected_time:
                continue


            frame = np.frombuffer(raw_frame, dtype=np.uint8)
            
            r = frame[0::3]
            g = frame[1::3]
            b = frame[2::3]

            if not pixel_mode:
                luminance = 0.299 * r + 0.587 * g + 0.114 * b
                char_idx = np.round((luminance / 255.0) * char_count).astype(np.uint8)
                chars = ascii_chars_array[char_idx]

            lines = []
            for row in range(height):
                start_idx = row * width
                end_idx = start_idx + width

                if pixel_mode:
                    line = "".join(
                        f"\033[48;2;{r[i]};{g[i]};{b[i]}m "
                        for i in range(start_idx, end_idx)
                    )
                else:
                    line = "".join(
                        f"\033[38;2;{r[i]};{g[i]};{b[i]}m{chars[i]}"
                        for i in range(start_idx, end_idx)
                    )
                lines.append(line)

            output = "\033[H" + "\033[0m\n".join(lines) + "\033[0m\n"
            sys.stdout.write(output)
            sys.stdout.flush()

            elapsed = time.time() - start_time
            sleep_time = frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\n')
        video_process.terminate()
        audio_process.terminate()


# if __name__ == "__main__":
#    ascii_video("badapple.mp4", fps=24)


# ensure that the code is executed directly from the terminal
# create the parser object. if user run the script with -h or -help desc will show up
# positional argument if no then error
# optional
# boolean toggle switch
# trigger the parser tow ork
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play video in the terminal using ASCII/ANSI art.")
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second (default: 24)")
    parser.add_argument("--pixel", action="store_true", help="Use solid pixel blocks instead of ASCII characters")

    args = parser.parse_args()

    # hide terminal cursor
    sys.stdout.write('\033[?25l')
    try:
        ascii_video(args.video, fps=args.fps, pixel_mode=args.pixel)
    finally:
        # return the cursor back
        sys.stdout.write('\033[?25h')
