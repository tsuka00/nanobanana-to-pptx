/**
 * LLM 02: 画像生成フェーズ
 * 設計JSONを元に背景画像を生成（テキストは生成しない）
 */

const { GoogleGenAI } = require('@google/genai');

const MODEL = 'gemini-2.5-flash-image';

const PRICING = {
  inputPerMillion: 0.075,
  outputPerMillion: 0.30
};

const SAFETY_SETTINGS = [
  { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_NONE' }
];

function getClient(apiKey) {
  return new GoogleGenAI({ apiKey });
}

/**
 * 背景画像を生成（テキストなし）
 * @param {Object} options
 * @param {string} options.apiKey - API key
 * @param {Object} options.design - 設計JSON（01_llmの出力）
 * @param {string} options.imageBase64 - 元画像
 * @param {string} [options.mimeType] - 画像のMIMEタイプ
 * @returns {Promise<Object>} { buffer: Buffer, response: Object }
 */
async function generateBackground({ apiKey, design, imageBase64, mimeType = 'image/png' }) {
  const ai = getClient(apiKey);

  // 背景生成プロンプト（テキスト生成を明示的に禁止）
  const prompt = `${design.background.prompt}

重要: 画像内にテキストや文字を一切含めないでください。背景のみを生成してください。`;

  const response = await ai.models.generateContent({
    model: MODEL,
    contents: [
      {
        role: 'user',
        parts: [
          { text: prompt },
          { inlineData: { mimeType, data: imageBase64 } }
        ]
      }
    ],
    generationConfig: { responseMimeType: 'image/png' },
    safetySettings: SAFETY_SETTINGS
  });

  const parts = response?.candidates?.[0]?.content?.parts || [];
  for (const part of parts) {
    if (part.inlineData?.data) {
      return {
        buffer: Buffer.from(part.inlineData.data, 'base64'),
        response
      };
    }
  }

  throw new Error('Gemini response did not include an image');
}

module.exports = {
  MODEL,
  PRICING,
  SAFETY_SETTINGS,
  getClient,
  generateBackground
};
