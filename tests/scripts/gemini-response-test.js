/**
 * Gemini API レスポンス構造調査テスト
 *
 * 使用方法:
 *   node tests/gemini-response-test.js
 *
 * 環境変数:
 *   GOOGLE_API_KEY - Gemini APIキー（必須）
 */

const fs = require('fs-extra');
const path = require('path');
const dotenv = require('dotenv');
const { GoogleGenAI } = require('@google/genai');

// 環境変数の読み込み
const envLocalPath = path.resolve('.env.local');
const envPath = path.resolve('.env');
if (fs.existsSync(envLocalPath)) {
  dotenv.config({ path: envLocalPath });
} else if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

const MODEL = 'gemini-2.5-flash-image';
const TEST_IMAGE = path.resolve('workflow/image-to-image/data-asset/id-0001.png');

function requireEnv(key) {
  const val = process.env[key];
  if (!val) throw new Error(`${key} is required`);
  return val;
}

function loadImageBase64(imagePath) {
  const buf = fs.readFileSync(imagePath);
  return buf.toString('base64');
}

async function testGeminiResponse() {
  console.log('=== Gemini API Response Structure Test ===\n');

  const ai = new GoogleGenAI({ apiKey: requireEnv('GOOGLE_API_KEY') });
  const imgB64 = loadImageBase64(TEST_IMAGE);

  console.log(`Model: ${MODEL}`);
  console.log(`Test Image: ${TEST_IMAGE}\n`);

  const prompt = 'Create a simple variation of this image with slightly different colors.';

  console.log('Sending request to Gemini API...\n');

  const response = await ai.models.generateContent({
    model: MODEL,
    contents: [
      {
        role: 'user',
        parts: [
          { text: prompt },
          { inlineData: { mimeType: 'image/png', data: imgB64 } }
        ]
      }
    ],
    generationConfig: { responseMimeType: 'image/png' },
    safetySettings: [
      { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_NONE' }
    ]
  });

  console.log('=== Response Object Analysis ===\n');

  // トップレベルのキー
  console.log('1. Top-level keys:');
  console.log('   ', Object.keys(response));
  console.log();

  // 各プロパティの型と値
  console.log('2. Property types and values:');
  for (const key of Object.keys(response)) {
    const value = response[key];
    const type = Array.isArray(value) ? 'array' : typeof value;
    if (type === 'object' && value !== null) {
      console.log(`   ${key}: (${type})`);
      console.log('      Keys:', Object.keys(value));
    } else if (type === 'array') {
      console.log(`   ${key}: (${type}, length: ${value.length})`);
    } else {
      console.log(`   ${key}: (${type}) ${value}`);
    }
  }
  console.log();

  // usageMetadata の詳細
  console.log('3. usageMetadata details:');
  if (response.usageMetadata) {
    console.log('   ', JSON.stringify(response.usageMetadata, null, 4).replace(/\n/g, '\n   '));
  } else {
    console.log('   usageMetadata is undefined or null');
    console.log('   Checking alternative locations...');

    // 他の場所を探索
    if (response.candidates?.[0]?.usageMetadata) {
      console.log('   Found in candidates[0].usageMetadata:');
      console.log('   ', JSON.stringify(response.candidates[0].usageMetadata, null, 4));
    }
  }
  console.log();

  // candidates の構造
  console.log('4. candidates structure:');
  if (response.candidates?.length) {
    const candidate = response.candidates[0];
    console.log('   candidates[0] keys:', Object.keys(candidate));
    console.log('   finishReason:', candidate.finishReason);
    if (candidate.content) {
      console.log('   content.role:', candidate.content.role);
      console.log('   content.parts count:', candidate.content.parts?.length);
      if (candidate.content.parts?.[0]) {
        const part = candidate.content.parts[0];
        console.log('   content.parts[0] keys:', Object.keys(part));
        if (part.inlineData) {
          console.log('   content.parts[0].inlineData.mimeType:', part.inlineData.mimeType);
          console.log('   content.parts[0].inlineData.data length:', part.inlineData.data?.length);
        }
      }
    }
  }
  console.log();

  // 完全なレスポンス（画像データを除く）
  console.log('5. Full response (excluding image data):');
  const sanitized = JSON.parse(JSON.stringify(response, (key, value) => {
    if (key === 'data' && typeof value === 'string' && value.length > 100) {
      return `[BASE64_DATA: ${value.length} chars]`;
    }
    return value;
  }));
  console.log(JSON.stringify(sanitized, null, 2));

  console.log('\n=== Test Complete ===');
}

testGeminiResponse().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
