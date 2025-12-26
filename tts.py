from TTS.api import TTS
from pathlib import Path
import torch
import wave

class MYTTS:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)

    def generate(self, text: str, voice: str, outputFileName: str, outputDirectory: Path):
        # Convert to Path objects for robust path joining
        outPath = outputDirectory / "tts"
        outPath.mkdir(parents=True, exist_ok=True)
        
        outPath = outPath / outputFileName
        speaker_path = Path("./voices") / f"{voice}"

        self.tts.tts_to_file(
            text=text,
            file_path=str(outPath),
            speaker_wav=str(speaker_path),
            language="en"
        )
        
        return str(outPath), self.wav_duration_seconds(str(outPath))

    def wav_duration_seconds(self, path: str) -> float:
        with wave.open(path, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
        return frames / float(rate)