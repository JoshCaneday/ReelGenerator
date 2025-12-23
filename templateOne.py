from clip import Clipper
from llm import LLM
from model import TextToImage
from tts import TTS

import subprocess
from pathlib import Path

generateScriptPrompt = """
Generate an original Instagram/TikTok reel voiceover script.

Style:
- Hard-hitting and emotional
- Second-person “you”
- Short lines that hit like beats
- Ends with a closing mic-drop line that hits hard

Topic:
Up to you, the LLM.

Must include:
- A hook in the first 1–2 lines that stops scrolling
- A closing 2-line mic-drop

Constraints:
- 150–190 words
- 8–12 paragraphs (mostly 1 sentence each)
- No hashtags, no emojis, no stage directions

Output ONLY the script. No title. No explanation. No formatting other than line breaks.
"""

def create_project(outputFolderName, automatic=True, script="", music=""):
    llm = LLM()
    tts = TTS()
    clip = TextToImage()
    clipper = Clipper()
    if automatic:
        # LLM
        text = llm.get_response(generateScriptPrompt)
        sentences = text.strip().split(".")
        sentenceNum = 0
        videoPaths = []
        for sentence in sentences:
            sentenceNum += 1

            # TTS
            ttsPath, ttsDuration = tts.generate(sentence,"voice1","/ttsSentence" + str(sentenceNum), outputFolderName)
            # CLIP (two types of "clip" used here, one as in a video clip, the other as in the OpenAI CLIP model)
            imagePath = clip.assign(sentence)
            clipPath = clipper.extract_clip(outputFolderName + "/clip" + str(sentenceNum), ttsDuration, imagePath)
            videoPaths.append(mux_audio_video(clipPath,ttsPath,f"{outputFolderName}/video{sentenceNum:04d}.mp4"))
        finalPath = concat_videos(videoPaths, f"{outputFolderName}/final.mp4")
        print(finalPath)

def mux_audio_video(clip_path: str, audio_path: str, out_path: str) -> str:
    # -shortest: stop when the shortest stream ends (usually audio if video is longer)
    # Re-encode to widely compatible codecs (H.264 + AAC).
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-y",
        "-i", clip_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path

def concat_videos(video_paths: list[str], out_path: str) -> str:
    out_path = str(out_path)

    # Create concat list file
    list_path = Path(out_path).with_suffix(".concat.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for p in video_paths:
            # concat demuxer requires: file 'path'
            f.write(f"file '{Path(p).as_posix()}'\n")

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path    
        
