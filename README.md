# ASCII-VIDEO-RENDERER

A high-performance, terminal-based video player that renders local video files and streams directly from YouTube into your command line. Built with Python, it uses NumPy for vectorized pixel math and advanced terminal string manipulation to achieve smooth 60fps playback with perfect audio synchronization.

## Features

* **Dual Rendering Modes**: 
  * **ASCII Mode**: Maps pixel luminance to a gradient of standard text characters.
  * **Pixel Mode**: Achieves double vertical resolution by combining ANSI foreground and background colors on a single upper-half block character (`▀`).
* **YouTube Streaming Integration**: Dynamically extracts direct streams from YouTube URLs using `yt-dlp`, complete with Node.js challenge solving to bypass anti-bot protections.
* **Master Clock Synchronization**: Absolute timeline tracking ensures video and audio never drift, automatically dropping late frames if terminal I/O lags.
* **Run-Length Encoding (RLE) Optimization**: Compresses the output string by only emitting ANSI color codes when a pixel's color changes, bypassing terminal emulator bottlenecks.
* **Dynamic Scaling**: Automatically detects terminal window size and video aspect ratio to perfectly fit and center the output.
* **Playback Controls**: Raw terminal input allows for non-blocking pause/play (Space) and quit (Q) using OS-level process signals.
* **UI**: Minimalist bottom-docked progress bar and time tracker.

## Prerequisites

This player relies on OS-level process controls (like `termios` and `SIGSTOP`), making it natively compatible with Linux and macOS. 

You must have the following system dependencies installed:
* **Python 3.x**
* **FFmpeg**: Required for decoding video (`ffmpeg`) and playing audio (`ffplay`).
* **Node.js**: Required by `yt-dlp` to solve YouTube's JavaScript security challenges.

## Installation

1. **Clone the repository and enter the directory**:
   ```bash
   git clone https://github.com/yourusername/ascii-video-renderer.git
   cd ascii-video-renderer
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   python3 -m venv venv
   
   # For standard Bash/Zsh:
   source venv/bin/activate
   
   # For Fish shell:
   source venv/bin/activate.fish
   ```

3. **Install the Python dependencies**:
   ```bash
   pip install numpy yt-dlp
   ```

## Usage

The player is executed directly from the command line. You must provide a target (either a local file path or a YouTube URL).

### Basic Commands

**Play a local video in standard ASCII mode:**
```bash
python3 ascii_player.py my_video.mp4
```

**Play a YouTube video in high-resolution Pixel mode:**
```bash
python3 ascii_player.py "https://www.youtube.com/watch?v=FtutLA63Cp8" --pixel
```

### CLI Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `video` | Positional | N/A | The path to a local video file OR a YouTube URL. |
| `--fps` | Optional | `24` | Target framerate. Useful for capping high-framerate videos to reduce CPU/Terminal load. |
| `--pixel` | Flag | `False` | Toggles the double-resolution true-color ANSI block rendering mode. |

## Controls

* **`Spacebar`**: Pause / Play
* **`Q`**: Quit the player and restore terminal settings

## Under the Hood

Rendering video in a text terminal presents massive I/O bottlenecks. This project solves them by:
1. **NumPy Vectorization**: Raw byte streams from `ffmpeg` are sliced and converted to luminance/RGB matrices in highly optimized C code, avoiding slow Python `for` loops.
2. **Color Quantization (Bitwise Masking)**: By applying a bitwise `& 0xF0` mask to the RGB values, microscopic MP4 compression noise is flattened. This allows the RLE string builder to group adjacent pixels and drastically reduce the number of ANSI escape sequences sent to `sys.stdout`.