from TTS.api import TTS
import torch
import wave

class TTS:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)

    def generate(self,text,voice,outputFileName,outputDirectory):
        outputPath = outputDirectory + outputFileName + ".wav"
        self.tts.tts_to_file(text=text,
                file_path=outputPath,
                speaker_wav="./voices/" + voice + ".wav",
                language="en")
        return outputPath, self.wav_duration_seconds(outputPath)

    def wav_duration_seconds(self, path: str) -> float:
        with wave.open(path, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
        return frames / float(rate)