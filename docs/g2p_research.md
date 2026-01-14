# G2P実装調査レポート

## 1. 調査目的

Unity向け日英TTSのG2P（Grapheme-to-Phoneme）実装に向けた技術選定。
商用SDK化を前提としたGPL/AGPL依存の排除が必須条件。

## 2. 候補ライブラリ比較

### 2.1 日本語G2P

| 項目 | pyopenjtalk-plus | misaki[ja] |
|------|------------------|------------|
| **リポジトリ** | [tsukumijima/pyopenjtalk-plus](https://github.com/tsukumijima/pyopenjtalk-plus) | [hexgrad/misaki](https://github.com/hexgrad/misaki) |
| **ライセンス** | MIT + Modified BSD + Apache 2.0 | Apache-2.0 |
| **内部依存** | OpenJTalk + カスタム辞書 | pyopenjtalk + unidic + **espeak-ng (GPLv3)** |
| **対応言語** | 日本語のみ | 日/英/韓/中/越 |
| **Python 3.13** | ✓ 対応済み | 要確認 |
| **インストール** | 事前ビルド済みwheel | 複数依存（spaCy等） |
| **商用利用** | ✓ 問題なし | ⚠️ espeak-ng依存でGPL汚染リスク |

### 2.2 英語G2P

| 項目 | CMU辞書 + ルールベース | misaki[en] |
|------|------------------------|------------|
| **ライセンス** | パブリックドメイン | Apache-2.0（ただしespeak依存） |
| **精度** | 辞書登録語は高精度、未登録語は低め | 高精度 |
| **依存** | nltk or ファイル直接読込 | spaCy + espeak-ng |
| **商用利用** | ✓ 問題なし | ⚠️ GPL汚染リスク |

### 2.3 採用決定

| 言語 | 採用 | 理由 |
|------|------|------|
| **日本語** | pyopenjtalk-plus | ライセンスクリーン、wheel同梱で導入簡単 |
| **英語** | CMU辞書 + ルールベース | パブリックドメイン、GPL依存なし |

## 3. ライセンス詳細

### pyopenjtalk-plus

```
pyopenjtalk-plus本体: MIT License
OpenJTalk: Modified BSD License
marine（アクセント推定）: Apache 2.0 License
```

すべて**商用利用可能**。GPL/AGPL依存なし。

### CMU Pronouncing Dictionary

```
License: Public Domain
URL: http://www.speech.cs.cmu.edu/cgi-bin/cmudict
収録語数: 約134,000語
```

### misakiの問題点

misakiはKokoro用に設計された多言語G2Pだが、**espeak-ng（GPLv3）** をフォールバックとして使用している。商用SDKでの利用はGPL汚染リスクがある。

## 4. 音素マッピング設計

### 4.1 StyleTTS2-liteのシンボルセット

StyleTTS2-liteは178シンボルのIPAベースセットを使用：

```yaml
# /Documents/StyleTTS2-lite/Configs/config_example.yaml より
symbol:
  pad: "$"
  punctuation: ';:,.!?¡¿—…"«»"" '
  letters: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
  letters_ipa: "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"
```

### 4.2 日本語音素変換（pyopenjtalk → IPA）

| pyopenjtalk | IPA | 説明 |
|-------------|-----|------|
| a | ɑ | 開母音 |
| i | i | 前舌高母音 |
| u | ɯ | 非円唇後舌高母音 |
| e | e | 前舌中母音 |
| o | o | 後舌中母音 |
| k | k | 無声軟口蓋破裂音 |
| g | ɡ | 有声軟口蓋破裂音 |
| s | s | 無声歯茎摩擦音 |
| z | z | 有声歯茎摩擦音 |
| t | t | 無声歯茎破裂音 |
| d | d | 有声歯茎破裂音 |
| n | n | 歯茎鼻音 |
| h | h | 無声声門摩擦音 |
| b | b | 有声両唇破裂音 |
| p | p | 無声両唇破裂音 |
| m | m | 両唇鼻音 |
| y | j | 硬口蓋接近音 |
| r | ɾ | 歯茎はじき音 |
| w | w | 両唇軟口蓋接近音 |
| sh | ʃ | 無声後部歯茎摩擦音 |
| ch | ʧ | 無声後部歯茎破擦音 |
| j | ʤ | 有声後部歯茎破擦音 |
| N | ɴ | 口蓋垂鼻音（撥音） |
| ts | ts | 無声歯茎破擦音 |
| f | ɸ | 無声両唇摩擦音 |
| cl | ʔ | 促音（声門閉鎖） |
| pau | (空白) | ポーズ |

### 4.3 英語音素変換（ARPABET → IPA）

| ARPABET | IPA | 例 |
|---------|-----|-----|
| AA | ɑ | father |
| AE | æ | cat |
| AH | ʌ | cup |
| AO | ɔ | law |
| AW | aʊ | how |
| AY | aɪ | my |
| EH | ɛ | bed |
| ER | ɚ | bird |
| EY | eɪ | say |
| IH | ɪ | bit |
| IY | i | see |
| OW | oʊ | go |
| OY | ɔɪ | boy |
| UH | ʊ | book |
| UW | u | too |
| B | b | boy |
| CH | ʧ | church |
| D | d | dog |
| DH | ð | this |
| F | f | fish |
| G | ɡ | go |
| HH | h | house |
| JH | ʤ | judge |
| K | k | cat |
| L | l | love |
| M | m | man |
| N | n | no |
| NG | ŋ | sing |
| P | p | pen |
| R | ɹ | red |
| S | s | see |
| SH | ʃ | she |
| T | t | top |
| TH | θ | think |
| V | v | voice |
| W | w | we |
| Y | j | yes |
| Z | z | zoo |
| ZH | ʒ | vision |

## 5. 実装構成

```
src/tukuyomi/g2p/
├── __init__.py           # G2PPipeline（統合API）
├── base.py               # PhonemeResult, BaseG2P
├── phoneme_set.py        # 統一Phoneme Set定義
├── normalizer.py         # テキスト正規化
├── lang_detector.py      # 言語判定
├── english/
│   ├── g2p.py            # EnglishG2P
│   ├── cmu_dict.py       # CMU辞書ローダー
│   └── fallback.py       # ルールベースフォールバック
└── japanese/
    ├── g2p.py            # JapaneseG2P
    └── converter.py      # pyopenjtalk出力→IPA変換
```

## 6. 依存パッケージ

```toml
[project]
dependencies = [
    "pyopenjtalk-plus>=0.4.1",  # 日本語G2P
    "nltk>=3.8",                 # CMU辞書アクセス
    "regex>=2024.0.0",           # 高度な正規表現
]
```

## 7. 参考リンク

- [pyopenjtalk-plus (GitHub)](https://github.com/tsukumijima/pyopenjtalk-plus)
- [pyopenjtalk-plus (PyPI)](https://pypi.org/project/pyopenjtalk-plus/)
- [misaki (GitHub)](https://github.com/hexgrad/misaki)
- [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
- [StyleTTS2-lite (GitHub)](https://github.com/dangtr0408/StyleTTS2-lite)
- [ARPABET (Wikipedia)](https://en.wikipedia.org/wiki/ARPABET)
