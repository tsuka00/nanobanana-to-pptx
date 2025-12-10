"""
検証: セグメンテーション → SVG変換
nanobanana画像から要素を切り出し、SVGに変換できるか検証
"""

import os
import sys
import json
import base64
from pathlib import Path
from io import BytesIO

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import numpy as np

# .env.local を読み込み
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env.local')

# 出力ディレクトリ
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# モデル
SEGMENTATION_MODEL = "gemini-3-pro-preview"  # セグメンテーション用
SVG_MODEL = "gemini-3-pro-preview"  # SVG生成用


def get_client():
    """Google GenAI クライアントを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


def load_image(image_path: str) -> tuple[Image.Image, str]:
    """画像を読み込んでPILイメージとBase64を返す"""
    with open(image_path, "rb") as f:
        image_data = f.read()

    image = Image.open(BytesIO(image_data))
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    return image, image_base64


def segment_image(client, image: Image.Image) -> list[dict]:
    """
    Gemini 2.5でセグメンテーションを実行

    Returns:
        list: セグメント情報のリスト
        [
            {
                "box_2d": [y0, x0, y1, x1],  # 0-1000正規化座標
                "mask": "base64エンコードPNG",
                "label": "ラベル"
            }
        ]
    """
    prompt = """この画像の全ての要素をセグメンテーションしてください。

特に以下の要素を検出してください：
- テキスト要素（タイトル、サブタイトル、ラベルなど）
- イラスト要素（キャラクター、シルエット、アイコンなど）
- 背景要素

Output a JSON list of segmentation masks where each entry contains:
- "box_2d": the 2D bounding box as [y0, x0, y1, x1] with coordinates normalized 0-1000
- "mask": the segmentation mask as base64 encoded PNG
- "label": a descriptive text label for the element

JSON形式のみを出力してください。"""

    response = client.models.generate_content(
        model=SEGMENTATION_MODEL,
        contents=[prompt, image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    try:
        segments = json.loads(response.text)
        return segments
    except json.JSONDecodeError:
        # JSONが見つからない場合、テキストから抽出を試みる
        import re
        json_match = re.search(r'\[[\s\S]*\]', response.text)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"Failed to parse segmentation response: {response.text}")


def extract_element(image: Image.Image, segment: dict) -> Image.Image:
    """
    セグメント情報を使って要素を切り出す

    Args:
        image: 元画像
        segment: セグメント情報（box_2d, mask, label）

    Returns:
        切り出された画像（透過PNG）
    """
    width, height = image.size

    # bbox座標を実際のピクセル座標に変換（0-1000 → 実際のサイズ）
    box = segment["box_2d"]
    y0 = int(box[0] * height / 1000)
    x0 = int(box[1] * width / 1000)
    y1 = int(box[2] * height / 1000)
    x1 = int(box[3] * width / 1000)

    # 要素を切り出し
    cropped = image.crop((x0, y0, x1, y1))

    # マスクがある場合は適用
    if "mask" in segment and segment["mask"]:
        try:
            mask_data = base64.b64decode(segment["mask"])
            mask_img = Image.open(BytesIO(mask_data)).convert("L")

            # マスクをクロップサイズにリサイズ
            mask_img = mask_img.resize(cropped.size, Image.Resampling.LANCZOS)

            # RGBAに変換してマスクを適用
            cropped = cropped.convert("RGBA")
            cropped.putalpha(mask_img)
        except Exception as e:
            print(f"  [Warning] マスク適用に失敗: {e}")

    return cropped


def image_to_svg(client, element_image: Image.Image, label: str) -> str:
    """
    切り出した要素をSVGに変換

    Args:
        element_image: 要素画像
        label: 要素のラベル

    Returns:
        SVGコード
    """
    # ラベルに応じてプロンプトを調整
    if "text" in label.lower() or "title" in label.lower():
        prompt = f"""この画像のテキストをSVGで再現してください。

要素: {label}

以下の点を正確に再現してください：
- テキストの内容
- フォントスタイル（太さ、サイズ感）
- 色（グラデーションがあれば含める）
- 縁取り（あれば）
- シャドウ効果（あれば）

SVGコードのみを出力してください。<svg>タグから始めてください。
viewBoxは "0 0 {element_image.width} {element_image.height}" にしてください。"""
    else:
        prompt = f"""この画像の要素をSVGで再現してください。

要素: {label}

できるだけ正確に形状と色を再現してください。
SVGコードのみを出力してください。<svg>タグから始めてください。
viewBoxは "0 0 {element_image.width} {element_image.height}" にしてください。"""

    response = client.models.generate_content(
        model=SVG_MODEL,
        contents=[prompt, element_image]
    )

    # SVGを抽出
    text = response.text

    # ```svg ... ``` または <svg>...</svg> を抽出
    import re
    svg_match = re.search(r'```svg\s*([\s\S]*?)\s*```', text)
    if svg_match:
        return svg_match.group(1).strip()

    svg_match = re.search(r'(<svg[\s\S]*?</svg>)', text)
    if svg_match:
        return svg_match.group(1).strip()

    # SVGが見つからない場合はそのまま返す
    return text


def main():
    """メイン処理"""
    # テスト画像
    test_image_path = Path(__file__).parent.parent / "output_parse_image" / "IZ99-8459.png"

    if not test_image_path.exists():
        print(f"Error: テスト画像が見つかりません: {test_image_path}")
        return

    print(f"=== セグメンテーション → SVG変換 検証 ===\n")
    print(f"入力画像: {test_image_path}\n")

    # クライアント初期化
    client = get_client()

    # 画像読み込み
    print("[Step 1] 画像を読み込み中...")
    image, _ = load_image(str(test_image_path))
    print(f"  サイズ: {image.size}")

    # セグメンテーション
    print("\n[Step 2] セグメンテーション実行中...")
    try:
        segments = segment_image(client, image)
        print(f"  検出された要素: {len(segments)}個")

        for i, seg in enumerate(segments):
            label = seg.get("label", "unknown")
            box = seg.get("box_2d", [])
            print(f"    [{i+1}] {label}: bbox={box}")

        # セグメンテーション結果を保存
        with open(OUTPUT_DIR / "segments.json", "w", encoding="utf-8") as f:
            # maskはサイズが大きいので省略
            segments_summary = [
                {"label": s.get("label"), "box_2d": s.get("box_2d"), "has_mask": bool(s.get("mask"))}
                for s in segments
            ]
            json.dump(segments_summary, f, ensure_ascii=False, indent=2)
        print(f"\n  セグメンテーション結果を保存: {OUTPUT_DIR / 'segments.json'}")

    except Exception as e:
        print(f"  Error: セグメンテーションに失敗: {e}")
        return

    # 各要素を切り出してSVG変換
    print("\n[Step 3] 各要素を切り出してSVG変換中...")

    for i, seg in enumerate(segments):
        label = seg.get("label", f"element_{i}")
        safe_label = "".join(c if c.isalnum() else "_" for c in label)[:30]

        print(f"\n  === 要素 {i+1}: {label} ===")

        # 要素を切り出し
        try:
            element_img = extract_element(image, seg)

            # 切り出した画像を保存
            element_path = OUTPUT_DIR / f"{i+1}_{safe_label}.png"
            element_img.save(element_path)
            print(f"    切り出し画像: {element_path}")

        except Exception as e:
            print(f"    Error: 切り出しに失敗: {e}")
            continue

        # SVG変換
        try:
            svg_code = image_to_svg(client, element_img, label)

            # SVGを保存
            svg_path = OUTPUT_DIR / f"{i+1}_{safe_label}.svg"
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_code)
            print(f"    SVG: {svg_path}")

        except Exception as e:
            print(f"    Error: SVG変換に失敗: {e}")
            continue

    print(f"\n=== 検証完了 ===")
    print(f"出力ディレクトリ: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
