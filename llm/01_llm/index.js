/**
 * LLM 01: 設計フェーズ
 * 自然言語からデザイン設計JSONを生成
 */

const { GoogleGenAI } = require('@google/genai');

const MODEL = 'gemini-2.0-flash';

const PRICING = {
  inputPerMillion: 0.10,
  outputPerMillion: 0.40
};

function getClient(apiKey) {
  return new GoogleGenAI({ apiKey });
}

/**
 * 自然言語からデザイン設計JSONを生成
 * @param {Object} options
 * @param {string} options.apiKey - API key
 * @param {string} options.userPrompt - ユーザーの自然言語指示
 * @param {string} [options.imageBase64] - 参照画像（オプション）
 * @param {string} [options.mimeType] - 画像のMIMEタイプ
 * @returns {Promise<Object>} デザイン設計JSON
 */
async function design({ apiKey, userPrompt, imageBase64, mimeType = 'image/png' }) {
  const ai = getClient(apiKey);

  const systemPrompt = `あなたは画像デザインの設計者です。
ユーザーの指示を解析し、以下のJSON形式でデザイン設計を出力してください。
JSONのみを出力し、他のテキストは含めないでください。

{
  "background": {
    "prompt": "背景画像生成用のプロンプト（テキストは含めない指示）",
    "style": "スタイル指示（例: grayscale, colorful, minimal など）"
  },
  "variables": [
    {
      "key": "変数名（例: title, subtitle, caption）",
      "text": "表示するテキスト",
      "position": "配置位置",
      "fontSize": フォントサイズ（数値）,
      "color": "文字色（例: #ffffff）"
    }
  ]
}

重要なルール:
- テキストは全てvariablesに含め、backgroundのpromptにはテキスト生成の指示を含めない
- 元画像にテキストがある場合、backgroundのpromptで削除を指示する
- fontSizeはピクセル単位（メインタイトルは60-72、サブタイトルは32-40が目安）
- 複数のテキストがある場合、必ず異なるpositionを指定すること（重ならないように）

position指定:
- top: 上部
- center: 中央
- bottom: 下部
- top-left, top-right: 上部左右
- bottom-left, bottom-right: 下部左右
- center-top: 中央やや上（メインタイトル向け）
- center-bottom: 中央やや下（サブタイトル向け）

例: メインタイトルとサブタイトルがある場合
- メインタイトル → position: "center-top" または "center"
- サブタイトル → position: "center-bottom" または "bottom"`;

  const parts = [{ text: systemPrompt + '\n\nユーザーの指示: ' + userPrompt }];

  if (imageBase64) {
    parts.push({ inlineData: { mimeType, data: imageBase64 } });
  }

  const response = await ai.models.generateContent({
    model: MODEL,
    contents: [{ role: 'user', parts }]
  });

  const text = response?.candidates?.[0]?.content?.parts?.[0]?.text || '';

  // JSONを抽出
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('Failed to parse design JSON from LLM response');
  }

  try {
    return JSON.parse(jsonMatch[0]);
  } catch (err) {
    throw new Error('Invalid JSON in LLM response: ' + err.message);
  }
}

module.exports = {
  MODEL,
  PRICING,
  getClient,
  design
};
