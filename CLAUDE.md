# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

**tukuyomi（読本）** - StyleTTS2-liteをベースにしたUnity向け日英オンデバイスTTS（Text-to-Speech）PoCプロジェクト

### 目標
- Unity Sentis 2.4.1での完全オンデバイス推論
- 日本語・英語の両言語サポート
- 商用SDK販売を前提としたGPL/AGPL依存の完全排除
- マルチプラットフォーム対応（Android/iOS/Windows/macOS/Linux）

### ライセンス制約
- GPL/AGPL依存は使用禁止
- G2P実装はOSS辞書の直接利用を避け独自実装（espeak-ngは使用不可）
- 学習データのライセンス確認必須

## 開発コマンド

```bash
# 依存パッケージのインストール
uv sync --extra demo --extra onnx

# 学習の実行
python train.py -p Configs/config.yaml

# 推論（デモ）
uv run Demo/infer.py

# ONNX変換
uv run ONNX/export_onnx.py
```

## アーキテクチャ

### TTSモデル構成

```
テキスト入力
    ↓
[G2P変換] テキスト → 音素列（独自実装予定）
    ↓
[TextEncoder] Embedding → 1D Conv → BiLSTM (5.6M params)
    ↓
[StyleEncoder] 2D Conv + ResBlock + Global Pooling → Linear (13.8M params)
    ↓
[ProsodyPredictor] Duration推定 + F0/Norm推定 (16.2M params)
    ↓
[Decoder: ISTFTNet/HiFiGAN/Vocos] 位相・振幅 → 波形生成 (54.3M params)
    ↓
音声出力
```

### 主要ファイル構成

| ファイル | 役割 |
|---------|------|
| `train.py` | 学習パイプライン（pretrained必須） |
| `inference.py` | 推論API（StyleTTS2クラス） |
| `models.py` | モデル定義（TextEncoder, StyleEncoder, ProsodyPredictor） |
| `meldataset.py` | データローダー、TextCleaner |
| `losses.py` | 損失関数（MultiResolutionSTFTLoss等） |
| `Modules/` | Decoder実装（istftnet, hifigan, vocos） |
| `ONNX/` | ONNX変換・推論コード |

### 設定ファイル（Configs/config_example.yaml）

- **シンボルセット**: 178トークン（pad + 句読点 + 英字 + IPA）
- **モデルパラメータ**: hidden_dim=512, style_dim=128
- **Decoder選択**: `decoder.type` で `istftnet` / `hifigan` / `vocos` を切替
- **学習戦略**: `training_strats` でモジュールのfreeze/ignore設定

### データフォーマット

学習データ（train.txt, val.txt）:
```
wav_path|IPA音素列
libriTTS/train/1.wav|ðə kæt sæt ɑn ðə mæt
```

音声仕様:
- サンプリング: 24kHz
- メルスペクトログラム: n_fft=2048, hop=300, n_mels=80

## G2P実装（実装完了）

日英G2P（Grapheme-to-Phoneme）パイプラインを実装済み。GPL/AGPL依存なし。

### 使用方法

```python
from g2p import G2PPipeline

pipeline = G2PPipeline()

# 日本語
pipeline.convert("こんにちは")  # -> "k o ɴ n i ʧ i w ɑ"

# 英語
pipeline.convert("Hello world")  # -> "hʌloʊ wɚld"

# 混在（自動言語判定）
pipeline.convert("Hello、こんにちは")  # -> "hʌloʊ , k o ɴ n i ʧ i w ɑ"
```

### ファイル構成

```
g2p/
├── __init__.py           # G2PPipeline（統合API・言語判定）
├── japanese/
│   ├── g2p.py            # JapaneseG2P（pyopenjtalk-plus）
│   └── converter.py      # pyopenjtalk → IPA変換マッピング
└── english/
    ├── g2p.py            # EnglishG2P（ARPABET → IPA）
    ├── cmu_dict.py       # CMU辞書ローダー（NLTK）
    └── fallback.py       # ルールベースフォールバック
```

### ライセンス
- 日本語: pyopenjtalk-plus（MIT/BSD）
- 英語: CMU辞書（Public Domain）+ NLTK（Apache 2.0）

## ドキュメント（docs/）

| ファイル | 内容 |
|---------|------|
| `poc_plan.md` | PoC実行計画・成果物定義 |
| `roadmap.md` | 5フェーズ開発ロードマップ |
| `tts_architecture_summary.md` | StyleTTS2/Lite/Kokoroの詳細比較 |
| `g2p_research.md` | G2Pライブラリ調査・選定理由 |
| `g2p_implementation_guide.md` | G2P実装の引き継ぎ資料 |
| `poc_pre_research.md` | 既存TTS実装の比較調査 |

## 品質基準（PoC判定ゲート）

- RTF（Real-time Factor）< 1.0
- 初回レイテンシ < 1秒
- MOS・誤読率が目標水準達成
