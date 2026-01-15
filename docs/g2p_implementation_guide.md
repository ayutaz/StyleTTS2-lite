# G2P実装ガイド（実装完了）

StyleTTS2-lite用の日英G2P（Grapheme-to-Phoneme）パイプライン

**ステータス**: ✅ 実装完了（2026-01-15）

## 1. 概要

日本語・英語のテキストをIPA音素列に変換するG2Pパイプラインを実装済み。
GPL/AGPL依存なしで商用利用可能。

### 採用技術

| 言語 | ライブラリ | ライセンス |
|------|-----------|----------|
| 日本語 | pyopenjtalk-plus | MIT/BSD |
| 英語 | CMU辞書 + NLTK | Public Domain / Apache 2.0 |

## 2. ファイル構成

```
g2p/
├── __init__.py           # G2PPipeline（統合API・言語判定）
├── japanese/
│   ├── __init__.py
│   ├── g2p.py            # JapaneseG2P
│   └── converter.py      # pyopenjtalk → IPA変換マッピング
└── english/
    ├── __init__.py
    ├── g2p.py            # EnglishG2P（ARPABET → IPA）
    ├── cmu_dict.py       # CMU辞書ローダー
    └── fallback.py       # ルールベースフォールバック
```

## 3. 使用方法

### 3.1 基本的な使い方

```python
from g2p import G2PPipeline

pipeline = G2PPipeline()

# 日本語
pipeline.convert("こんにちは")
# -> "k o ɴ n i ʧ i w ɑ"

# 英語
pipeline.convert("Hello world")
# -> "hʌloʊ wɚld"

# 混在（自動言語判定）
pipeline.convert("Hello、こんにちは")
# -> "hʌloʊ , k o ɴ n i ʧ i w ɑ"

# 言語を明示指定
pipeline.convert("テスト", language="ja")
pipeline.convert("test", language="en")
```

### 3.2 個別G2Pの使用

```python
# 日本語のみ
from g2p.japanese import JapaneseG2P
ja_g2p = JapaneseG2P()
ja_g2p.convert("東京")  # -> "t o o k j o o"

# 英語のみ
from g2p.english import EnglishG2P
en_g2p = EnglishG2P()
en_g2p.convert("Tokyo")  # -> "toʊkioʊ"
```

### 3.3 学習データ作成

```python
from g2p import G2PPipeline

pipeline = G2PPipeline()

# テキストファイルからIPA変換済みマニフェスト作成
with open('raw_texts.txt', 'r') as f_in, \
     open('train.txt', 'w') as f_out:
    for line in f_in:
        wav_path, text = line.strip().split('|')
        ipa = pipeline.convert(text)
        f_out.write(f"{wav_path}|{ipa}\n")
```

## 4. 動作テスト結果

### 4.1 日本語

| 入力 | 出力 |
|------|------|
| こんにちは | `k o ɴ n i ʧ i w ɑ` |
| ありがとうございます | `ɑ ɾ i ɡ ɑ t o o ɡ o z ɑ i m ɑ s ɯ` |
| 東京 | `t o o k j o o` |

### 4.2 英語

| 入力 | 出力 |
|------|------|
| Hello world | `hʌloʊ wɚld` |
| Thank you very much | `θæŋk ju vɛɹi mʌʧ` |

### 4.3 混在

| 入力 | 出力 |
|------|------|
| Hello、こんにちは | `hʌloʊ , k o ɴ n i ʧ i w ɑ` |

## 5. 音素マッピング

### 5.1 日本語（pyopenjtalk → IPA）

| pyopenjtalk | IPA | 説明 |
|-------------|-----|------|
| a | ɑ | 開母音 |
| i | i | 前舌高母音 |
| u | ɯ | 非円唇後舌高母音 |
| e | e | 前舌中母音 |
| o | o | 後舌中母音 |
| N | ɴ | 撥音（ん） |
| cl/q | ʔ | 促音（っ） |
| r | ɾ | はじき音 |
| sh | ʃ | 無声後部歯茎摩擦音 |
| ch | ʧ | 無声後部歯茎破擦音 |
| j | ʤ | 有声後部歯茎破擦音 |
| ts | ts | 無声歯茎破擦音 |
| f | ɸ | 無声両唇摩擦音 |
| hy | ç | 無声硬口蓋摩擦音 |
| g | ɡ | 有声軟口蓋破裂音（U+0261） |
| y | j | 硬口蓋接近音 |

### 5.2 英語（ARPABET → IPA）

| ARPABET | IPA | 例 |
|---------|-----|-----|
| AA | ɑ | father |
| AE | æ | cat |
| AH | ʌ | cup |
| ER | ɚ | bird |
| IY | i | see |
| UW | u | too |
| TH | θ | think |
| DH | ð | this |
| SH | ʃ | she |
| ZH | ʒ | vision |
| CH | ʧ | church |
| JH | ʤ | judge |
| NG | ŋ | sing |

## 6. StyleTTS2-liteとの統合

### 6.1 TextCleanerとの互換性

G2Pの出力はTextCleanerで直接処理可能：

```python
from meldataset import TextCleaner
from g2p import G2PPipeline

# G2Pでテキスト変換
pipeline = G2PPipeline()
ipa = pipeline.convert("こんにちは")

# TextCleanerでID列に変換
cleaner = TextCleaner(symbol_dict, debug=True)
ids = cleaner(ipa)
```

### 6.2 inference.pyへの統合（実装完了）

`inference.py`にG2Pパイプラインが統合済み：

```python
from g2p import G2PPipeline

class StyleTTS2:
    def __init__(self, config_path, models_path):
        # G2Pパイプライン
        self.g2p = G2PPipeline()

    def generate_from_text(self, text, style, stabilize=True, n_merge=16, language=None):
        """テキストから直接音声生成（G2P統合版）"""
        phonemes = self.g2p.convert(text, language=language)
        return self.generate(phonemes, style, stabilize, n_merge)
```

既存の`generate()`は音素入力のまま維持（後方互換性）。

## 7. 注意事項

### 7.1 日本語特有の問題

- **長音**: 現状は連続母音として出力（例: 東京 → `t o o k j o o`）
- **アクセント**: 現状未対応（将来的にプロソディ情報を追加可能）

### 7.2 英語特有の問題

- **未登録語**: CMU辞書にない単語はルールベースフォールバック（精度低下）
- **同形異義語**: 文脈による発音の違いは未対応（例: read/read）

### 7.3 シンボルセット拡張

必要に応じて`config.yaml`の`extend`に追加：

```yaml
symbol:
  extend: "ɴː"  # 追加シンボル
```

## 8. 次のステップ

- [x] G2Pパイプライン実装
- [x] 日本語G2P（pyopenjtalk-plus）
- [x] 英語G2P（CMU辞書）
- [x] 動作テスト
- [x] inference.pyへの統合
- [x] pytestテストスイート（34テスト）
- [ ] 日本語学習データの作成
- [ ] 日本語モデルの学習
