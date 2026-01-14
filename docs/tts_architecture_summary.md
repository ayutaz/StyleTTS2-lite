# StyleTTS2 / StyleTTS2‑lite / Kokoro アーキテクチャ調査まとめ

作成日: 2026-01-14

## 1. 目的
StyleTTS2 / StyleTTS2‑lite / Kokoro‑82M のアーキテクチャ上の差分を整理し、
オンデバイス（Unity内完結）向けの改良方針の材料にする。

## 2. StyleTTS2（論文ベース）

### 2.1 設計の要点
- **Style diffusion**: スタイルを拡散モデルでサンプリングし、参照音声なしで多様な話し方を生成。
- **SLM（WavLM等）を識別器として利用**し、差分可能なDuration Modelingと組み合わせてE2E学習。
- **E2E波形生成**: メルではなく波形を直接生成する構成へ拡張。
- **デコーダは2系統**:
  - HifiGANベース
  - iSTFTNetベース（位相・振幅からiSTFTで波形生成）
- AdaINを使ったスタイル注入。
- 複数識別器（MPD/MRD）を組み合わせて音質を強化。

### 2.2 モジュール構成（論文記述より）
- **Acoustic modules**: Text Encoder / Style Encoder / Decoder
- **TTS prediction modules**: Duration Predictor / Prosody Predictor
- **Utility modules**: Discriminator / Text Aligner / Pitch Extractor

## 3. StyleTTS2‑lite（Hugging Faceモデルカード）

### 3.1 設計の要点
- StyleTTS2の公式重みをベースに **軽量化**。
- **削除されたコンポーネント**:
  - PLBert
  - Diffusion
  - Prosodic Encoder
  - SLM
  - Spectral Normalization

### 3.2 アーキテクチャ内訳（パラメータ数）
- Decoder: 54,289,492
- Predictor: 16,194,612
- Style Encoder: 13,845,440
- Text Encoder: 5,612,320
- **Total: 89,941,576**

### 3.3 位置づけ
- **学習コード・fine‑tune手順が公開**されており、改良や再学習が現実的。
- ただしG2Pの扱いはREADME上 espeak‑ng を前提としているため、
  商用SDK前提なら **GPL回避のG2P置換が必要**。

### 3.4 GitHubコードベースの実在と主要ファイル
- GitHubリポジトリが存在し、学習/推論/ONNX関連のコードが配置されている。
- 確認済みリポジトリ: https://github.com/dangtr0408/StyleTTS2-lite
- ローカルクローン: /Users/s19447/Documents/StyleTTS2-lite
- 確認時点のコミット: 8ebc2c2093aacd85c828052df595b1f6e2dde19f
- LICENSE は MIT ライセンス
- リポジトリには以下の主要フォルダ/ファイルが含まれる:
  - `Configs/`, `Demo/`, `Extend/`, `Models/Finetune/`, `Modules/`, `ONNX/`
  - `train.py`, `inference.py`, `models.py`, `losses.py`, `meldataset.py`, `optimizers.py`, `utils.py`
  - `.gitignore`, `pyproject.toml`, `setup.cfg`, `README.md`, `LICENSE`
  - 追加で `uv.lock`, `.python-version` が含まれる

### 3.5 推論コードで確認できる構成（inference.py）
- `StyleTTS2` 推論クラスを持ち、以下の構成でモデルを組み立てる:
  - `TextEncoder`, `StyleEncoder`, `ProsodyPredictor` を使用
  - Decoderは **設定ファイルの `decoder.type`** によって `istftnet` / `hifigan` / `vocos` を切り替える
- 参照音声からの **Style抽出**（メル変換→StyleEncoder）を行う
- `TextCleaner` により文字列→トークン列へ変換（configのシンボル辞書に依存）

### 3.6 モデル内部構成（models.py の主要クラス）
- **TextEncoder**: Embedding → 1D Convブロック → BiLSTM の構成
- **StyleEncoder**: 2D Conv + ResBlk + Global Pooling → Linear の構成
- **ProsodyPredictor**: DurationEncoder + LSTM + F0/N 推定ヘッド
- **DurationEncoder**: LSTM + AdaLayerNorm を積層
- 学習用に **ASR / JDC / Discriminator** のモジュールが import されるが、推論時は利用しない

### 3.7 Decoder/Vocoder 実装の配置（Modules/）
- `Modules/istftnet.py`, `Modules/hifigan.py`, `Modules/vocos.py` に Decoder/Generator 実装がある
- ONNX変換用の実装は `ONNX/` 配下に配置されている

### 3.8 学習パイプライン詳細（train.py / config_example.yaml / models.py / losses.py / meldataset.py / optimizers.py）
- **データ形式**: `train.txt` / `val.txt` は `wav_path|text` の2要素想定（`FilePathDataset` が2要素で読む）。
- **前処理**:
  - サンプリング周波数は 24kHz 前提（異なる場合はリサンプル）
  - 両端に 0.5 秒の無音パディング（12000サンプル）を追加
  - メルは `n_fft=2048, win_length=1200, hop_length=300, n_mels=80`
  - `log(1e-5 + mel)` を `mean=-4, std=4` で正規化
  - メル長を偶数に切り詰め
- **データローダ**:
  - `Collater` で長さ順ソート → パディング
  - `BatchSampler` はフレーム長に基づくビン分け（hop=300 を前提に時間ビン計算）
- **モデル構成（build_model）**:
  - `TextEncoder`, `StyleEncoder`, `ProsodyPredictor`
  - `text_aligner(ASRCNN)`, `pitch_extractor(JDCNet)`
  - `decoder` は `istftnet` / `hifigan` / `vocos`
  - `mpd` / `msd` を持つ
- **学習の前提**:
  - `pretrained_model` が必須（未指定だと `Must have a pretrained!` で停止）
  - 既存チェックポイントを読み込んで **追加学習/微調整**する設計
- **損失**:
  - Multi‑Resolution STFT loss（メル再構成）
  - MPD/MSD の adversarial loss + feature matching + TPRLS
  - `F0` / `Norm` の再構成 loss（Smooth L1）
  - Duration CE + L1、S2S CE、monotonic alignment loss
- **最適化**:
  - `AdamW` + `OneCycleLR` の `MultiOptimizer`
  - `decoder` と `style_encoder` は `ft_lr` に変更（他より低い学習率）

### 3.9 推論パイプライン詳細（inference.py）
- **テキスト前処理**:
  - 句読点を `.` に統一、空白正規化
  - `.` で分割 → 短文をマージ
  - `nltk.word_tokenize` を通してトークン化
  - `TextCleaner` によるシンボル辞書変換
- **参照音声のスタイル抽出**:
  - 24kHz で読み込み、最大 20 秒までに制限
  - 参照音声を分割してスタイルを平均化するモードあり
  - ノイズ低減オプションあり
- **推論ステップ**:
  - `TextEncoder` → `ProsodyPredictor` で duration 推定
  - duration を正規化して outlier を抑制、`speed` で話速調整
  - alignment から `F0/N` 推定 → `decoder` で波形生成
  - 文単位で連結、前後にパディングを追加

## 4. Kokoro‑82M（Hugging Faceモデルカード）

### 4.1 設計の要点
- **StyleTTS2 + ISTFTNet** を採用した **decoder‑only** 構成。
- **拡散なし / encoder未公開**。
- **82Mパラメータの軽量モデル**。

### 4.2 位置づけ
- 推論専用ライブラリとして公開されており、**学習コードは明示されていない**。
- 軽量・高速を重視した構成で、**オンデバイス志向の設計思想が明確**。

### 4.3 公式モデルカードの主要事実（リリース/規模/訓練）
- **リリース**:
  - v1.0（2025-01-27）: 言語 8、ボイス 54
  - v0.19（2024-12-25）: 言語 1、ボイス 10
  - v0.19 の **ONNX 版は 2025-01-02 リリース**（モデルカード記載） citeturn4view1
- **モデル仕様**: StyleTTS2 + ISTFTNet をベースにした **decoder‑only**（拡散なし/エンコーダ非公開） citeturn4view1turn2search1
- **学習データ**: permissive/非著作権の音声 + IPA ラベル（数百時間規模） citeturn4view1
- **学習コスト（参考）**: A100 80GB で合計 1000 時間相当（v0.19 + v1.0） citeturn4view1

### 4.4 公式推論ライブラリ（kokoro）
- GitHub の `hexgrad/kokoro` は **推論ライブラリ**であり、`KPipeline` を使った生成例が掲載されている citeturn7view0
- 推論は **generator 形式で `(gs, ps, audio)` を順次返す**設計（チャンク生成想定） citeturn7view0
- `lang_code` と `voice` を指定して生成する構成（多言語のコード例あり） citeturn7view0

### 4.5 G2P/トークナイザ（misaki）
- `kokoro` は **misaki G2P** を内部で使用 citeturn7view0
- misaki は **Apache‑2.0** ライセンス citeturn7view1
- 英語は `misaki[en]` で使用可能、**espeak-ng を fallback にできる**（任意） citeturn7view1
- 日本語は **pyopenjtalk + unidic** を使う第2世代トークナイザの説明がある（Pitch accent 対応） citeturn7view1

### 4.6 ONNX/コミュニティ推論の動向（参考）
- 公式モデルカードで **ONNX 版リリースが明記**されている citeturn4view1
- **コミュニティの ONNX 実装例**として `kokoro-onnx` があり、ONNX Runtime を利用する構成が示されている citeturn8view0
- 追加で **onnx-community の Kokoro-82M-ONNX** が公開されている（モデルファイル公開） citeturn6search5

### 4.7 ライセンス上の注意点（本件要件との関係）
- **モデル重み: Apache‑2.0**（商用利用に適合） citeturn4view1
- **推論コード: MIT** と明記（モデルカード） citeturn2search1
- **espeak-ng は GPLv3 依存**としてモデルカードに明記（商用 SDK では回避が必要） citeturn2search1

### 4.8 KPipeline の内部構造（コードベース確認）
- ローカルクローン: `/Users/s19447/Documents/kokoro`
- 主要実装: `kokoro/pipeline.py`
- **責務**:
  - 言語別 G2P（テキスト→phoneme）とチャンク分割
  - 声色埋め込み（voice pack）の遅延ロードとキャッシュ
- **初期化と言語処理**:
  - `lang_code` は ALIASES で正規化（`en-us`→`a` 等）
  - `a/b` は `misaki.en.G2P`（英語）で処理、`espeak` フォールバックを任意で使用
  - `j` は `misaki.ja.JAG2P`、`z` は `misaki.zh.ZHG2P`
  - その他言語は `espeak.EspeakG2P` を利用
- **voice pack 管理**:
  - `hf_hub_download` で `voices/{voice}.pt` を取得
  - 複数ボイス指定時は **平均** して単一 pack を生成
- **チャンク分割**:
  - 英語は **phoneme 長 510** を上限として chunking
  - 非英語は **約400文字**を目安に文境界で分割
- **出力**:
  - 生成は generator で `Result` を順次返す（`graphemes / phonemes / audio`）
  - `Result` は `audio`/`pred_dur` をプロパティで返す設計
  - `pred_dur` から token timestamp を計算するロジックが含まれる

### 4.9 KModel の内部構造（コードベース確認）
- 主要実装: `kokoro/model.py`
- **構成**:
  - `CustomAlbert`（PL‑BERT相当） + `bert_encoder`
  - `ProsodyPredictor` / `TextEncoder`
  - `Decoder` は `istftnet`（StyleTTS2系）
- **入力**:
  - `phonemes` を **vocab で ID 化** → `[BOS, ids..., EOS]`
  - `ref_s` は **style/prosody を分割**して利用（`[:128]` と `[128:]` を用途別に参照）
  - **BERT max position** により length 制限（`context_length`）
- **forward**:
  - duration 予測 → alignment 行列構成 → `F0/N` 推定 → `decoder` で波形生成
  - `pred_dur` は `KPipeline` 側で timestamp 生成に使う
- **ONNX**:
  - `KModelForONNX` が `forward_with_tokens` をラップ

## 5. StyleTTS2（フル）学習パイプライン詳細（train_first.py / train_second.py / config.yml / meldataset.py）

### 5.1 ステージ構成
- **第1段階（train_first.py）**: TMA + 基本音声生成の事前学習
- **第2段階（train_second.py）**: 拡散モデルとSLM adversarial を含む共同学習

### 5.2 第1段階の要点
- `ASR(text_aligner)` / `JDC(pitch_extractor)` / `PLBERT` を利用
- `TMA_epoch` 以降に **TMA（monotonic alignment） + S2S loss** を投入
- `WavLM` 特徴を使った **SLM loss** を適用
- `mpd` / `msd` で adversarial、`MultiResolutionSTFTLoss` で再構成
- `accelerate` を使った DDP 構成

### 5.3 第2段階の要点
- **拡散モデル（diffusion）** によるスタイルサンプリングを学習
- `PLBERT` によるテキスト埋め込みを使用
- `WavLM` を使った **SLM adversarial** を導入
- `diff_epoch` 以降で拡散学習開始、`joint_epoch` 以降で joint training
- DDP が不安定なため **DataParallel** 実装が使われている

### 5.4 データ仕様の違い
- `wav_path|text|speaker_id` を前提（`FilePathDataset` が 3要素を読む）
- **参照メル**と**OODテキスト**をサンプリングして学習に利用

## 6. StyleTTS2 vs StyleTTS2‑lite（差分と影響）

### 6.1 構成差分（コードベース）
- **PLBERT**: StyleTTS2 は使用、StyleTTS2‑lite では不在
- **Diffusion**: StyleTTS2 は使用、StyleTTS2‑lite では不在
- **SLM adversarial (WavLM)**: StyleTTS2 は使用、StyleTTS2‑lite では未使用
- **Prosodic style encoder**: StyleTTS2 は `predictor_encoder` を持つが lite には無い
- **Decoder選択肢**: StyleTTS2 は `istftnet / hifigan`、lite は `vocos` も選択可能
- **学習ステージ**: StyleTTS2 は 2段階、lite は 1段階（pretrained 前提）
- **データ形式**: StyleTTS2 は `speaker_id` + OOD テキスト必須、lite は不要

### 6.2 期待される品質・性能の影響（推定）
- **品質/表現力**:
  - StyleTTS2 は diffusion + PLBERT + SLM adversarial によって自然さ・多様性が高い設計
  - lite はこれらが無いため **表現力の上限が下がる可能性**
- **学習/推論コスト**:
  - StyleTTS2 は学習パイプラインが重く VRAM 要件も高い
  - lite は軽量で **学習/推論ともに現実的**
- **オンデバイス適性**:
  - どちらも推論側の構成次第だが、lite のほうが **ONNX 化と実装が簡単**

## 7. Kokoro‑82M vs StyleTTS2‑lite（参考にする候補の比較）

### 7.1 既知の差分（公開情報ベース）
- **学習コード**: Kokoro は公開されていない / StyleTTS2‑lite は学習可能
- **構成**: Kokoro は decoder‑only を志向 / StyleTTS2‑lite は text + style + predictor を持つ
- **パラメータ数**: Kokoro 82M / StyleTTS2‑lite 約 90M
- **位置づけ**: Kokoro は推論用・軽量志向、StyleTTS2‑lite は改良・再学習向き

### 7.2 実装面での示唆
- **独自学習コードを作る前提**なら StyleTTS2‑lite が安全
- **推論速度を最大化**したいなら Kokoro の構成思想は参考になるが、
  学習部分は自作が必要

## 8. まとめ（アーキテクチャ差分の要点）

- **StyleTTS2**は高品質を最優先としたフル構成
  - Diffusion + SLM + E2E波形生成 + 複数識別器
- **StyleTTS2‑lite**は「StyleTTS2から不要な重い要素を削って軽量化」
  - Diffusion / SLM / Prosody系の削除で推論負荷を低減
- **Kokoro**は「StyleTTS2の思想をさらに軽量化し、decoder‑onlyに寄せた構成」
  - 拡散やencoderを切り落とした**オンデバイス向け設計**

## 9. 結論（現時点の採用方針）

- **結論**: ベースは **StyleTTS2‑lite** を採用する方針
- **補足**: StyleTTS2 も学習/推論コードは存在するが、以下の理由で **liteが現実的**:
  - **学習/推論パイプラインが単純**で、改造・検証の回転が早い
  - **拡散 + SLM adversarial + PLBERT**を含むフル構成は学習コストが高く、PoC期間に適合しづらい
  - **ONNX/Sentis互換の難易度**が相対的に低い（演算子/モジュールが少ない）
- **位置づけ**: StyleTTS2 は **教師モデル/参考設計**として活用し、品質向上の指針に使う

## 10. 出典

- StyleTTS2 論文（ar5iv版）: https://ar5iv.labs.arxiv.org/html/2306.07691
- StyleTTS2‑lite モデルカード（Hugging Face）: https://huggingface.co/dangtr0408/StyleTTS2-lite
- StyleTTS2‑lite GitHub: https://github.com/dangtr0408/StyleTTS2-lite
- Kokoro‑82M モデルカード README: https://huggingface.co/hexgrad/Kokoro-82M/raw/main/README.md
