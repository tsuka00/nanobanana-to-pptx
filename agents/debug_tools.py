#!/usr/bin/env python3
"""
ツール個別デバッグ（インタラクティブ）
"""

import os
import sys
import base64
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image
import io

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / '.env.local')


def create_test_image(width=800, height=600, color='#2d3436'):
    """テスト用の画像を作成"""
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def test_jp_fonts():
    """jp_fonts ツールをテスト"""
    print("=== jp_fonts テスト ===\n")

    from agents.tools.jp_fonts import jp_fonts

    test_image = create_test_image()
    print(f"テスト画像を作成: Base64長 = {len(test_image)}")

    text = input("テキストを入力: ").strip()
    if not text:
        text = "テスト"

    result = jp_fonts._tool_func(
        image_base64=test_image,
        text=text,
        font_size=64,
        color="#ffffff",
        position="center"
    )

    print(f"\nSuccess: {result.get('success')}")
    if result.get('success'):
        print(f"出力画像 Base64長: {len(result.get('image_base64', ''))}")
        img_data = base64.b64decode(result['image_base64'])
        output_path = PROJECT_ROOT / 'test_output_jp_fonts.png'
        with open(output_path, 'wb') as f:
            f.write(img_data)
        print(f"保存: {output_path}")
    else:
        print(f"Error: {result.get('error')}")

    return result.get('success')


def test_text_to_image():
    """text_to_image ツールをテスト"""
    print("\n=== text_to_image テスト ===\n")

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY が設定されていません")
        return False

    from agents.tools.text_to_image import text_to_image

    prompt = input("画像生成プロンプトを入力: ").strip()
    if not prompt:
        print("プロンプトが空です。スキップします。")
        return False

    print("\nGemini API を呼び出し中（16:9固定）...")
    result = text_to_image._tool_func(prompt=prompt)

    print(f"\nSuccess: {result.get('success')}")
    if result.get('success'):
        print(f"出力画像 Base64長: {len(result.get('image_base64', ''))}")
        img_data = base64.b64decode(result['image_base64'])
        output_path = PROJECT_ROOT / 'test_output_text_to_image.png'
        with open(output_path, 'wb') as f:
            f.write(img_data)
        print(f"保存: {output_path}")
    else:
        print(f"Error: {result.get('error')}")

    return result.get('success')


def test_image_to_image():
    """image_to_image ツールをテスト"""
    print("\n=== image_to_image テスト ===\n")

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY が設定されていません")
        return False

    from agents.tools.image_to_image import image_to_image

    test_image = create_test_image()
    print(f"テスト画像を作成: Base64長 = {len(test_image)}")

    prompt = input("画像編集プロンプトを入力: ").strip()
    if not prompt:
        print("プロンプトが空です。スキップします。")
        return False

    print("\nGemini API を呼び出し中...")
    result = image_to_image._tool_func(
        prompt=prompt,
        image_base64=test_image,
        mime_type="image/png"
    )

    print(f"\nSuccess: {result.get('success')}")
    if result.get('success'):
        print(f"出力画像 Base64長: {len(result.get('image_base64', ''))}")
        img_data = base64.b64decode(result['image_base64'])
        output_path = PROJECT_ROOT / 'test_output_image_to_image.png'
        with open(output_path, 'wb') as f:
            f.write(img_data)
        print(f"保存: {output_path}")
    else:
        print(f"Error: {result.get('error')}")

    return result.get('success')


def main():
    print("ツール個別デバッグ\n")
    print("テストするツールを選択:")
    print("  1. jp_fonts (テキスト描画)")
    print("  2. text_to_image (テキストから画像生成)")
    print("  3. image_to_image (既存画像を編集)")
    print("  4. すべて")

    choice = input("\n選択 (1/2/3/4): ").strip()

    jp_ok = None
    t2i_ok = None
    i2i_ok = None

    if choice in ["1", "4"]:
        jp_ok = test_jp_fonts()

    if choice in ["2", "4"]:
        t2i_ok = test_text_to_image()

    if choice in ["3", "4"]:
        i2i_ok = test_image_to_image()

    print("\n=== 結果 ===")
    if jp_ok is not None:
        print(f"jp_fonts: {'OK' if jp_ok else 'NG'}")
    if t2i_ok is not None:
        print(f"text_to_image: {'OK' if t2i_ok else 'NG'}")
    if i2i_ok is not None:
        print(f"image_to_image: {'OK' if i2i_ok else 'NG'}")


if __name__ == "__main__":
    main()
