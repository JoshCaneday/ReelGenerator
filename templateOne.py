from clipper import Clipper
from llm import LLM
from model import TextToImage
from tts import MYTTS

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
- 50–90 words
- 3–6 paragraphs (mostly 1 sentence each)
- No hashtags, no emojis, no stage directions

Output ONLY the script. No title. No explanation. No formatting other than line breaks.
"""

def create_project(outputFolderName, automatic=True, script="", music=""):
    outputFolderName = "./projects" + outputFolderName
    output_path = Path(outputFolderName)
    output_path.mkdir(parents=True, exist_ok=True)
    
    llm = LLM()
    tts = MYTTS()
    clip_model = TextToImage()
    clipper = Clipper()

    if automatic:
        text = ""
        if not script:
            text = llm.get_response(generateScriptPrompt)
        else:
            text = script
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 2]
        
        videoPaths = []
        for i, sentence in enumerate(sentences, 1):
            # TTS
            tts_filename = f"tts_part_{i}"
            ttsPath, ttsDuration = tts.generate(sentence, "voice1", tts_filename, str(output_path))
            
            # CLIP
            imageName = clip_model.assign(sentence)
            
            # Extract video segment
            out_clip_base = str(output_path / "clips" / f"clip_{i}")
            clipPath = clipper.extract_clip(out_clip_base, ttsDuration, imageName)
            
            # Mux (Combine audio and video)
            final_segment = str(output_path / "segments" / f"segment_{i:04d}.mp4")
            videoPaths.append(mux_audio_video(clipPath, ttsPath, final_segment))
            
        finalPath = concat_videos(videoPaths, str(output_path / "final_reel.mp4"))
        print(f"Success! Video created at: {finalPath}")
    

def mux_audio_video(clip_path: str, audio_path: str, out_path: str) -> str:
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    # We take VIDEO from input 0 and AUDIO from input 1
    # We re-encode the audio to aac to ensure it "sticks" to the video
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-y",
        "-i", clip_path,   # The visual clip (Input 0)
        "-i", audio_path,  # The TTS audio (Input 1)
        "-map", "0:v:0",   # Take ONLY video from clip
        "-map", "1:a:0",   # Take ONLY audio from TTS
        "-c:v", "copy",    # Keep video as is
        "-c:a", "aac",     # Encode audio to a compatible format
        "-shortest",       # Match the length of the shortest stream
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path

def concat_videos(video_paths: list[str], out_path: str) -> str:
    out_path = Path(out_path)
    list_path = Path(video_paths[0]).parent / "final_reel.concat.txt"
    
    with open(list_path, "w", encoding="utf-8") as f:
        for p in video_paths:
            f.write(f"file '{Path(p).name}'\n")

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path.name,
        "-c", "copy",
        f"../{out_path.name}",
    ]
    
    subprocess.run(cmd, check=True, cwd=Path(video_paths[0]).parent)
    return str(out_path)
        
create_project("/proj1")