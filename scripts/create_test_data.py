"""Create minimal test dataset for training pipeline verification."""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from g2p import G2PPipeline

# Sample texts for each audio file (English transcriptions)
SAMPLE_TEXTS = {
    "1_heart.wav": "The heart beats with passion and love.",
    "2_belle.wav": "Belle danced gracefully through the hall.",
    "3_kore.wav": "The ancient temple stood in silence.",
    "4_sarah.wav": "Sarah walked down the sunny street.",
    "5_nova.wav": "A nova exploded in the distant galaxy.",
    "6_sky.wav": "The sky was painted with brilliant colors.",
    "7_alloy.wav": "The alloy was forged in intense heat.",
    "8_jessica.wav": "Jessica smiled warmly at her friends.",
    "9_river.wav": "The river flowed gently to the sea.",
    "10_michael.wav": "Michael played his guitar softly.",
    "11_fenrir.wav": "The legend of Fenrir was told by elders.",
    "12_puck.wav": "Puck danced merrily in the moonlight.",
    "13_echo.wav": "An echo rang through the mountains.",
    "14_eric.wav": "Eric finished reading his favorite book.",
    "15_liam.wav": "Liam walked through the autumn leaves.",
    "16_onyx.wav": "The onyx stone gleamed in darkness.",
    "17_santa.wav": "Santa brought gifts to all the children.",
    "18_adam.wav": "Adam watched the sunrise from the hill.",
}


def main():
    # Initialize G2P
    g2p = G2PPipeline()

    # Create output directory
    data_dir = root_dir / "Data" / "test"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Generate IPA transcriptions
    train_lines = []
    val_lines = []

    audio_files = list(SAMPLE_TEXTS.keys())

    for i, (audio_file, text) in enumerate(SAMPLE_TEXTS.items()):
        # Convert to IPA
        ipa = g2p.convert(text, language="en")

        # Create line: relative_path|IPA
        line = f"Demo/Audio/{audio_file}|{ipa}"

        # Split: first 3 for validation, rest for training
        if i < 3:
            val_lines.append(line)
        else:
            train_lines.append(line)

        print(f"[{'VAL' if i < 3 else 'TRAIN'}] {audio_file}: {ipa[:50]}...")

    # Write train.txt
    train_path = data_dir / "train.txt"
    with open(train_path, "w", encoding="utf-8") as f:
        f.write("\n".join(train_lines))
    print(f"\nWritten {len(train_lines)} samples to {train_path}")

    # Write val.txt
    val_path = data_dir / "val.txt"
    with open(val_path, "w", encoding="utf-8") as f:
        f.write("\n".join(val_lines))
    print(f"Written {len(val_lines)} samples to {val_path}")


if __name__ == "__main__":
    main()
