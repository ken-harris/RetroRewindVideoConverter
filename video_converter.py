from tkinter import ttk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import re
import json
import shutil
import sys

if getattr(sys, 'frozen', False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(_base_dir, "settings.json")


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            install_var.set(data.get("install_location", ""))
            movie_var.set(data.get("movie_location", ""))
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "install_location": install_var.get(),
            "movie_location": movie_var.get()
            }, f)


def check_ready(*_):
    movie = movie_var.get().strip()
    input_path = input_var.get().strip()
    if movie and input_path:
        stem, _ = os.path.splitext(os.path.basename(input_path))
        output_var.set(os.path.join(movie, stem + "_512x512.mp4"))
        convert_btn.config(state=tk.NORMAL)
    else:
        convert_btn.config(state=tk.DISABLED)


def select_input_file():
    path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("MP4 files", "*.mp4"),
                   ("All video files", "*.mp4 *.mov *.avi *.mkv")],
                   initialdir=movie_var.get()
    )
    if path:
        input_var.set(path)


def select_install_location():
    path = filedialog.askdirectory(
        title="Retro Rewind Install Location...",
        initialdir=install_var.get()
    )
    if path:
        install_var.set(path)
        save_settings()


def select_movie_location():
    path = filedialog.askdirectory(
        title="Converted Movie Location...",
        initialdir=movie_var.get()
    )
    if path:
        movie_var.set(path)
        save_settings()

def get_video_duration(input_path):
    """Use ffprobe to get the duration of the video in seconds."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path
            ],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def convert_video():
    input_path = input_var.get().strip()
    output_path = output_var.get().strip()

    if not input_path:
        messagebox.showwarning(
            "Missing Input", "Please select an input video file.")
        return
    if not output_path:
        messagebox.showwarning(
            "Missing Output", "Please specify an output file path.")
        return
    if not os.path.isfile(input_path):
        messagebox.showerror(
            "File Not Found", f"Input file does not exist:\n{input_path}")
        return

    convert_btn.config(state=tk.DISABLED)
    status_var.set("Starting conversion...")
    progress_bar["value"] = 0

    def run():
        duration = get_video_duration(input_path)

        # FFmpeg filter:
        #   Scale down to fit within 512x512 (preserving aspect ratio),
        #   then pad to exactly 512x512 with black bars.
        vf_filter = (
            "scale=512:512:force_original_aspect_ratio=decrease,"
            "pad=512:512:(ow-iw)/2:(oh-ih)/2:color=black"
        )

        cmd = [
            "ffmpeg",
            "-y",                        # Overwrite output without asking
            "-i", input_path,
            "-vf", vf_filter,
            "-c:v", "libx264",           # H.264 video codec
            "-preset", "medium",         # Encoding speed/quality balance
            # Quality level (lower = better, 18-28 is typical)
            "-crf", "30",
            "-c:a", "aac",               # AAC audio codec
            "-b:a", "192k",              # Audio bitrate
            "-movflags", "+faststart",   # Optimize for streaming/playback
            output_path
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Parse FFmpeg's stderr for progress updates
            time_pattern = re.compile(r"time=(\d+):(\d+):([\d.]+)")

            for line in process.stderr:
                match = time_pattern.search(line)
                if match and duration:
                    h, m, s = int(match.group(1)), int(
                        match.group(2)), float(match.group(3))
                    elapsed = h * 3600 + m * 60 + s
                    pct = min(int((elapsed / duration) * 100), 99)
                    root.after(0, lambda p=pct: update_progress(p))

            process.wait()

            if process.returncode == 0:
                root.after(0, on_success)
            else:
                root.after(0, lambda: on_error(
                    "FFmpeg exited with an error. Make sure FFmpeg is installed and on your PATH."))

        except FileNotFoundError:
            root.after(0, lambda: on_error(
                "FFmpeg was not found.\n\n"
                "Please install FFmpeg and make sure it is added to your system PATH.\n"
                "Download it at: https://ffmpeg.org/download.html"
            ))
        except Exception as e:
            root.after(0, lambda err=e: on_error(str(err)))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def update_progress(pct):
    progress_bar["value"] = pct
    status_var.set(f"Converting... {pct}%")


def on_success():
    progress_bar["value"] = 100
    status_var.set("Done! Conversion complete.")
    check_ready()
    refresh_movie_list()
    messagebox.showinfo(
        "Success", f"Video converted successfully!\n\nSaved to:\n{output_var.get()}")


def on_error(msg):
    status_var.set("Error during conversion.")
    progress_bar["value"] = 0
    check_ready()
    messagebox.showerror("Conversion Failed", msg)


def refresh_movie_list(*_):
    movie_listbox.delete(0, tk.END)
    directory = movie_var.get().strip()
    if not directory or not os.path.isdir(directory):
        return
    files = sorted(
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(".mp4")
    )
    for f in files:
        movie_listbox.insert(tk.END, f)

def copy_selected_movie():
    selection = movie_listbox.curselection()
    if not selection:
        messagebox.showwarning("No Selection", "Please select a movie from the list.")
        return

    install_dir = install_var.get().strip()
    if not install_dir:
        messagebox.showwarning("No Install Location", "Please set the Retro Rewind install location.")
        return

    selected_filename = movie_listbox.get(selection[0])
    source_path = os.path.join(movie_var.get().strip(), selected_filename)

    dest_dir = os.path.join(install_dir, "RetroRewind", "Content", "Movies", "VHS", "Public")
    dest_path = os.path.join(dest_dir, "RR_Channel_Public.mp4")

    if not os.path.isfile(source_path):
        messagebox.showerror("File Not Found", f"Source file does not exist:\n{source_path}")
        return

    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy2(source_path, dest_path)
    messagebox.showinfo("Done", f"'{selected_filename}' copied as:\n{dest_path}")

# --- UI Setup ---
root = tk.Tk()
root.title("Retro Rewind Video Converter")
root.resizable(False, False)

pad = {"padx": 10, "pady": 5}

row = 0

# Title
tk.Label(root, text="Retro Rewind Video Converter", font=("Segoe UI", 14, "bold")).grid(
    row=row, column=0, columnspan=3, pady=(15, 5)
)
row += 1
tk.Label(root, text="Converts video to 512×512 · H.264 · AAC", font=("Segoe UI", 9), fg="gray").grid(
    row=row, column=0, columnspan=3, pady=(0, 10)
)
row += 1
tk.Label(root, text="Settings:", font=("Segoe UI", 12)).grid(
    row=row, column=0, columnspan=3, pady=(15, 5)
)

row += 1
tk.Label(root, text="Retro Rewind Install Location:").grid(
    row=row, column=0, sticky="e", **pad)
install_var = tk.StringVar()
tk.Entry(root, textvariable=install_var, width=50).grid(row=row, column=1, **pad)
tk.Button(root, text="Browse...", command=select_install_location).grid(
    row=row, column=2, **pad)

row += 1

tk.Label(root, text="Converted Movies Location:").grid(
    row=row, column=0, sticky="e", **pad)
movie_var = tk.StringVar()
tk.Entry(root, textvariable=movie_var, width=50).grid(row=row, column=1, **pad)
tk.Button(root, text="Browse...", command=select_movie_location).grid(
    row=row, column=2, **pad)


load_settings()
row += 1
separator = ttk.Separator(root, orient='horizontal')
separator.grid(row=row, column=0, columnspan=3, sticky='ew', pady=5)

row += 1

tk.Label(root, text="Convert:", font=("Segoe UI", 12)).grid(
    row=row, column=0, columnspan=3, pady=(15, 5)
)

row += 1
# Input
tk.Label(root, text="Input File:").grid(row=row, column=0, sticky="e", **pad)
input_var = tk.StringVar()
tk.Entry(root, textvariable=input_var, width=50).grid(row=row, column=1, **pad)
tk.Button(root, text="Browse…", command=select_input_file).grid(
    row=row, column=2, **pad)

row += 1
# Output
tk.Label(root, text="Output File:").grid(row=row, column=0, sticky="e", **pad)
output_var = tk.StringVar()
tk.Entry(root, textvariable=output_var, width=50).grid(row=row, column=1, **pad)

row += 1
# Convert button
convert_btn = tk.Button(
    root, text="Convert Video", command=convert_video,
    font=("Segoe UI", 10, "bold"), bg="#2d7dd2", fg="white",
    relief="flat", padx=12, pady=6, state=tk.DISABLED
)
convert_btn.grid(row=row, column=0, columnspan=3, pady=12)

input_var.trace_add("write", check_ready)
movie_var.trace_add("write", check_ready)
movie_var.trace_add("write", refresh_movie_list)
check_ready()

row += 1
separator = ttk.Separator(root, orient='horizontal')
separator.grid(row=row, column=0, columnspan=3, sticky='ew', pady=5)

row += 1
tk.Label(root, text="Set Movie:", font=("Segoe UI", 12)).grid(
    row=row, column=0, columnspan=3, pady=(15, 5)
)

row += 1
movie_listbox = tk.Listbox(root, width=60, height=10)
movie_listbox.grid(row=row, column=0, columnspan=2, padx=(10, 0), pady=5, sticky="ew")
scrollbar = ttk.Scrollbar(root, orient="vertical", command=movie_listbox.yview)
scrollbar.grid(row=row, column=2, padx=(0, 10), pady=5, sticky="ns")
movie_listbox.config(yscrollcommand=scrollbar.set)

refresh_movie_list()

row += 1
# Set Video button
set_video_btn = tk.Button(
    root, text="Set Video", command=copy_selected_movie,
    font=("Segoe UI", 10, "bold"), bg="#2d7dd2", fg="white",
    relief="flat", padx=12, pady=6
)
set_video_btn.grid(row=row, column=0, columnspan=3, pady=12)

row += 1
separator = ttk.Separator(root, orient='horizontal')
separator.grid(row=row, column=0, columnspan=3, sticky='ew', **pad)

row += 1
# Progress bar (manual using Canvas for compatibility)
progress_bar = ttk.Progressbar(
    root, orient="horizontal", length=500, mode="determinate")
progress_bar.grid(row=row, column=0, columnspan=3, padx=10, pady=(10, 5))

row += 1
# Status label
status_var = tk.StringVar(value="Ready.")
tk.Label(root, textvariable=status_var, font=("Segoe UI", 9), fg="gray").grid(
    row=row, column=0, columnspan=3, pady=(0, 12)
)

root.mainloop()