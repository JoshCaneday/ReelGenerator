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
        
        # USE RECURSIVE GLOB: '**/*' looks into all subfolders
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        self.image_paths = [
            p for p in self.directory.glob('**/*') 
            if p.is_file() and p.suffix.lower() in extensions
        ]
        
        if not self.image_paths:
            raise FileNotFoundError(f"No valid image files found in {self.directory.absolute()}")

        self.images = torch.stack([
            self.preprocess(Image.open(p).convert("RGB")) 
            for p in self.image_paths
        ]).to(self.device)
        
        with torch.no_grad():
            self.image_features = self.model.encode_image(self.images)
    
    def assign(self, script):
        sentence = [script]
        text = clip.tokenize(sentence).to(self.device)
        with torch.no_grad():
            logits_per_image, logits_per_text = self.model(self.images, text)
            probsImage = logits_per_text.softmax(dim=-1).cpu().numpy()
            best_idx = int(probsImage.argmax())
            
            return self.image_paths[best_idx].name