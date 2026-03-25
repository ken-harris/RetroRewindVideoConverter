# Retro Rewind Video Converter

A desktop tool for converting videos to the format required by Retro Rewind, and deploying them directly to your Retro Rewind install.

## Requirements

### FFmpeg (required)

FFmpeg must be installed on your machine and available on your system PATH.

Download: https://ffmpeg.org/download.html

After installing, verify it is working by opening a terminal and running:

```
ffmpeg -version
```

### Python

Python 3.x is required to run the script directly.

## Usage

### Settings

- **Retro Rewind Install Location** — the root folder of your Retro Rewind installation. This is used when deploying a movie.
- **Converted Movies Location** — the folder where converted `.mp4` files are stored. This is the source for the movie list and the output destination for conversions.

Settings are saved automatically to `settings.json` in the same folder as the script and restored on next launch.

### Convert

1. Click **Browse** next to **Input File** and select a video file (`.mp4`, `.mov`, `.avi`, `.mkv`).
2. The **Output File** path is set automatically based on your Converted Movies Location and the input filename (e.g. `Office Space_512x512.mp4`).
3. Click **Convert Video**.

The output video will be scaled and padded to exactly 512x512, encoded as H.264 with AAC audio.

### Set Movie

Once you have converted movies in your Converted Movies Location, they will appear in the **Set Movie** list.

1. Select a movie from the list.
2. Click **Set Video**.

The selected file will be copied to:

```
<Retro Rewind Install Location>\RetroRewind\Content\Movies\VHS\Public\RR_Channel_Public.mp4
```

Any existing file at that path will be replaced.

## Output Format

| Setting   | Value              |
|-----------|--------------------|
| Resolution | 512x512 (padded with black bars to preserve aspect ratio) |
| Video codec | H.264 (`libx264`) |
| Audio codec | AAC                |
| Audio bitrate | 192k             |