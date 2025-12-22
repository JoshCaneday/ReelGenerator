from pathlib import Path
import subprocess

VIDEO_DIR = Path("videos")
IMAGE_DIR = Path("images")
INTERVAL_SECONDS = 3  # every 3 seconds

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

for video in VIDEO_DIR.glob("*.mp4"):
    out_dir = IMAGE_DIR / video.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    # images/images_vidname/vidname_000001.jpg, etc.
    out_pattern = str(out_dir / f"{video.stem}_%06d.jpg")

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            f"fps=1/{INTERVAL_SECONDS}",
            "-q:v",
            "2",
            "-vsync",
            "vfr",
            out_pattern,
        ],
        check=True,
    )

print("Done.")

