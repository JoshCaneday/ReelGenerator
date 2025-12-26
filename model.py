from pathlib import Path
import torch
import clip
from PIL import Image
import numpy as np
from pathlib import Path

class TextToImage:
    def __init__(self, cache_file='image_embeddings.pt'):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cache_path = Path(cache_file)
        
        if not self.cache_path.exists():
            raise FileNotFoundError("Run the preprocessing notebook first to generate image_embeddings.pt")

        # 1. Load CLIP (We still need this to encode the SCRIPT text)
        print("Loading CLIP model...")
        self.model, _ = clip.load("RN50", device=self.device)
        
        # 2. Load the pre-computed features
        print("Loading pre-computed embeddings...")
        data = torch.load(self.cache_path, map_location=self.device)
        
        self.image_features = data['features'].to(self.device)
        self.image_paths = data['paths']
    
    def assign(self, script):
        text = clip.tokenize([script]).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            similarity = (text_features @ self.image_features.T)
            best_idx = similarity.argmax().item()
            
            return Path(self.image_paths[best_idx]).name