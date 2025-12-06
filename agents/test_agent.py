#!/usr/bin/env python3
"""
Designer Agent インタラクティブテスト（要素別生成版）
"""

import os
import sys
import base64
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env.local を読み込み
from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / '.env.local')

from agents import DesignerAgent


def load_image(path: str) -> str:
    """画像ファイルを読み込んでBase64に変換"""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def main():
    # API キーの確認
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY が設定されていません")
        print(".env.local に GOOGLE_API_KEY を設定してください")
        sys.exit(1)

    # エージェントを初期化
    print("エージェントを初期化中...")
    agent = DesignerAgent()
    print(f"初期化完了! [Session ID: {agent.session_id}]\n")

    # 画像入力（オプション）
    print("画像ファイルのパスを入力 (空でtext-to-imageモード):")
    image_input = input("> ").strip().strip("'\"")

    image_base64 = None
    if image_input:
        if os.path.exists(image_input):
            image_base64 = load_image(image_input)
            print(f"画像を読み込みました: {image_input}")
            print("モード: image-to-image\n")
        else:
            print(f"ファイルが見つかりません: {image_input}")
            sys.exit(1)
    else:
        print("モード: text-to-image\n")

    print("=" * 50)
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

        if result.get('result_path'):
            print(f"\n最終結果: {result.get('result_path')}")
    else:
        print(f"Error: {result.get('error')}")
        if result.get('traceback'):
            print(f"\nTraceback:\n{result.get('traceback')}")


if __name__ == "__main__":
    main()
