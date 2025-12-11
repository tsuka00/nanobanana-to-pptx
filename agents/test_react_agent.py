#!/usr/bin/env python3
"""
ReAct Designer Agent インタラクティブテスト
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

from agents.react_agent import ReActDesignerAgent


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
    print("ReAct エージェントを初期化中...")
    agent = ReActDesignerAgent()
    print(f"初期化完了! [Session ID: {agent.session_id}]\n")

    # 参照画像入力（オプション）
    print("参照画像のパスを入力 (空でスキップ):")
    image_input = input("> ").strip().strip("'\"")

    reference_image = None
    if image_input:
        if os.path.exists(image_input):
            reference_image = load_image(image_input)
            print(f"参照画像を読み込みました: {image_input}\n")
        else:
            print(f"ファイルが見つかりません: {image_input}")
            sys.exit(1)

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
    print("ReAct エージェント実行中...\n")

    # 実行
    result = agent.run(
        user_prompt=user_prompt,
        reference_image_base64=reference_image
    )

    print("\n" + "=" * 50)
    print("結果")
    print("=" * 50 + "\n")

    if result.get('success'):
        print(f"成功! (イテレーション: {result.get('iterations')}回)")
        print(f"\n--- Final Answer ---\n{result.get('final_answer', '')}")

        if result.get('result'):
            r = result['result']
            if r.get('pptx_path'):
                print(f"\nPPTX: {r['pptx_path']}")
            if r.get('background_path'):
                print(f"背景画像: {r['background_path']}")
    else:
        print(f"失敗: {result.get('error')}")

    print(f"\n--- 実行したツール ({len(result.get('tools_executed', []))}件) ---")
    for i, t in enumerate(result.get('tools_executed', []), 1):
        print(f"{i}. {t['action']}")
        if t.get('observation'):
            print(f"   → {t['observation'][:100]}...")


if __name__ == "__main__":
    main()
