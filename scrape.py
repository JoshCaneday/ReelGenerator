import shutil
import subprocess
import sys

# Terminal Command Equivalent:
# yt-dlp --js-runtimes node -S "ext:mp4:m4a,vcodec:h264,acodec:aac" -P "./videos"  --merge-output-format mp4 "https://www.youtube.com/watch?v=4x7mxKG-9KI"

JS_RUNTIME = "node"
OUTPUT_DIR = "./videos"
URLS = [
    "https://www.youtube.com/watch?v=kJGmZ8XpAXo",
    "https://www.youtube.com/watch?v=4c5mfRsX-VI",
    "https://www.youtube.com/watch?v=73L0PRImRmA",
    "https://www.youtube.com/watch?v=1Hs0Z_JWWfk",
    "https://www.youtube.com/watch?v=7Kdk97wvd94",
    "https://www.youtube.com/watch?v=sWi9Dx38PAM",
    "https://www.youtube.com/watch?v=4x7mxKG-9KI",
    "https://www.youtube.com/watch?v=LQ6WZ6F3ziI",
    "https://www.youtube.com/watch?v=h2x7R3Icv08",
    "https://www.youtube.com/watch?v=hnDdbzoX6tA"
]
yt_dlp = shutil.which("yt-dlp")
if yt_dlp is None:
    print("ERROR: yt-dlp not found on PATH.", file=sys.stderr)
    sys.exit(1)

for url in URLS:
    cmd = [
        yt_dlp,
        "--js-runtimes", JS_RUNTIME,
        "-S", "ext:mp4:m4a,vcodec:h264,acodec:aac",
        "-P", OUTPUT_DIR,
        "--merge-output-format", "mp4",
        url,
    ]
    print("Running:\n  " + " ".join(cmd))
    rc = subprocess.call(cmd)
sys.exit(rc)
