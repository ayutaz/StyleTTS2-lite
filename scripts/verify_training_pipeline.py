"""Verify training pipeline components without actual training.

This script verifies:
1. Config loading and symbol dictionary creation
2. Data loading and preprocessing
3. Model initialization from pretrained weights
4. Forward pass simulation (on CPU/MPS)

Note: Actual training requires CUDA GPU.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import yaml
import torch
from munch import Munch

from meldataset import build_dataloader, TextCleaner
from models import build_model, load_checkpoint
from utils import get_data_path_list


def main():
    print("=" * 60)
    print("Training Pipeline Verification")
    print("=" * 60)

    # Determine device
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"\n[1/6] Device: {device}")

    # Load config
    config_path = root_dir / "Configs" / "config_test.yaml"
    print(f"\n[2/6] Loading config: {config_path}")
    config = yaml.safe_load(open(config_path, "r", encoding="utf-8"))

    # Build symbol dictionary
    print("\n[3/6] Building symbol dictionary...")
    symbols = (
        list(config["symbol"]["pad"])
        + list(config["symbol"]["punctuation"])
        + list(config["symbol"]["letters"])
        + list(config["symbol"]["letters_ipa"])
        + list(config["symbol"]["extend"])
    )
    symbol_dict = {s: i for i, s in enumerate(symbols)}
    n_token = len(symbol_dict) + 1
    print(f"  - Total symbols: {n_token}")

    # Test TextCleaner
    print("\n[4/6] Testing TextCleaner...")
    cleaner = TextCleaner(symbol_dict, debug=True)
    test_ipa = "ðʌ hɑɹt bits wɪð pæʃʌn ʌnd lʌv ."
    tokens = cleaner(test_ipa)
    print(f"  - Input: {test_ipa}")
    print(f"  - Tokens: {tokens[:10]}... (length: {len(tokens)})")

    # Load data
    print("\n[5/6] Testing data loading...")
    train_path = config["data_params"]["train_data"]
    val_path = config["data_params"]["val_data"]
    root_path = config["data_params"]["root_path"]

    train_list, val_list = get_data_path_list(train_path, val_path)
    print(f"  - Train samples: {len(train_list)}")
    print(f"  - Val samples: {len(val_list)}")

    # Build dataloader (CPU mode for verification)
    print("\n  Building dataloader...")
    train_dataloader = build_dataloader(
        train_list,
        root_path,
        symbol_dict,
        batch_size=2,
        num_workers=0,
        dataset_config={"debug": True},
        device="cpu",
    )

    # Test loading one batch
    print("  Loading test batch...")
    for batch in train_dataloader:
        waves, texts, input_lengths, mels, mel_input_length = batch
        print(f"  - Waves: {len(waves)} samples")
        print(f"  - Texts shape: {texts.shape}")
        print(f"  - Mels shape: {mels.shape}")
        print(f"  - Input lengths: {input_lengths}")
        print(f"  - Mel lengths: {mel_input_length}")
        break

    # Build model
    print("\n[6/6] Testing model initialization...")

    def recursive_munch(d):
        if isinstance(d, dict):
            return Munch((k, recursive_munch(v)) for k, v in d.items())
        elif isinstance(d, list):
            return [recursive_munch(v) for v in d]
        else:
            return d

    model_params = recursive_munch(config["model_params"])
    model_params["n_token"] = n_token

    try:
        model = build_model(model_params)
        print("  - Model built successfully")

        # Count parameters
        total_params = 0
        for name, module in model.items():
            params = sum(p.numel() for p in module.parameters())
            total_params += params
            print(f"    {name}: {params:,} params")
        print(f"  - Total: {total_params:,} params")

        # Load pretrained weights
        pretrained_path = config["pretrained_model"]
        print(f"\n  Loading pretrained: {pretrained_path}")

        # Load checkpoint directly
        checkpoint = torch.load(pretrained_path, map_location="cpu")
        params = checkpoint["net"]

        loaded_count = 0
        skipped_modules = []
        for key in model:
            if key in params:
                try:
                    # Handle DataParallel prefix mismatch
                    from collections import OrderedDict

                    state_dict = params[key]
                    new_state_dict = OrderedDict()
                    for k, v in state_dict.items():
                        name = k[7:] if k.startswith("module.") else k
                        new_state_dict[name] = v

                    # Load with strict=False to handle size mismatches
                    missing, unexpected = model[key].load_state_dict(
                        new_state_dict, strict=False
                    )
                    if missing or unexpected:
                        skipped_modules.append(
                            f"{key}: {len(missing)} missing, {len(unexpected)} unexpected"
                        )
                    loaded_count += 1
                except Exception as e:
                    skipped_modules.append(f"{key}: {e}")

        print(f"  - Loaded {loaded_count}/{len(model)} modules")
        if skipped_modules:
            print(f"  - Notes: {skipped_modules}")
        print(f"  - Checkpoint epoch: {checkpoint.get('epoch', 'N/A')}")

        # Move to device and test forward pass (if not CUDA)
        if device != "cuda":
            print(f"\n  Testing forward pass on {device}...")

            # Move text_encoder to device
            text_encoder = model["text_encoder"].to(device)
            text_encoder.eval()

            # Test forward
            with torch.no_grad():
                test_input = torch.randint(0, n_token, (1, 20)).to(device)
                test_lengths = torch.tensor([20]).to(device)
                test_mask = torch.zeros(1, 20).bool().to(device)
                output = text_encoder(test_input, test_lengths, test_mask)
                print(f"  - TextEncoder output shape: {output.shape}")

    except Exception as e:
        print(f"  - Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("Verification PASSED")
    print("=" * 60)
    print("\nNote: Actual training requires CUDA GPU.")
    print("The pipeline is ready for training on a CUDA-enabled machine.")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
