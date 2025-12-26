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
    
    llm = LLM()
    tts = MYTTS()
    clip_model = TextToImage()
    clipper = Clipper()

    outputFolderName = "./projects" + outputFolderName
    outputPath = Path(outputFolderName)
    outputPath.mkdir(parents=True, exist_ok=True)


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
            ttsFileName = f"tts_part_{i}.wav"
            ttsPath, ttsDuration = tts.generate(sentence, "voice1.wav", ttsFileName, outputPath)
            
            # CLIP
            imageName = clip_model.assign(sentence)
            
            # Extract video segment
            clipFileName = f"clip_{i}.mp4"
            clipPath = clipper.extract_clip(ttsDuration, imageName, clipFileName, outputPath)
            
            # Mux (Combine audio and video)
            segmentFileName = f"segment_{i:04d}.mp4"
            videoPaths.append(mux_audio_video(clipPath, ttsPath, segmentFileName, outputPath))
        
        resultFileName = "final_reel.mp4"
        finalPath = concat_videos(videoPaths, resultFileName, outputPath)
        print(f"Video created at: {finalPath}")
    

def mux_audio_video(clip_path: str, audio_path: str, outputFileName: str, outputDirectory: Path) -> str:
    outPath = outputDirectory / "segments"
    outPath.mkdir(parents=True, exist_ok=True)
    outPath  = outPath / outputFileName
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
        str(outPath),
    ]
    subprocess.run(cmd, check=True)
    return str(outPath)

def concat_videos(videoPaths: list[str], resultFileName: str, outPath: Path) -> str:
    segments_dir = outPath / "segments"
    list_path = segments_dir / "final_reel.concat.txt"
    
    with open(list_path, "w", encoding="utf-8") as f:
        for p in videoPaths:
            # We only write the filename (e.g., 'segment_0001.mp4')
            # because FFmpeg will be running in the same folder as these files
            f.write(f"file '{Path(p).name}'\n")

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path.name,  # 'final_reel.concat.txt'
        "-c", "copy",
        f"../{resultFileName}" # '../final_reel.mp4' moves it up into 'proj2'
    ]
    
    # 3. Execute from INSIDE the segments folder
    subprocess.run(cmd, check=True, cwd=segments_dir)
    
    return str(outPath / resultFileName)
        
create_project("/proj5")