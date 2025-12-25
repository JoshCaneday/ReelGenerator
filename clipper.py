import re
import subprocess
from pathlib import Path

class Clipper:
    def __init__(self):
        self.VIDEOS_DIR = Path("videos")
        self.FRAME_INTERVAL_SECONDS = 1.0
        self.IMG_RE = re.compile(r"\[(?P<vid>.*?)\]_(?P<idx>\d+)", re.I)

    def extract_clip(self, outDir, clipDuration, imagePath: str) -> str:
        out_dir = Path(outDir)
        out_dir.mkdir(parents=True, exist_ok=True)
        m = self.IMG_RE.search(imagePath)
        if not m:
            raise ValueError(f"Bad image name: {imagePath}")

        videoID = m.group("vid")
        idx = int(m.group("idx"))

        timestamp = idx * self.FRAME_INTERVAL_SECONDS

        video = self.find_video(videoID)
        videoDuration = self.get_duration(video)
        start, end = self.clamp_window(timestamp, videoDuration, clipDuration)

        out_path = outDir + ".mp4"

        print("Image:", imagePath)
        print("Video :", video.name)
        print(f"idx={idx} -> t={timestamp:.3f}s")
        print(f"Extract [{start:.3f}, {end:.3f}] -> {out_path}")

        subprocess.run([
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-ss", f"{start:.3f}",
            "-i", str(video),
            "-t", f"{(end-start):.3f}",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_path),
        ], check=True)

        print("Done.")
        return out_path

    def get_duration(self, video: Path) -> float:
        # ffprobe output is just: 442.851234
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video),
        ])
        return float(out.decode().strip())


    def find_video(self, video_id: str) -> Path:
        needle = f"[{video_id}]"
        for ext in ("*.mp4", "*.webm", "*.mkv", "*.mov"):
            for p in self.VIDEOS_DIR.glob(ext):
                if needle in p.name:
                    return p
        raise FileNotFoundError(f"No video in {self.VIDEOS_DIR} containing {needle}")


    def clamp_window(self, center: float, total: float, length: float) -> tuple[float, float]:
        # want [center - length/2, center + length/2], but shift if it spills past ends
        half = length / 2
        start = center - half
        end = center + half

        if start < 0:
            start = 0
            end = length
        if end > total:
            end = total
            start = total - length

        # if video shorter than length, just return whole thing
        if start < 0:
            start = 0

        return start, end
