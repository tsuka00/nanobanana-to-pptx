# 設計JSONスキーマ

Designer Agent が生成する設計JSONの仕様です。

## 概要

ユーザーの自然言語指示は Gemini 2.0 Flash によって以下の構造化JSONに変換されます。

同じ設計JSONから PNG、SVG、PPTX の3形式が生成されます：

| 出力形式 | 用途 | 編集 |
|----------|------|------|
| PNG | 最終合成画像（プレビュー用） | 不可 |
| SVG | 編集可能なベクター形式 | Illustratorで編集可能 |
| PPTX | PowerPointプレゼンテーション | テキスト編集可能 |

## プリセットシステム

v2.0から、**プリセットシステム**が導入されました。座標や色を細かく指定する代わりに、プリセット名を指定することで一貫性のあるデザインを簡単に生成できます。

### プリセットの利点

- **簡潔な指定**: 座標や色を省略しても適切な値が自動設定される
- **一貫性**: トーンに合ったレイアウト・配色の組み合わせが保証される
- **LLMの負担軽減**: AIが細かい数値を考える必要がなくなる
- **カスタマイズ可能**: 明示的に指定した値はプリセットより優先される

## スキーマ構造

```json
{
  "preset": {
    "layout": "string",
    "palette": "string",
    "tone": "string"
  },
  "background": {
    "prompt": "string"
  },
  "illustration": {
    "type": "string",
    "points": [[number, number], ...],
    "x": number,
    "y": number,
    "width": number,
    "height": number,
    "fill": {
      "type": "string",
      "color": "string",
      "start": "string",
      "end": "string",
      "direction": "string"
    },
    "opacity": number
  },
  "title": {
    "text": "string",
    "x": number,
    "y": number,
    "fontSize": number,
    "fontFamily": "string",
    "fontWeight": "string",
    "style": "string",
    "color": "string",
    "glowColor": "string",
    "fill": {
      "type": "string",
      "start": "string",
      "end": "string",
      "direction": "string"
    }
  },
  "subtitle": {
    "text": "string",
    "x": number,
    "y": number,
    "fontSize": number,
    "fontFamily": "string",
    "fontWeight": "string",
    "style": "string",
    "color": "string",
    "glowColor": "string",
    "fill": {
      "type": "string",
      "start": "string",
      "end": "string",
      "direction": "string"
    }
  }
}
```

## 各要素の詳細

### preset（プリセット）

プリセットセクションでは、デザインの基本方針を指定します。**すべてのプロパティは省略可能**です。

| プロパティ | 型 | デフォルト | 説明 |
|------------|-----|------------|------|
| layout | string | "center" | レイアウトプリセット名 |
| palette | string | "light" | 配色パレット名 |
| tone | string | null | トーンプリセット名 |

#### レイアウトプリセット（layout）

| 値 | タイトル位置 | サブタイトル位置 | 説明 |
|----|-------------|------------------|------|
| center | (960, 400) | (960, 520) | 中央配置（デフォルト） |
| center-middle | (960, 480) | (960, 600) | 中央・垂直中央（インパクト重視） |
| left | (200, 400) | (200, 520) | 左寄せ（右に余白） |
| right | (1720, 400) | (1720, 520) | 右寄せ（左に余白） |
| bottom | (960, 800) | (960, 920) | 下部配置（背景重視） |
| top | (960, 200) | (960, 320) | 上部配置 |
| split-left | (480, 450) | (480, 580) | 左半分にテキスト（50:50分割） |
| split-right | (1440, 450) | (1440, 580) | 右半分にテキスト（50:50分割） |
| bottom-left | (200, 800) | (200, 920) | 左下配置 |
| bottom-right | (1720, 800) | (1720, 920) | 右下配置 |
| overlay | (960, 480) | (960, 620) | オーバーレイ（背景画像の上） |

#### 配色パレット（palette）

| 値 | 背景色 | テキスト色 | アクセント色 | 用途 |
|----|--------|-----------|-------------|------|
| light | #ffffff | #1a1a1a | #2196F3 | 明るい、ビジネス |
| light-warm | #faf8f5 | #3d3d3d | #ff9800 | 温かみ |
| light-cool | #f5f9fc | #1a3a5c | #00bcd4 | クール |
| dark | #1a1a1a | #ffffff | #00bcd4 | モダン |
| dark-tech | #0a0a0a | #ffffff | #00ffff | テック、サイバー |
| dark-purple | #1a0a2e | #ffffff | #e040fb | クリエイティブ |
| monochrome | #f5f5f5 | #000000 | #000000 | ミニマル |
| monochrome-dark | #121212 | #ffffff | #ffffff | ダークミニマル |
| premium-gold | #1a1a1a | #ffffff | #ffd700 | 高級感・ゴールド |
| premium-silver | #1a1a2e | #ffffff | #e8e8e8 | 高級感・シルバー |
| vibrant | #ffffff | #1a1a1a | #ff4081 | エネルギッシュ |
| vibrant-gradient | #667eea | #ffffff | #f093fb | グラデーション背景 |
| nature | #f5f5dc | #2e4a2e | #4caf50 | 自然・エコ |
| ocean | #e3f2fd | #0d47a1 | #00bcd4 | 海・青系 |
| corporate | #f8f9fa | #212529 | #0056b3 | 企業向け |
| corporate-dark | #1e2a3a | #ffffff | #3182ce | 企業向けダーク |

#### トーンプリセット（tone）

| 値 | 説明 | 推奨レイアウト | 推奨パレット |
|----|------|---------------|-------------|
| professional | ビジネス、信頼感 | center, left | corporate, light |
| creative | アーティスティック | left, right | vibrant, dark-purple |
| tech | 未来的、先進的 | center, split-left | dark-tech, dark |
| premium | 高級、ラグジュアリー | center, center-middle | premium-gold, premium-silver |
| minimal | シンプル、余白重視 | center, center-middle | monochrome, light |
| energetic | 活発、ダイナミック | left, right | vibrant, vibrant-gradient |
| warm | 温かみ、親しみ | center, left | light-warm, nature |
| cool | クール、知的 | center, split-left | light-cool, ocean |
| nature | 自然、オーガニック | center, bottom | nature, ocean |
| playful | 遊び心、楽しさ | left, bottom-left | vibrant, light-warm |

**例（プリセット使用）**:

```json
{
  "preset": {
    "tone": "tech",
    "layout": "center",
    "palette": "dark-tech"
  },
  "title": {
    "text": "AI革命",
    "fontSize": 100,
    "style": "3d-metallic"
  },
  "subtitle": {
    "text": "未来を創る技術"
  }
}
```

この例では、タイトルとサブタイトルの座標（x, y）と色（color）は省略されています。プリセット解決後、以下の値が自動設定されます：
- タイトル座標: (960, 400) ← `center` レイアウトから
- サブタイトル座標: (960, 520) ← `center` レイアウトから
- タイトル色: #ffffff ← `dark-tech` パレットの text_primary
- サブタイトル色: #888888 ← `dark-tech` パレットの text_secondary

---

### background（背景）

| プロパティ | 型 | 必須 | 説明 |
|------------|-----|------|------|
| prompt | string | 任意 | 背景画像生成プロンプト（省略時はパレットのヒントを使用） |

**プリセットとの連携**: `prompt` を省略すると、選択したパレットに応じた背景が自動生成されます。

| パレット | 自動生成される背景のヒント |
|----------|---------------------------|
| dark-tech | "dark futuristic background, subtle grid or particles, tech atmosphere" |
| premium-gold | "elegant dark background with subtle gold accents, luxury" |
| nature | "natural, organic background, soft green tones, earthy" |
| ... | パレットごとに最適化されたヒント |

**例（明示的に指定）**:

```json
{
  "background": {
    "prompt": "青空、白い雲、晴れた夏の日の空"
  }
}
```

**例（プリセットから自動生成）**:

```json
{
  "preset": { "palette": "dark-tech" },
  "background": {}
}
```
→ "dark futuristic background, subtle grid or particles, tech atmosphere, cyber aesthetic" が自動設定される

---

### illustration（イラスト/シェイプ）

幾何学シェイプを定義します。Pillow で描画されます。

| プロパティ | 型 | 必須 | 説明 |
|------------|-----|------|------|
| type | string | 必須 | シェイプタイプ |
| points | array | 条件付き | 頂点座標（polygon, triangle） |
| x | number | 条件付き | X座標（rectangle, ellipse） |
| y | number | 条件付き | Y座標（rectangle, ellipse） |
| width | number | 条件付き | 幅（rectangle, ellipse） |
| height | number | 条件付き | 高さ（rectangle, ellipse） |
| fill | object | 必須 | 塗りつぶし設定 |
| opacity | number | 任意 | 不透明度（0.0〜1.0、デフォルト: 1.0） |

**シェイプタイプ（type）**:

| 値 | 説明 | 必須パラメータ |
|----|------|----------------|
| polygon | 多角形 | points |
| rectangle | 矩形 | x, y, width, height |
| ellipse | 楕円 | x, y, width, height |
| triangle | 三角形 | points（3点） |

**塗りつぶし設定（fill）**:

| プロパティ | 型 | 説明 |
|------------|-----|------|
| type | string | "solid"（単色）または "gradient"（グラデーション） |
| color | string | 単色の場合の色（#RRGGBB形式） |
| start | string | グラデーション開始色（#RRGGBB形式） |
| end | string | グラデーション終了色（#RRGGBB形式） |
| direction | string | グラデーション方向（vertical, horizontal, diagonal） |

**グラデーション方向**:

| 値 | 説明 |
|----|------|
| vertical | 縦方向（上から下） |
| horizontal | 横方向（左から右） |
| diagonal | 斜め方向（左上から右下） |

**例（グラデーション四角形）**:

```json
{
  "illustration": {
    "type": "polygon",
    "points": [[0, 400], [0, 1080], [800, 1080], [400, 400]],
    "fill": {
      "type": "gradient",
      "start": "#4CAF50",
      "end": "#81C784",
      "direction": "diagonal"
    },
    "opacity": 1.0
  }
}
```

**例（単色矩形）**:

```json
{
  "illustration": {
    "type": "rectangle",
    "x": 100,
    "y": 100,
    "width": 400,
    "height": 300,
    "fill": {
      "type": "solid",
      "color": "#2196F3"
    },
    "opacity": 0.8
  }
}
```

---

### title（タイトル）

| プロパティ | 型 | 必須 | デフォルト | 説明 |
|------------|-----|------|------------|------|
| text | string | 必須 | - | タイトルテキスト |
| x | number | 任意 | レイアウトから | X座標（テキスト中心） |
| y | number | 任意 | レイアウトから | Y座標（テキスト中心） |
| fontSize | number | 任意 | 64 | フォントサイズ |
| fontFamily | string | 任意 | "Hiragino Sans" | フォントファミリー |
| fontWeight | string | 任意 | トーンから | フォントの太さ |
| style | string | 任意 | パレットから | スタイルプリセット |
| color | string | 任意 | パレットから | 文字色（flat/outline/emboss用） |
| glowColor | string | 任意 | null | グロー色（neon-glow用） |
| fill | object | 任意 | null | グラデーション設定 |

**プリセットとの連携**:
- `x`, `y` 省略時: 選択したレイアウトの `title_x`, `title_y` が使用される
- `color` 省略時: 選択したパレットの `text_primary` が使用される
- `style` 省略時: 選択したパレットの推奨スタイル（最初のもの）が使用される
- `fontWeight` 省略時: 選択したトーンの `font_weight_title` が使用される

**スタイルプリセット（style）**:

| 値 | 説明 | 推奨用途 |
|----|------|----------|
| flat | シンプルな単色 | ビジネス、フォーマル |
| shadow | ドロップシャドウ | 可読性重視 |
| 3d-metallic | 3D/メタリック/ホログラム | 立体感、光沢、虹色反射 |
| neon-glow | ネオン発光 | テクノロジー、エンタメ |
| glass | ガラス風透明感 | 洗練、クリーン |
| outline | アウトライン | カジュアル、ポップ |
| gold | ゴールドメタリック | 高級感、祝い事 |
| silver | シルバーメタリック | クール、先進的 |
| emboss | エンボス/浮き彫り | 伝統的、重厚感 |
| gradient | 2色グラデーション | 単純な色変化 |

**フォントファミリー（fontFamily）**:

| 値 | 説明 |
|----|------|
| Hiragino Sans | モダン、クリーン（デフォルト） |
| Hiragino Mincho | フォーマル、伝統的 |
| Hiragino Maru Gothic | 親しみやすい、カジュアル |
| Helvetica Neue | 欧文、モダン |
| Arial | 欧文、汎用 |

**フォントの太さ（fontWeight）**:

| 値 | 説明 |
|----|------|
| bold | 太字（強調） |
| normal | 通常 |
| light | 細字（繊細、エレガント） |

**例（シンプル）**:

```json
{
  "title": {
    "text": "Hello World",
    "x": 960,
    "y": 400,
    "fontSize": 72,
    "style": "flat",
    "color": "#ffffff"
  }
}
```

**例（3Dメタリック + グラデーション）**:

```json
{
  "title": {
    "text": "CADC",
    "x": 960,
    "y": 400,
    "fontSize": 200,
    "fontFamily": "Helvetica Neue",
    "fontWeight": "bold",
    "style": "3d-metallic",
    "fill": {
      "type": "gradient",
      "start": "#00FF00",
      "end": "#00FFFF",
      "direction": "diagonal"
    }
  }
}
```

**例（ネオングロー）**:

```json
{
  "title": {
    "text": "NEON",
    "x": 960,
    "y": 400,
    "fontSize": 120,
    "style": "neon-glow",
    "color": "#00FFFF",
    "glowColor": "#00FFFF"
  }
}
```

---

### subtitle（サブタイトル）

| プロパティ | 型 | 必須 | デフォルト | 説明 |
|------------|-----|------|------------|------|
| text | string | 必須 | - | サブタイトルテキスト |
| x | number | 任意 | レイアウトから | X座標（テキスト中心） |
| y | number | 任意 | レイアウトから | Y座標（テキスト中心） |
| fontSize | number | 任意 | 36 | フォントサイズ |
| fontFamily | string | 任意 | "Hiragino Sans" | フォントファミリー |
| fontWeight | string | 任意 | トーンから | フォントの太さ |
| style | string | 任意 | "flat" | スタイルプリセット |
| color | string | 任意 | パレットから | 文字色 |
| glowColor | string | 任意 | null | グロー色（neon-glow用） |
| fill | object | 任意 | null | グラデーション設定 |

**プリセットとの連携**:
- `x`, `y` 省略時: 選択したレイアウトの `subtitle_x`, `subtitle_y` が使用される
- `color` 省略時: 選択したパレットの `text_secondary` が使用される
- `fontWeight` 省略時: 選択したトーンの `font_weight_subtitle` が使用される

**例**:

```json
{
  "subtitle": {
    "text": "Welcome to the presentation",
    "x": 960,
    "y": 500,
    "fontSize": 36,
    "style": "flat",
    "color": "#cccccc"
  }
}
```

**例（複数行）**:

```json
{
  "subtitle": {
    "text": "CyberAgent Developer Conference 2024\n10.29 Tue - 10.30 Wed",
    "x": 960,
    "y": 650,
    "fontSize": 40,
    "style": "flat",
    "color": "#FFFFFF"
  }
}
```

---

## 座標仕様

キャンバスサイズは 1920x1080 ピクセル（16:9）です。

### 座標系

- 原点 (0, 0): 左上
- X軸: 右方向に増加（0〜1920）
- Y軸: 下方向に増加（0〜1080）

### テキスト座標

タイトルとサブタイトルの座標はテキストの**中心位置**を指定します。

```
例: x=960, y=400 の場合

              960
               |
    ┌──────────┼──────────┐
    │          │          │
400 ├──────[テキスト中心]──┤
    │                     │
    └─────────────────────┘
```

### イラスト座標

多角形の頂点座標は**絶対座標**で指定します。

```
例: points=[[0, 400], [0, 1080], [600, 1080], [300, 400]]

    0        300       600
    |         |         |
    ┌─────────┬─────────┐
    │         │         │
400 ├─────────●─────────┤
    │        ╱╲         │
    │       ╱  ╲        │
    │      ╱    ╲       │
    │     ╱      ╲      │
1080├────●────────●─────┤
    └─────────────────────┘
```

---

## 座標ガイド

### よく使う座標

| 位置 | X | Y |
|------|-----|-----|
| 中央 | 960 | 540 |
| 左上 | 200 | 200 |
| 右上 | 1720 | 200 |
| 左下 | 200 | 880 |
| 右下 | 1720 | 880 |

### タイトル配置

| 配置 | X | Y |
|------|-----|-----|
| 中央上部 | 960 | 300〜400 |
| 左寄せ | 200〜400 | 400 |
| 右寄せ | 1520〜1720 | 400 |

### フォントサイズの目安

| 用途 | サイズ |
|------|--------|
| メインタイトル | 64〜200 |
| サブタイトル | 36〜48 |
| キャプション | 24〜32 |

---

## 色指定

色は16進数カラーコード（#RRGGBB形式）で指定します。

### 推奨カラーパレット

**暗い背景用（白系テキスト）**:

| 色 | コード |
|----|--------|
| 白 | #ffffff |
| ライトグレー | #f5f5f5 |
| オフホワイト | #fafafa |

**明るい背景用（暗系テキスト）**:

| 色 | コード |
|----|--------|
| 黒 | #000000 |
| ダークグレー | #333333 |
| チャコール | #424242 |

**アクセントカラー**:

| 色 | コード |
|----|--------|
| 緑 | #4CAF50 |
| 青 | #2196F3 |
| オレンジ | #FF9800 |
| 赤 | #F44336 |
| 紫 | #9C27B0 |

---

## 完全な例

```json
{
  "background": {
    "prompt": "抽象的なグラデーション背景、青から紫へのグラデーション、モダンでミニマル"
  },
  "illustration": {
    "type": "polygon",
    "points": [[0, 300], [0, 1080], [700, 1080], [350, 300]],
    "fill": {
      "type": "gradient",
      "start": "#00BCD4",
      "end": "#4DD0E1",
      "direction": "diagonal"
    },
    "opacity": 0.9
  },
  "title": {
    "text": "プレゼンテーション",
    "x": 1200,
    "y": 450,
    "fontSize": 72,
    "fontFamily": "Hiragino Sans",
    "fontWeight": "bold",
    "style": "3d-metallic",
    "fill": {
      "type": "gradient",
      "start": "#FFD700",
      "end": "#FFA500",
      "direction": "vertical"
    }
  },
  "subtitle": {
    "text": "2025年度 年次報告",
    "x": 1200,
    "y": 550,
    "fontSize": 36,
    "style": "flat",
    "color": "#e0e0e0"
  }
}
```

この設計JSONは以下のスライドを生成します：
- 青〜紫のグラデーション背景
- 左下に斜めの水色シェイプ
- 右側に3Dメタリックスタイルのタイトル（ゴールドグラデーション）
- タイトル下にライトグレーのサブタイトル

---

## null値の扱い

要素が不要な場合は `null` を指定します：

```json
{
  "background": {
    "prompt": "シンプルな白背景"
  },
  "illustration": null,
  "title": {
    "text": "タイトルのみ",
    "x": 960,
    "y": 540,
    "fontSize": 80,
    "style": "flat",
    "color": "#333333"
  },
  "subtitle": null
}
```

この場合、イラストとサブタイトルは生成されません。

---

## 出力形式別の注意事項

### SVG出力

- フォントは `Hiragino Sans` を使用（Illustrator互換）
- 背景画像はそのままSVG内に埋め込み（品質劣化なし）
- テキストスタイルプリセットが完全に適用される
- 各要素はレイヤーとして分離（`id` 属性で識別）

### PPTX出力

- テキストはネイティブテキストボックスとして配置（**編集可能**）
- スタイルプリセットは適用されない（シンプルなテキスト）
- 色・フォントサイズ・フォントファミリーは反映される
- 背景・イラストは画像として配置

### PNG出力

- すべての要素がラスタライズされる
- スタイルプリセットはPillow描画では反映されない（単色のみ）
- 最終的な見た目の確認用
