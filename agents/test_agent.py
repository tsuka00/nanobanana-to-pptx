#!/usr/bin/env python3
"""
Designer Agent インタラクティブテスト
"""

import os
import sys
import base64
import random
import string
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def generate_run_id():
    """固有のID生成（例: ABCD-1234）"""
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    numbers = ''.join(random.choices(string.digits, k=4))
    return f"{letters}-{numbers}"

from PIL import Image
import io

# .env.local を読み込み
from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / '.env.local')

from agents import DesignerAgent

# 出力ディレクトリ
OUTPUT_DIR = PROJECT_ROOT / "output"


def create_test_image(width=1280, height=720, color='#2d3436'):
    """テスト用の画像を作成"""
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def load_image(path: str):
    """画像ファイルを読み込んでBase64に変換"""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def save_result(image_base64: str, output_path: str):
    """Base64画像をファイルに保存"""
    img_data = base64.b64decode(image_base64)
    with open(output_path, 'wb') as f:
        f.write(img_data)
    print(f"保存しました: {output_path}")


def main():
    # API キーの確認
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY が設定されていません")
        print(".env.local に GOOGLE_API_KEY を設定してください")
        sys.exit(1)

    # 実行IDを生成
    run_id = generate_run_id()
    print(f"=== Designer Agent [ID: {run_id}] ===\n")

    # エージェントを初期化
    print("エージェントを初期化中...")
    agent = DesignerAgent()
    print("初期化完了!\n")

    # 画像の準備
    print("画像ファイルのパスを入力 (空でテスト画像を生成):")
    image_input = input("> ").strip().strip("'\"")

    if image_input and os.path.exists(image_input):
        image_base64 = load_image(image_input)
        print(f"画像を読み込みました: {image_input}")
    elif image_input:
        print(f"ファイルが見つかりません: {image_input}")
        sys.exit(1)
    else:
        image_base64 = create_test_image()
        print("テスト画像を生成しました (1280x720)")

    print("\n" + "=" * 50)
    print("プロンプトを入力してください (空行で実行)")
    print("=" * 50 + "\n")

    # 複数行入力
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break

    user_prompt = "\n".join(lines)

    if not user_prompt.strip():
        print("プロンプトが空です。終了します。")
        sys.exit(0)

    print(f"\n--- プロンプト ---\n{user_prompt}\n")
    print("エージェント実行中...\n")

    # 実行
    result = agent.generate(
        user_prompt=user_prompt,
        image_base64=image_base64
    )

    print("\n" + "=" * 50)
    print("結果")
    print("=" * 50 + "\n")

    if result.get('success'):
        print(result.get('response', ''))

        # 結果画像があれば自動保存
        if result.get('image_base64'):
            # 出力ディレクトリを作成
            OUTPUT_DIR.mkdir(exist_ok=True)

            # ID付きファイル名
            save_path = OUTPUT_DIR / f"{run_id}.png"

            img_data = base64.b64decode(result['image_base64'])
            with open(save_path, 'wb') as f:
                f.write(img_data)

            print(f"\n画像を保存しました: {save_path}")
        else:
            print("\n(結果画像がありません)")
    else:
        print(f"Error: {result.get('error')}")
        if result.get('traceback'):
            print(f"\nTraceback:\n{result.get('traceback')}")


if __name__ == "__main__":
    main()
