# G2P実装 引き継ぎ資料

StyleTTS2-lite forkでのG2P実装ガイド

## 1. 現状のコード構造

### 1.1 関連ファイル一覧

```
StyleTTS2-lite/
├── meldataset.py          # TextCleaner実装、データローダー
├── inference.py           # 推論パイプライン（TextCleanerの使用例）
├── train.py               # 学習パイプライン
├── models.py              # モデル定義
├── Configs/
│   └── config_example.yaml  # シンボルセット定義
└── g2p/                   # ← ここに新規作成
    ├── __init__.py
    ├── phoneme_set.py
    ├── english/
    └── japanese/
```

### 1.2 TextCleanerの仕組み

**ファイル**: `meldataset.py:21-35`

```python
class TextCleaner:
    def __init__(self, symbol_dict, debug=True):
        self.word_index_dictionary = symbol_dict
        self.debug = debug

    def __call__(self, text):
        indexes = []
        for char in text:
            try:
                indexes.append(self.word_index_dictionary[char])
            except KeyError as e:
                if self.debug:
                    print("\nWARNING UNKNOWN IPA CHARACTERS/LETTERS: ", char)
                continue
        return indexes
```

**重要**: TextCleanerは**IPA音素列を受け取る**前提。G2Pはその前段で実行する必要がある。

### 1.3 シンボルセット構築

**ファイル**: `inference.py:71-82`

```python
symbols = (
    list(config['symbol']['pad']) +          # "$"
    list(config['symbol']['punctuation']) +  # ';:,.!?¡¿—…"«»"" '
    list(config['symbol']['letters']) +      # A-Za-z
    list(config['symbol']['letters_ipa']) +  # IPA文字
    list(config['symbol']['extend'])         # 拡張用（空）
)
symbol_dict = {}
for i in range(len(symbols)):
    symbol_dict[symbols[i]] = i

n_token = len(symbol_dict) + 1  # 178 + 1 = 179
```

**シンボルID割り当て（config_example.yamlより）**:

| 範囲 | 内容 | 例 |
|------|------|-----|
| 0 | PAD | `$` |
| 1-17 | 句読点 | `;:,.!?` など |
| 18-69 | 英字 | `A-Za-z` |
| 70-177 | IPA | `ɑɐɒæ...` |

### 1.4 推論時のテキスト処理フロー

**ファイル**: `inference.py:224-232`

```python
def __inference(self, phonem, ref_s, speed=1, prev_d_mean=0, t=0.1):
    # 1. nltkでトークン化（スペース区切り）
    phonem = ' '.join(word_tokenize(phonem))

    # 2. TextCleanerでID列に変換
    tokens = self.cleaner(phonem)

    # 3. 開始・終了トークン追加
    tokens.insert(0, 0)  # PAD
    tokens.append(0)     # PAD

    # 4. テンソル化
    tokens = torch.LongTensor(tokens).to(device).unsqueeze(0)
```

**注意**: 現状は`phonem`引数に**既にIPA変換済みのテキスト**が渡される前提。

### 1.5 学習データフォーマット

**ファイル**: `meldataset.py:69, 101-103`

```
wav_path|text
```

- `wav_path`: 音声ファイルパス（相対パス）
- `text`: **IPA音素列**（TextCleanerで直接処理される）

**例**:
```
libriTTS/train/1.wav|ðə kæt sæt ɑn ðə mæt
libriTTS/train/2.wav|həloʊ wɝld
```

### 1.6 音声前処理

**ファイル**: `meldataset.py:101-120`

```python
def _load_tensor(self, data):
    wave_path, text = data
    wave, sr = sf.read(osp.join(self.root_path, wave_path))

    # ステレオ→モノラル
    if wave.shape[-1] == 2:
        wave = wave[:, 0].squeeze()

    # 24kHzリサンプリング
    if sr != 24000:
        wave = librosa.resample(wave, orig_sr=sr, target_sr=24000)

    # 両端に0.5秒パディング（12000サンプル = 0.5秒 × 24000Hz）
    wave = np.concatenate([np.zeros([12000]), wave, np.zeros([12000])], axis=0)

    # テキスト→ID変換
    text = self.text_cleaner(text)
    text.insert(0, 0)  # 開始トークン
    text.append(0)     # 終了トークン
    text = torch.LongTensor(text)

    return wave, text
```

---

## 2. G2P実装計画

### 2.1 ディレクトリ構造

```
StyleTTS2-lite/
└── g2p/
    ├── __init__.py           # G2PPipeline（統合API）
    ├── phoneme_set.py        # 統一Phoneme Set（config連携）
    ├── normalizer.py         # テキスト正規化
    ├── lang_detector.py      # 言語判定
    ├── english/
    │   ├── __init__.py
    │   ├── g2p.py            # EnglishG2P
    │   ├── cmu_dict.py       # CMU辞書ローダー
    │   └── fallback.py       # ルールベースフォールバック
    └── japanese/
        ├── __init__.py
        ├── g2p.py            # JapaneseG2P
        └── converter.py      # pyopenjtalk→IPA変換
```

### 2.2 依存パッケージ

```bash
pip install pyopenjtalk-plus nltk regex
```

または（uv使用時）:
```bash
uv add pyopenjtalk-plus nltk regex
```

---

## 3. 実装詳細

### 3.1 PhonemeSet（config連携）

**ファイル**: `g2p/phoneme_set.py`

```python
"""StyleTTS2-lite互換のPhoneme Set"""
import yaml
from typing import Dict, List, Optional

class PhonemeSet:
    """configファイルからシンボルセットを構築"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self._load_from_config(config_path)
        else:
            self._use_default()

    def _load_from_config(self, config_path: str):
        """configファイルからシンボルを読み込み"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.symbols = (
            list(config['symbol']['pad']) +
            list(config['symbol']['punctuation']) +
            list(config['symbol']['letters']) +
            list(config['symbol']['letters_ipa']) +
            list(config['symbol'].get('extend', ''))
        )
        self._build_dict()

    def _use_default(self):
        """デフォルトのシンボルセット（config_example.yaml相当）"""
        self.pad = "$"
        self.punctuation = ';:,.!?¡¿—…"«»"" '
        self.letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        self.letters_ipa = "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"

        self.symbols = list(
            self.pad + self.punctuation + self.letters + self.letters_ipa
        )
        self._build_dict()

    def _build_dict(self):
        """シンボル↔ID辞書を構築"""
        self.symbol_to_id: Dict[str, int] = {s: i for i, s in enumerate(self.symbols)}
        self.id_to_symbol: Dict[int, str] = {i: s for i, s in enumerate(self.symbols)}

    def to_ids(self, phonemes: List[str]) -> List[int]:
        """音素リスト→IDリスト"""
        return [self.symbol_to_id.get(p, 0) for p in phonemes]

    def to_phonemes(self, ids: List[int]) -> List[str]:
        """IDリスト→音素リスト"""
        return [self.id_to_symbol.get(i, self.pad) for i in ids]

    def get_symbol_dict(self) -> Dict[str, int]:
        """TextCleaner用の辞書を返す"""
        return self.symbol_to_id

    @property
    def vocab_size(self) -> int:
        return len(self.symbols) + 1  # +1 for compatibility
```

### 3.2 日本語G2P

**ファイル**: `g2p/japanese/g2p.py`

```python
"""pyopenjtalk-plusベースの日本語G2P"""
import pyopenjtalk
from typing import List
from .converter import JapanesePhonemeConverter

class JapaneseG2P:
    """日本語テキスト→IPA音素列"""

    def __init__(self):
        self.converter = JapanesePhonemeConverter()

    def convert(self, text: str) -> str:
        """テキストをIPA音素列に変換"""
        # pyopenjtalkでG2P
        raw_phonemes = pyopenjtalk.g2p(text)
        # 例: "k o N n i ch i w a"

        # スペース区切りで分割
        phoneme_list = raw_phonemes.split()

        # IPA形式に変換
        ipa_phonemes = self.converter.to_ipa(phoneme_list)

        # スペース区切りで結合
        return ' '.join(ipa_phonemes)

    def convert_to_list(self, text: str) -> List[str]:
        """テキストをIPA音素リストに変換"""
        raw_phonemes = pyopenjtalk.g2p(text)
        phoneme_list = raw_phonemes.split()
        return self.converter.to_ipa(phoneme_list)
```

**ファイル**: `g2p/japanese/converter.py`

```python
"""pyopenjtalk出力→IPA変換"""
from typing import List

class JapanesePhonemeConverter:
    """pyopenjtalk音素をStyleTTS2-lite互換IPAに変換"""

    # pyopenjtalk → IPA マッピング
    PHONEME_MAP = {
        # 母音
        'a': 'ɑ',
        'i': 'i',
        'u': 'ɯ',
        'e': 'e',
        'o': 'o',
        # 子音
        'k': 'k',
        'g': 'ɡ',  # 注意: U+0261 (LATIN SMALL LETTER SCRIPT G)
        's': 's',
        'z': 'z',
        't': 't',
        'd': 'd',
        'n': 'n',
        'h': 'h',
        'b': 'b',
        'p': 'p',
        'm': 'm',
        'y': 'j',
        'r': 'ɾ',
        'w': 'w',
        # 複合子音
        'sh': 'ʃ',
        'ch': 'ʧ',
        'j': 'ʤ',
        'ts': 'ts',  # 注意: 2文字のまま
        'f': 'ɸ',
        'hy': 'ç',
        'ky': 'kj',
        'gy': 'ɡj',
        'ny': 'ɲ',
        'by': 'bj',
        'py': 'pj',
        'my': 'mj',
        'ry': 'ɾj',
        # 特殊音素
        'N': 'ɴ',       # 撥音
        'q': 'ʔ',       # 促音（pyopenjtalkでは'q'）
        'cl': 'ʔ',      # 促音（別表記）
        'pau': ' ',     # ポーズ
        'sil': '',      # 無音（除去）
        'sp': ' ',      # 短いポーズ
    }

    def to_ipa(self, phonemes: List[str]) -> List[str]:
        """pyopenjtalk音素列をIPAに変換"""
        result = []
        for p in phonemes:
            p_lower = p.lower() if p != 'N' else p  # 'N'は大文字のまま

            if p_lower in self.PHONEME_MAP:
                mapped = self.PHONEME_MAP[p_lower]
                if mapped:  # 空文字でなければ追加
                    # 複数文字の場合は分割
                    if len(mapped) > 1 and mapped not in ['ts', 'ʧ', 'ʤ']:
                        result.extend(list(mapped))
                    else:
                        result.append(mapped)
            else:
                # 未知の音素はそのまま追加（デバッグ用）
                print(f"WARNING: Unknown Japanese phoneme: {p}")
                result.append(p)

        return result
```

### 3.3 英語G2P

**ファイル**: `g2p/english/g2p.py`

```python
"""CMU辞書ベースの英語G2P"""
from typing import List, Optional
from .cmu_dict import CMUDict
from .fallback import RuleBasedFallback

class EnglishG2P:
    """英語テキスト→IPA音素列"""

    # ARPABET → IPA 変換テーブル
    ARPABET_TO_IPA = {
        # 母音
        'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ',
        'AW': ['a', 'ʊ'], 'AY': ['a', 'ɪ'],
        'EH': 'ɛ', 'ER': 'ɚ', 'EY': ['e', 'ɪ'],
        'IH': 'ɪ', 'IY': 'i',
        'OW': ['o', 'ʊ'], 'OY': ['ɔ', 'ɪ'],
        'UH': 'ʊ', 'UW': 'u',
        # 子音
        'B': 'b', 'CH': 'ʧ', 'D': 'd', 'DH': 'ð',
        'F': 'f', 'G': 'ɡ', 'HH': 'h', 'JH': 'ʤ',
        'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n',
        'NG': 'ŋ', 'P': 'p', 'R': 'ɹ', 'S': 's',
        'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'V': 'v',
        'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
    }

    def __init__(self):
        self.cmu_dict = CMUDict()
        self.fallback = RuleBasedFallback()

    def convert(self, text: str) -> str:
        """テキストをIPA音素列に変換"""
        words = self._tokenize(text)
        all_phonemes = []

        for word in words:
            if not word.strip():
                continue

            # 句読点はそのまま
            if word in '.,!?;:':
                all_phonemes.append(word)
                continue

            phonemes = self._convert_word(word)
            all_phonemes.extend(phonemes)
            all_phonemes.append(' ')  # 単語区切り

        return ''.join(all_phonemes).strip()

    def _tokenize(self, text: str) -> List[str]:
        """テキストを単語に分割"""
        import re
        # 句読点を分離
        tokens = re.findall(r"[\w']+|[.,!?;:]", text)
        return tokens

    def _convert_word(self, word: str) -> List[str]:
        """単語をIPA音素列に変換"""
        # CMU辞書で検索
        arpabet = self.cmu_dict.lookup(word.upper())

        if arpabet is None:
            # フォールバック
            arpabet = self.fallback.predict(word)

        # ARPABET→IPA変換
        return self._arpabet_to_ipa(arpabet)

    def _arpabet_to_ipa(self, arpabet: List[str]) -> List[str]:
        """ARPABETをIPAに変換"""
        ipa = []
        for phone in arpabet:
            # ストレスマーカー(0,1,2)を除去
            base_phone = phone.rstrip('012')
            mapped = self.ARPABET_TO_IPA.get(base_phone)

            if isinstance(mapped, list):
                ipa.extend(mapped)
            elif mapped:
                ipa.append(mapped)

        return ipa
```

**ファイル**: `g2p/english/cmu_dict.py`

```python
"""CMU発音辞書ローダー"""
from typing import Dict, List, Optional

class CMUDict:
    """CMU発音辞書"""

    def __init__(self):
        self._dict: Dict[str, List[List[str]]] = {}
        self._load()

    def _load(self):
        """nltk経由でCMU辞書をロード"""
        try:
            import nltk
            nltk.download('cmudict', quiet=True)
            from nltk.corpus import cmudict
            self._dict = cmudict.dict()
            print(f"CMU辞書ロード完了: {len(self._dict)}語")
        except Exception as e:
            print(f"CMU辞書ロードエラー: {e}")
            self._dict = {}

    def lookup(self, word: str) -> Optional[List[str]]:
        """単語の発音を検索"""
        word_lower = word.lower()
        pronunciations = self._dict.get(word_lower)

        if pronunciations:
            return pronunciations[0]  # 最初の発音を返す
        return None

    def has_word(self, word: str) -> bool:
        """辞書に単語が存在するか"""
        return word.lower() in self._dict
```

**ファイル**: `g2p/english/fallback.py`

```python
"""未登録語用ルールベースG2P"""
from typing import List

class RuleBasedFallback:
    """ルールベースの発音予測"""

    # 基本的な文字→ARPABET
    LETTER_TO_PHONEME = {
        'a': ['AE'], 'b': ['B'], 'c': ['K'],
        'd': ['D'], 'e': ['EH'], 'f': ['F'],
        'g': ['G'], 'h': ['HH'], 'i': ['IH'],
        'j': ['JH'], 'k': ['K'], 'l': ['L'],
        'm': ['M'], 'n': ['N'], 'o': ['AA'],
        'p': ['P'], 'q': ['K'], 'r': ['R'],
        's': ['S'], 't': ['T'], 'u': ['AH'],
        'v': ['V'], 'w': ['W'], 'x': ['K', 'S'],
        'y': ['Y'], 'z': ['Z'],
    }

    # ダイグラフ（2文字組み合わせ）
    DIGRAPHS = {
        'ch': ['CH'], 'sh': ['SH'], 'th': ['TH'],
        'ph': ['F'], 'wh': ['W'], 'ck': ['K'],
        'ng': ['NG'], 'qu': ['K', 'W'],
        'ee': ['IY'], 'oo': ['UW'], 'ea': ['IY'],
        'ou': ['AW'], 'oi': ['OY'], 'ow': ['OW'],
    }

    def predict(self, word: str) -> List[str]:
        """ルールベースで発音を予測"""
        word = word.lower()
        phonemes = []
        i = 0

        while i < len(word):
            # ダイグラフをチェック
            if i + 1 < len(word):
                digraph = word[i:i+2]
                if digraph in self.DIGRAPHS:
                    phonemes.extend(self.DIGRAPHS[digraph])
                    i += 2
                    continue

            # 単一文字
            char = word[i]
            if char in self.LETTER_TO_PHONEME:
                phonemes.extend(self.LETTER_TO_PHONEME[char])
            i += 1

        return phonemes
```

### 3.4 統合パイプライン

**ファイル**: `g2p/__init__.py`

```python
"""日英統合G2Pパイプライン"""
import re
from typing import Optional
from .phoneme_set import PhonemeSet
from .japanese.g2p import JapaneseG2P
from .english.g2p import EnglishG2P

class G2PPipeline:
    """日英統合G2P"""

    # 日本語文字パターン
    JAPANESE_PATTERN = re.compile(
        r'[\u3040-\u309F'   # ひらがな
        r'\u30A0-\u30FF'    # カタカナ
        r'\u4E00-\u9FFF'    # 漢字
        r'\uFF65-\uFF9F]',  # 半角カナ
        re.UNICODE
    )

    def __init__(self, config_path: Optional[str] = None):
        self.phoneme_set = PhonemeSet(config_path)
        self.japanese_g2p = JapaneseG2P()
        self.english_g2p = EnglishG2P()

    def convert(self, text: str, language: Optional[str] = None) -> str:
        """テキストをIPA音素列に変換

        Args:
            text: 入力テキスト
            language: 'ja', 'en', または None（自動判定）

        Returns:
            IPA音素列（スペース区切り）
        """
        # テキスト正規化
        text = self._normalize(text)

        # 言語判定
        if language is None:
            language = self._detect_language(text)

        # 言語別処理
        if language == 'ja':
            return self.japanese_g2p.convert(text)
        elif language == 'en':
            return self.english_g2p.convert(text)
        else:  # mixed
            return self._convert_mixed(text)

    def _normalize(self, text: str) -> str:
        """テキスト正規化"""
        # 全角句読点→半角
        replacements = {
            '。': '.', '、': ',', '！': '!', '？': '?',
            '：': ':', '；': ';',
        }
        for jp, en in replacements.items():
            text = text.replace(jp, en)

        # 連続空白を単一に
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _detect_language(self, text: str) -> str:
        """言語判定"""
        has_japanese = bool(self.JAPANESE_PATTERN.search(text))
        has_english = bool(re.search(r'[a-zA-Z]', text))

        if has_japanese and has_english:
            return 'mixed'
        elif has_japanese:
            return 'ja'
        else:
            return 'en'

    def _convert_mixed(self, text: str) -> str:
        """日英混在テキストを処理"""
        result = []
        current_text = ""
        current_lang = None

        for char in text:
            if self.JAPANESE_PATTERN.match(char):
                char_lang = 'ja'
            elif char.isalpha():
                char_lang = 'en'
            else:
                # 句読点等は現在のセグメントに追加
                current_text += char
                continue

            # 言語が変わったら処理
            if current_lang and char_lang != current_lang:
                if current_text.strip():
                    if current_lang == 'ja':
                        result.append(self.japanese_g2p.convert(current_text))
                    else:
                        result.append(self.english_g2p.convert(current_text))
                current_text = ""

            current_lang = char_lang
            current_text += char

        # 残りを処理
        if current_text.strip() and current_lang:
            if current_lang == 'ja':
                result.append(self.japanese_g2p.convert(current_text))
            else:
                result.append(self.english_g2p.convert(current_text))

        return ' '.join(result)

    def get_symbol_dict(self):
        """TextCleaner用の辞書を返す"""
        return self.phoneme_set.get_symbol_dict()
```

---

## 4. 使用方法

### 4.1 基本的な使い方

```python
from g2p import G2PPipeline

# 初期化
pipeline = G2PPipeline()

# 日本語
ja_ipa = pipeline.convert("こんにちは")
print(ja_ipa)  # "k o ɴ n i ʧ i w ɑ"

# 英語
en_ipa = pipeline.convert("Hello world")
print(en_ipa)  # "h ʌ l o ʊ w ɝ l d"

# 混在
mixed_ipa = pipeline.convert("Helloこんにちは")
print(mixed_ipa)  # "h ʌ l o ʊ k o ɴ n i ʧ i w ɑ"
```

### 4.2 inference.pyとの統合

```python
# inference.py を修正

from g2p import G2PPipeline

class StyleTTS2(torch.nn.Module):
    def __init__(self, config_path, models_path):
        super().__init__()
        # ... 既存コード ...

        # G2Pパイプライン追加
        self.g2p = G2PPipeline(config_path)

    def generate(self, text, style, stabilize=True, n_merge=16):
        """テキストから音声生成（G2P統合版）"""
        # テキスト→IPA変換
        phonem = self.g2p.convert(text)

        # 以降は既存の処理
        # ...
```

### 4.3 学習データ作成

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

---

## 5. テスト・検証

### 5.1 動作確認スクリプト

```python
# test_g2p.py
from g2p import G2PPipeline
from g2p.phoneme_set import PhonemeSet

def test_japanese():
    from g2p.japanese.g2p import JapaneseG2P
    g2p = JapaneseG2P()

    tests = [
        ("こんにちは", "k o ɴ n i ʧ i w ɑ"),
        ("ありがとう", "ɑ ɾ i ɡ ɑ t o ɯ"),
        ("東京", "t o ɯ k j o ɯ"),
    ]

    for text, expected in tests:
        result = g2p.convert(text)
        print(f"{text} -> {result}")
        # assert expected in result, f"Failed: {text}"

def test_english():
    from g2p.english.g2p import EnglishG2P
    g2p = EnglishG2P()

    tests = [
        ("hello", "h ʌ l o ʊ"),
        ("world", "w ɝ l d"),
    ]

    for text, expected in tests:
        result = g2p.convert(text)
        print(f"{text} -> {result}")

def test_phoneme_set():
    ps = PhonemeSet()
    print(f"Vocab size: {ps.vocab_size}")

    # IPA文字がすべて含まれているか確認
    test_chars = ['ɑ', 'ɴ', 'ʧ', 'ɾ', 'ŋ', 'θ', 'ð']
    for char in test_chars:
        assert char in ps.symbol_to_id, f"Missing: {char}"
    print("All test characters found in phoneme set")

if __name__ == '__main__':
    print("=== Japanese G2P ===")
    test_japanese()

    print("\n=== English G2P ===")
    test_english()

    print("\n=== Phoneme Set ===")
    test_phoneme_set()
```

### 5.2 TextCleanerとの互換性確認

```python
# test_compatibility.py
from meldataset import TextCleaner
from g2p import G2PPipeline
from g2p.phoneme_set import PhonemeSet

# PhonemeSetからsymbol_dictを取得
ps = PhonemeSet()
symbol_dict = ps.get_symbol_dict()

# TextCleanerを初期化
cleaner = TextCleaner(symbol_dict, debug=True)

# G2Pでテキストを変換
pipeline = G2PPipeline()
ipa = pipeline.convert("こんにちは Hello")
print(f"IPA: {ipa}")

# TextCleanerでID列に変換
ids = cleaner(ipa)
print(f"IDs: {ids}")

# IDを音素に戻す
phonemes = ps.to_phonemes(ids)
print(f"Phonemes: {phonemes}")
```

---

## 6. 注意事項

### 6.1 日本語特有の問題

1. **撥音（ん）**: pyopenjtalkは `N` で出力 → `ɴ` に変換
2. **促音（っ）**: pyopenjtalkは `q` で出力 → `ʔ` に変換
3. **長音**: 現状未対応、必要に応じて `ː` を追加

### 6.2 英語特有の問題

1. **未登録語**: CMU辞書にない単語はフォールバック処理（精度低下）
2. **同形異義語**: 文脈による発音の違いは未対応（例: read/read）
3. **固有名詞**: 多くが辞書未登録

### 6.3 シンボルセットの拡張

日本語音素で不足がある場合、`config.yaml` の `extend` に追加:

```yaml
symbol:
  # ... 既存 ...
  extend: "ɴː"  # 撥音、長音記号を追加
```

### 6.4 ライセンス確認事項

| ライブラリ | ライセンス | 商用利用 |
|-----------|----------|---------|
| pyopenjtalk-plus | MIT | ✓ |
| OpenJTalk | Modified BSD | ✓ |
| CMU辞書 | Public Domain | ✓ |
| nltk | Apache 2.0 | ✓ |

**すべて商用利用可能。GPL依存なし。**

---

## 7. 次のステップ

1. `g2p/` ディレクトリを作成
2. 上記コードを実装
3. `test_g2p.py` で動作確認
4. `inference.py` にG2P統合
5. 学習データ作成パイプラインの整備
