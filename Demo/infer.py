"""
Demo script for StyleTTS2-lite inference.

Prerequisites:
    wget https://huggingface.co/dangtr0408/StyleTTS2-lite/resolve/main/Models/base_model.pth -O Models/Finetune/base_model.pth
    wget https://huggingface.co/dangtr0408/StyleTTS2-lite/resolve/main/Models/config.yaml -O Configs/config.yaml

Usage:
    uv sync --extra demo
    uv run Demo/infer.py
"""
import soundfile as sf
import sys
import torch
import numpy as np
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from inference import StyleTTS2
from g2p import G2PPipeline


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    config_path = str(root_dir / "Configs" / "config.yaml")
    models_path = str(root_dir / "Models" / "Finetune" / "base_model.pth")

    print(f"Device: {device}")
    print(f"Config: {config_path}")
    print(f"Model: {models_path}")

    model = StyleTTS2(config_path, models_path).eval().to(device)

    # Initialize G2P pipeline (supports Japanese & English)
    g2p = G2PPipeline()

    # English text
    text = "Nearly 300 scholars currently working in the United States have applied for positions at Aix Marseille University in France."

    # Convert text to phonemes using G2PPipeline
    phonemes = g2p.convert(text)
    print(f"Text: {text}")
    print(f"Phonemes: {phonemes[:100]}...")

    speed = 1
    denoise = 0.2
    avg_style = True
    stabilize = True

    speaker = {
        "path": str(root_dir / "Demo" / "Audio" / "1_heart.wav"),
        "speed": speed,
    }

    with torch.no_grad():
        styles = model.get_styles(speaker, denoise, avg_style)
        r = model.generate(phonemes, styles, stabilize, 18)
        r = r / np.max(np.abs(r))  # Normalize

    sr = 24000
    output_path = "audio.wav"
    sf.write(output_path, r, sr)
    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
