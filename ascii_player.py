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
        'ffprobe', '-v', 'error',
        '-show_entries', 'stream=width,height:format=duration',
        '-of', 'json', video_path
    ]
    try:
        # await, pipe the output and error, convert the raw data into python string
        # take the json and turn into dictionary(object in js)

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)
        width = info['streams'][0]['width']
        height = info['streams'][0]['height']
        duration = float(info.get('format', {}).get('duration', 0))
        return width / height, duration
    except Exception:
        return 16 / 9, 0
# extract url and aspect ratio using ytdlp
def get_ytvideo(url):
    import yt_dlp

    ydl_opts = {
        # download best, but also the one that has both audio and vdieo precombined not seprate
        'format': 'b', 'quiet': True, 'noplaylist': True,
        # try mimicking an android
        'js_runtimes': {
            'node': {}
        },
        # get the cookeues
        'cookiesfrombrowser': ('firefox', ),
        # fetch a community written script to bypass the youtube anti scarpper system
        'remote_components': ['ejs:github']
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        width = info.get('width', 16)
        height = info.get('height', 9)
        aspect = width / height

        return info['url'], aspect

def ascii_video(target_path, fps=24, pixel_mode=False):
    if target_path.startswith('http://') or target_path.startswith('https://'):
        sys.stdout.write("Extracting direct stream URL... please wait.\n")
        sys.stdout.flush()
        play_url, aspect_ratio = get_ytvideo(target_path)
    else:
        play_url = target_path
        aspect_ratio = get_aspect_ratio(target_path)


    # take the width and height of the terminal
    # leave a row empty at the bottom to remove the jumping
    term_cols, term_lines = shutil.get_terminal_size()
    max_height = (term_lines - 1) * 2 if pixel_mode else term_lines - 1
    max_width = term_cols


    font_ratio = 1.0 if pixel_mode else 2.2

    calc_width = max_width
    calc_height = int((calc_width / aspect_ratio) / font_ratio)

    if calc_height > max_height:
        calc_height = max_height
        calc_width = int(calc_height * font_ratio * aspect_ratio)

    if calc_height % 2 != 0:
        calc_height -= 1

    width = calc_width
    height = calc_height

    ascii_chars = " .:-=+*#%@"
    ascii_chars_array = np.array(list(ascii_chars))
    char_count = len(ascii_chars) - 1



    # separate vidoe but dont display
    # when the audio trach ends exit
    # silence all output
    audio_command = [
        'ffplay',
        '-nodisp',
        '-autoexit',
        '-loglevel', 'quiet',
        play_url
    ]

    # ask dat thing
    command = [
        'ffmpeg',
        '-i', play_url,
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

    start_time = None
    frame_index = 0

    try:
        while True:
            raw_frame = video_process.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break
            if start_time is None:
                start_time = time.time()
            # frame tally
            frame_index += 1
            # current frame * 1/fps and compare it to time now
            expected_time = start_time + (frame_index * frame_duration)
            if time.time() > expected_time:
                continue

            # every byte as binary
            frame = np.frombuffer(raw_frame, dtype=np.uint8)
            # skip over 3
            # scrunch the colors
            r = frame[0::3] & 0xF0
            g = frame[1::3] & 0xF0
            b = frame[2::3] & 0xF0
            # pick the chars
            if not pixel_mode:
                luminance = 0.299 * r + 0.587 * g + 0.114 * b
                char_idx = np.round((luminance / 255.0) * char_count).astype(np.uint8)
                chars = ascii_chars_array[char_idx]
            #colors
            lines = []

            if pixel_mode:
                for row in range(0, height, 2):
                    # two rows at a time
                    top_start = row * width
                    bot_start = (row + 1) * width

                    line_parts = []
                    # previous pixel
                    ltr, ltg, ltb = -1, -1, -1
                    lbr, lbg, lbb = -1, -1, -1

                    for x in range(width):
                        t_idx = top_start + x
                        b_idx = bot_start + x

                        tr, tg, tb = r[t_idx], g[t_idx], b[t_idx]
                        br, bg, bb = r[b_idx], g[b_idx], b[b_idx]

                        if tr != ltr or tg != ltg or tb != ltb or br != lbr or bg != lbg or bb != lbb:
                            ltr, ltg, ltb = tr, tg, tb
                            lbr, lbg, lbb = br, bg, bb

                            line_parts.append(f"\033[38;2;{tr};{tg};{tb}m\033[48;2;{br};{bg};{bb}m▀")
                        else:
                            line_parts.append("▀")

                    lines.append("".join(line_parts))
            else:
                for row in range(height):
                    start_idx = row * width
                    end_idx = start_idx + width

                    line_parts = []
                    lr, lg, lb = -1, -1, -1

                    for i in range(start_idx, end_idx):
                        cr, cg, cb = r[i], g[i], b[i]
                        if cr != lr or cg != lg or cb != lb:
                            lr, lg, lb = cr, cg, cb
                            line_parts.append(f"\033[38;2;{cr};{cg};{cb}m{chars[i]}")
                        else:
                            line_parts.append(chars[i])
                    lines.append("".join(line_parts))

            output = "\033[H" + "\033[0m\n".join(lines) + "\033[0m\n"
            sys.stdout.write(output)
            sys.stdout.flush()

            
            sleep_time = expected_time - time.time()
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
