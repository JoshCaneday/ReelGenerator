from pathlib import Path
import torch
import clip
from PIL import Image
import numpy as np
from pathlib import Path

class TextToImage:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu" 
        self.model, self.preprocess = clip.load("RN50", device=self.device)
        self.directory = Path('./images')
        self.images = torch.stack([self.preprocess(Image.open(p).convert("RGB")) for p in self.directory.glob('*')]).to(self.device)
        with torch.no_grad():
            self.image_features = self.model.encode_image(self.images)
    
    def assign(self,script):
        sentences = script.strip().split(".")
        text = clip.tokenize(sentences).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(text)

            logits_per_image, logits_per_text = self.model(self.images, text)
            probsText = logits_per_image.softmax(dim=-1).cpu().numpy()
            probsImage = logits_per_text.softmax(dim=-1).cpu().numpy()
        # do more
