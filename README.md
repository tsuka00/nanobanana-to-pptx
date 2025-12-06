# Nanobanana workflows (text-to-image / image-to-image)

SVG/PPTXパイプラインは停止し、生成ワークフロー（text-to-image / image-to-image）に整理しました。

## 環境変数 (.env / .env.local)
- `.env.local` があれば優先。なければ `.env` を読み込みます。
  ```env
  ELEMENTS=data/elements.json        # 省略時: data/elements.example.json
  LAYOUT=data/layout.json            # 省略時: data/layout.example.json
  GOOGLE_API_KEY=your-google-genai-key                      # Geminiで画像生成（必須）
  LANGFUSE_PUBLIC_KEY=your-langfuse-public-key              # 任意（追跡用）
  LANGFUSE_SECRET_KEY=your-langfuse-secret-key              # 任意（追跡用）
  LANGFUSE_BASE_URL=https://cloud.langfuse.com              # 任意（追跡用）
  ```
- 雛形: `.env.local.example` をコピーして `.env.local` を作成してください。

## 実運用手順
1) 画像生成（text-to-image）: `npm run workflow` でプロンプト入力→Gemini生成（`.env/.env.local` に `GOOGLE_API_KEY` 必須）。入出力は `workflow/text-to-image/data-asset/`（任意の素材置き場）と `workflow/text-to-image/output/` を使用。
2) 画像生成（image-to-imageトレーニング）: `npm run train <画像パス>` でプロンプトを実行後に入力。入出力は `workflow/image-to-image/data-asset/` と `workflow/image-to-image/output/` を使用。
3) 必要に応じて `npm run fetch:nanobanana` で要素別生成、`npm run sample` でデモ用入力生成

## Gemini (Google GenAI) で要素画像を生成する場合
- `.env` または `.env.local` に `GOOGLE_API_KEY` を設定（モデルは固定で `gemini-2.5-flash-image`）
- `ELEMENTS` で指定した要素リストの `prompt` を使って生成: `npm run fetch:nanobanana`

## トレーニング用（既存画像をもとに同じIDで生成 & Langfuseで記録）
- もっと簡単に: 画像パスだけ渡してプロンプトは実行時入力  
  `npm run train workflow/image-to-image/data-asset/id-0001.png`
  （実行後にプロンプトを聞かれます）
- 明示指定の例:  
  `npm run train -- --id=0001 --image=workflow/image-to-image/data-asset/id-0001.png --prompt="同じテイストで生成"`
- 出力: `workflow/image-to-image/output/id-0001-1234.png`（ID＋ランダム4桁）
- Langfuse: trainは`category=train`でtraceを作成し、usage（Gemini使用量が返る場合）とプロンプト/パラメータを記録。完了後に`good/bad/skip`でフィードバックを入力可能（trace.scoreに保存）。
- Langfuse連携（任意）：`.env`/`.env.local` に `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` を設定すると、trace/span にプロンプトや出力パスを記録します。

## ターミナルでプロンプトを入力してワークフロー実行
- コマンド: `npm run workflow`
- ターミナル上で背景/メイン/バッジのプロンプトとヘッドライン文言を入力すると、`output/tmp/session-*.json` を自動生成し、Geminiで画像生成 → パイプライン実行まで一括で行います（`GOOGLE_API_KEY` が必須）。
- Langfuse: workflowは`category=workflow`でtraceを作成し、完了後に`good/bad/skip`でフィードバックを入力できます。

## 主要ファイル
- `workflow/text-to-image/*` text-to-image ワークフロー
- `workflow/image-to-image/*` image-to-image トレーニングワークフロー
- `workflow/image-to-image/make-samples.js` サンプル入力生成（必要なければ未使用でOK）
- `data/elements.example.json` 要素定義サンプル（Nanobananaプロンプトメモもここに残せます）。
- `data/layout.example.json` レイアウトサンプル（キャンバス設定＋レイヤ配置＋テキスト）。

## カスタマイズのポイント
- Langfuseキーを設定すると trace/span/generation にプロンプトやフィードバック（good/bad）を保存できます。
- モデルは `gemini-2.5-flash-image` 固定。必要ならスクリプト側で変更してください。
