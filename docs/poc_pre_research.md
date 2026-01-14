# PoC事前調査メモ（TTS × Unity）

作成日: 2026-01-14

## 1. 前提と目的

- エンタメ用途のUnity向けTTSモデルおよびSDKのPoCを実施する
- 体制は1人、助言者あり
- 予算は人件費以外に活用（最大200万円）
- GPUはRTX 6000 Ada 1台を無償利用
- 生成はサーバーNG、Unity内で完結するオンデバイスTTSが必須
- 推論基盤はSentis 2.4.1を採用（ONNX Runtimeはバックアップ候補）
- 商用SDK販売を前提とし、GPL/AGPL系（例: espeak-ng等）は使用しない方針

## 2. ベースモデル候補の調査

### 2.1 CosyVoice（CosyVoice 3系）

- ライセンス: Apache-2.0
- 特徴: 9言語対応、指示（感情・速度等）の指定、テキスト入力ストリーミングと音声出力ストリーミングの両対応、低遅延（~150ms）を掲げる
- CosyVoice 3論文では、学習データを約100万時間、モデル規模を1.5Bへスケールアップしている
- 1台GPU環境では「一からの学習」よりも「既存モデルの推論・微調整」前提でPoCを設計するのが現実的

### 2.2 StyleTTS2

- コードはMITライセンスだが、推論はGPLライセンス依存（GPLフォークあり）
- MITのみで動作する代替パッケージ（gruut利用）は品質が下がる旨の記載あり
- 事前学習モデル利用時は「合成音声である旨の告知」と「声の利用許諾」が条件
- PL-BERTは英語事前学習のみで、他言語は言語別PL-BERTや多言語PL-BERT（14言語対応）を用いる必要がある
- 学習時間の目安: 1時間分のデータを4xA100で約4時間、24時間データの学習は4xA100で約2.5日

### 2.3 KokoroTTS（Kokoro-82M）

- Apache-2.0で公開されているオープンウェイトTTSモデル
- StyleTTS2アーキテクチャとISTFTNetデコーダに基づいた「decoder-only」構成（diffusionなし、encoder公開なし）
- 公式リリースでは複数言語・複数話者が提供されている
- 公式の推論実装では「kokoro」パッケージと「misaki」G2Pが使われる
- 日本語対応にはmisakiの日本語パッケージ利用が必要
- 注意: 公式モデルカードで「偽サイトが存在する」旨の注意喚起があるため、公式リポジトリ/モデルカードに限定して参照する

## 3. 既存活動の確認（ユーザー実施分）

### 3.1 piper-plus

- Piper TTSを拡張した実装で、WebUI・WebAssembly対応、辞書・音素入力・OpenJTalk統合などの機能が追加されている
- ローカル/ブラウザ動作の両面でPoCに転用しやすい構成

### 3.2 uPiper

- Unity AI Inference Engine（Sentis）を使ったローカル推論構成
- piper-plusをベースに、OpenJTalk統合・GPU推論サポートを実装
- 日本語/英語対応、Unity 2023.2以上を想定
- 英語G2PはeSpeak依存を避けた実装があり、以下のGPLフリー系バックエンドが利用可能:
  - RuleBasedPhonemizer（MIT）: CMU辞書 + ルールベースG2P
  - EnhancedEnglishPhonemizer（MIT）: CMU辞書 + 統計G2P + 同形異義語/形態素対策
  - FliteLTSPhonemizer（BSD/Flite）: Flite LTSのC#実装 + CMU辞書
- eSpeak-NG（GPLv3）のネイティブプラグインも含まれるため、商用配布時は除外・未使用を徹底する必要あり

### 3.3 uZipVoice

- ZipVoice/ZipVoice-SFTのUnity実装（Unity 6 + AI Inference Engine）
- 数秒の参照音声でのゼロショットTTSに対応
- Flow Matchingの4/8/16ステップ推論に対応

### 3.4 CosyVoice3 ONNX化の検証（はてな記事）

- CosyVoice3を完全ONNX化し、PyTorchなしで推論する構成を検証
- 文字列先頭の言語タグがそのまま発話される問題があり、自動言語検出で回避
- ONNX Runtime 1.19以降でFP16読み込みエラーが発生し、1.18.0で回避できた旨の記載

## 4. PoCアプローチ案（Unityマルチプラットフォーム / オンデバイス必須）

### 4.1 実行基盤の選択（Sentis 2.4.1を主採用）

- Unity Sentis 2.4.1を主採用し、Unity内完結を優先
- Unity Sentisは「全Unityランタイム」をサポートし、ONNX opset 7〜15を推奨範囲としている
- ただしSentisはQuantize/Dequantize系やQLinear系など、量子化関連のONNX演算を未サポート
- 量子化ONNXを使う場合は、UnityネイティブプラグインとしてONNX Runtime Mobileを組み込む方が現実的
- ONNX Runtime Mobileは、AndroidでXNNPACK、iOSでCoreMLのEP利用が可能（Sentis未対応時の補助）

### 4.2 テキストフロントエンド（G2P）

- 日本語: OpenJTalk（辞書と形態素）またはmisaki[ja]
- 英語: CMU辞書またはmisaki/en
- どちらも「正規化→音素列→ID化」を共通APIとして抽象化
- misakiはPython依存で、日本語はpyopenjtalk+UniDicの利用が前提。Unity内利用にはC# or C++実装への置換が必要
- 商用配布を前提に、英語G2PはCMUdict + 独自実装（uPiperの実装を参考）で置き換える方針

### 4.3 推論ランタイム

- Unity Sentis 2.4.1: ONNX opset対応とオペレータ制約のため、モデル分割や簡略化が必要になる可能性
- ONNX Runtime: Sentisで未対応演算がある場合のバックアップとして検討

### 4.4 ONNX化の進め方

- まずはSentis動作を前提に推論パスのみONNX化（学習はPyTorch）
- 大型モデルは「複数ONNX分割」「FP16/FP32混在」「動的形状回避」が必須になる可能性
- 既存のCosyVoice3 ONNX化検証を再利用し、Unity向けに段階的に最適化

## 5. 追加候補TTS（オンデバイス向き）

- Kokoro-82M: Apache-2.0のオープンウェイト、v1.0で8言語/54話者。日本語ボイスも存在するが、非英語はG2Pとデータ量の弱さで品質が落ちる旨の注意がある
- Kokoro-82M ONNX: onnx-community版で量子化済みモデルが提供され、FP16/INT8でサイズが大幅に縮小される
- StyleTTS2-lite: StyleTTS2系の軽量版でMITライセンス。公開済みチェックポイントは英語/ベトナム語が中心で、日本語は追加学習が必要
- StyleTTS2（本家）: コードはMITだが事前学習モデルには追加の利用条件があるため、商用配布時に注意が必要

## 6. GPU・計算資源の前提

- RTX 6000 Adaは48GB GDDR6メモリ、300Wクラス
- 1台GPU前提のため、巨大モデルのフル学習よりも「推論」「小規模微調整」「最適化（量子化・バッチ調整）」に重きを置く

## 7. PoCで検証すべき技術項目

- 低遅延の実測（初回チャンク到達時間、RTF）
- 音質評価（MOS相当の主観評価、明瞭度/破綻率）
- 日本語テキスト正規化・読み上げ精度
- Unity内API（Sentis/ネイティブ連携）の設計
- 音声データパイプライン（収録→前処理→メタデータ整備）

## 8. PoCの成果物イメージ

- Unity内推論パッケージ（Sentis前提）
- Unityサンプルシーン（スクリプト付き）
- 評価レポート（遅延・音質・運用条件）
- 将来拡張に向けた課題整理（ライセンス、権利、データ要件）

## 9. リスク・留意点

- ライセンス（GPL依存、事前学習モデルの利用条件）
- 音声権利（収録者の同意と利用許諾の明確化）
- 日本語対応に必要な追加学習（PL-BERT等）
- 単一GPU環境での学習・推論負荷
- G2Pのライセンス汚染リスク（AGPL系コードの流用に注意）

## 10. 参考リンク

- CosyVoice GitHub: https://github.com/FunAudioLLM/CosyVoice
- CosyVoice 3論文: https://arxiv.org/abs/2505.17589
- StyleTTS2 GitHub: https://github.com/yl4579/StyleTTS2
- KokoroTTS（モデルカード）: https://huggingface.co/hexgrad/Kokoro-82M
- KokoroTTS（推論リポジトリ）: https://github.com/hexgrad/kokoro
- Kokoro-82M-ONNX（onnx-community）: https://huggingface.co/onnx-community/Kokoro-82M-ONNX
- StyleTTS2-lite: https://github.com/dangtr0408/StyleTTS2-lite
- Unity Sentis Supported platforms/opset: https://docs.unity.cn/Packages/com.unity.sentis%402.1/manual/index.html
- Unity Sentis Supported operators: https://docs.unity.cn/Packages/com.unity.sentis%402.1/manual/supported-operators.html
- ONNX Runtime Mobile: https://onnxruntime.ai/docs/tutorials/mobile/
- NVIDIA RTX 6000 Ada: https://www.nvidia.com/en-us/products/workstations/rtx-6000/
- Lenovo RTX 6000 Ada Product Guide: https://lenovopress.lenovo.com/lp1940-thinksystem-nvidia-rtx-6000-ada-48gb-pcie-active-gpu
- piper-plus: https://github.com/ayutaz/piper-plus
- uPiper: https://github.com/ayutaz/uPiper
- uZipVoice: https://github.com/ayutaz/uZipVoice
- CosyVoice3 ONNX検証記事: https://ayousanz.hatenadiary.jp/entry/2026/01/14/005400
