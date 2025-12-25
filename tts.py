from TTS.api import TTS
from pathlib import Path
import torch
import wave

class MYTTS:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)

    def generate(self, text, voice, outputFileName, outputDirectory):
        # Convert to Path objects for robust path joining
        outputDirectory += "/tts"
        out_dir = Path(outputDirectory)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        output_file_path = out_dir / f"{outputFileName}.wav"
        speaker_path = Path("./voices") / f"{voice}.wav"

        self.tts.tts_to_file(
            text=text,
            file_path=str(output_file_path),
            speaker_wav=str(speaker_path),
            language="en"
        )
        
        return str(output_file_path), self.wav_duration_seconds(str(output_file_path))

    def wav_duration_seconds(self, path: str) -> float:
        with wave.open(path, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
        return frames / float(rate)