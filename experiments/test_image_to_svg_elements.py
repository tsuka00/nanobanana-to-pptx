"""
検証: 1回のAPI呼び出しで画像から全要素をSVGに変換
"""

import os
import sys
import json
import base64
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env.local')

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL = "gemini-3-pro-preview"

PROMPT = """この画像を分析し、各要素を個別のSVGとして再現してください。

## 検出すべき要素
1. テキスト要素（タイトル、サブタイトル、ラベルなど）
2. イラスト要素（シルエット、アイコンなど）
3. 背景は除外

## 出力形式（JSON）
```json
{
  "elements": [
    {
      "id": "element_1",
      "type": "text",
      "label": "要素の説明",
      "content": "テキスト内容（テキストの場合）",
      "bbox": {"x": 0, "y": 0, "width": 100, "height": 50},
      "svg": "<svg>...</svg>"
    }
  ]
}
```

## SVG生成のルール
- 各SVGのviewBoxは要素のサイズに合わせる
- テキストは元の見た目を忠実に再現（グラデーション、縁取り、影など）
- 背景は透明にする

JSONのみを出力してください。"""


def main():
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    image_path = Path(__file__).parent.parent / "output_parse_image" / "IZ99-8459.png"
    image = Image.open(image_path)

    print(f"画像: {image_path}")
    print(f"サイズ: {image.size}")
    print(f"\nAPI呼び出し中...")

    response = client.models.generate_content(
        model=MODEL,
        contents=[PROMPT, image]
    )

    print(f"\n=== レスポンス ===\n")

    # デバッグ: レスポンス構造を確認
    print(f"candidates: {len(response.candidates) if response.candidates else 0}")
    if response.candidates:
        for i, c in enumerate(response.candidates):
            print(f"  candidate[{i}]: parts={len(c.content.parts) if c.content else 0}")
            if c.content:
                for j, p in enumerate(c.content.parts):
                    print(f"    part[{j}]: text={bool(p.text)}, inline_data={bool(p.inline_data) if hasattr(p, 'inline_data') else False}")

    text = response.text if response.text else ""
    if text:
        print(text[:3000])
        with open(OUTPUT_DIR / "response.txt", "w") as f:
            f.write(text)
        print(f"\n保存: {OUTPUT_DIR / 'response.txt'}")
    else:
        print("テキストレスポンスなし")


if __name__ == "__main__":
    main()
