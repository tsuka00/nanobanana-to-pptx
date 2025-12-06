/**
 * nanobanana ワークフロー
 *
 * フェーズ1: LLM 01 で設計（デザインJSON生成）
 * フェーズ2: LLM 02 で背景画像生成（テキストなし）
 * フェーズ3: スクリプトで変数をテキストとして画像に挿入
 */

const fs = require('fs-extra');
const path = require('path');
const dotenv = require('dotenv');
const readline = require('readline');
const llm = require('#llm');
const langfuseClient = require('#langfuse');
const jpFonts = require('#plugin/jp-fonts');

const envLocalPath = path.resolve('.env.local');
const envPath = path.resolve('.env');
if (fs.existsSync(envLocalPath)) {
  dotenv.config({ path: envLocalPath });
} else if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

const INPUT_DIR = path.resolve('training/image-to-image/data-asset');
const OUTPUT_DIR = path.resolve('training/image-to-image/output');

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {};
  const positionals = [];
  args.forEach(arg => {
    if (arg.startsWith('--')) {
      const [k, v] = arg.replace(/^--/, '').split('=');
      params[k] = v || true;
    } else {
      positionals.push(arg);
    }
  });
  if (positionals.length && !params.image) {
    params.image = positionals[0];
  }
  return params;
}

function requireEnv(key) {
  const val = process.env[key];
  if (!val) throw new Error(`${key} is required`);
  return val;
}

function loadImageBase64(imagePath) {
  const abs = path.resolve(imagePath);
  if (!fs.existsSync(abs)) throw new Error(`Image not found: ${abs}`);
  return fs.readFileSync(abs).toString('base64');
}

function randomSuffix() {
  return Math.floor(1000 + Math.random() * 9000).toString();
}

function ask(question) {
  return new Promise(resolve => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(`${question}: `, answer => {
      rl.close();
      resolve(answer?.trim() || '');
    });
  });
}

/**
 * フェーズ3: 変数を画像にオーバーレイ
 */
async function applyVariables({ imageBuffer, variables }) {
  let result = imageBuffer;

  for (const v of variables) {
    result = await jpFonts.overlayText({
      image: result,
      text: v.text,
      fontSize: v.fontSize || 48,
      color: v.color || '#ffffff',
      position: v.position || 'center',
      padding: v.padding || 20
    });
  }

  return result;
}

async function run() {
  const args = parseArgs();
  const apiKey = requireEnv('GOOGLE_API_KEY');

  const derivedId = (() => {
    if (args.id) return args.id;
    if (args.image) {
      const base = path.basename(args.image, path.extname(args.image));
      const m = base.match(/id-(\d+)/);
      if (m) return m[1];
      return base;
    }
    return '0001';
  })();

  const id = derivedId;
  const imagePath = args.image || path.join(INPUT_DIR, `id-${id}.png`);
  const imageBase64 = loadImageBase64(imagePath);

  // ユーザー入力
  const userPrompt = await ask('どのような画像を生成しますか？');
  if (!userPrompt) {
    console.log('プロンプトが入力されませんでした');
    process.exit(1);
  }

  const trace = langfuseClient.createTrace({
    id: `nanobanana-${id}-${Date.now()}`,
    name: 'nanobanana',
    input: { userPrompt, imagePath },
    metadata: { category: 'nanobanana', id },
    tags: ['nanobanana']
  });

  try {
    // フェーズ1: 設計
    console.log('\n[フェーズ1] デザイン設計中...');
    const design = await llm.design.design({
      apiKey,
      userPrompt,
      imageBase64
    });
    console.log('設計JSON:', JSON.stringify(design, null, 2));

    if (trace) {
      langfuseClient.recordGeneration({
        traceId: trace.id,
        name: 'design',
        model: llm.design.MODEL,
        input: { userPrompt },
        output: design,
        tags: ['design']
      });
    }

    // フェーズ2: 背景画像生成
    console.log('\n[フェーズ2] 背景画像生成中...');
    const { buffer: bgBuffer, response } = await llm.generate.generateBackground({
      apiKey,
      design,
      imageBase64
    });

    const usage = langfuseClient.extractUsage(response);
    if (trace) {
      langfuseClient.recordGeneration({
        traceId: trace.id,
        name: 'generateBackground',
        model: llm.generate.MODEL,
        input: { backgroundPrompt: design.background.prompt },
        output: { step: 'background' },
        usage: langfuseClient.formatUsage(usage),
        tags: ['generate', 'background']
      });
    }

    // フェーズ3: テキストオーバーレイ
    let finalBuffer = bgBuffer;
    if (design.variables && design.variables.length > 0) {
      console.log('\n[フェーズ3] テキストオーバーレイ中...');
      finalBuffer = await applyVariables({
        imageBuffer: bgBuffer,
        variables: design.variables
      });
    }

    // 保存
    const outName = `${id}-${randomSuffix()}.png`;
    const outPath = path.join(OUTPUT_DIR, outName);
    await fs.ensureDir(OUTPUT_DIR);
    await fs.writeFile(outPath, finalBuffer);

    trace?.update({
      output: { outPath, outName, design },
      metadata: { usage }
    });

    console.log(`\n✓ 画像を保存しました: ${outPath}`);

    // フィードバック
    const feedback = await ask('\n結果はどうでしたか？ (good/bad/skip)');
    if (feedback && feedback.toLowerCase() !== 'skip') {
      const value = feedback.toLowerCase() === 'good' ? 1 : 0;
      trace?.score({ name: 'user_feedback', value, comment: feedback });
    }

  } catch (err) {
    trace?.update({ output: { error: err.message } });
    throw err;
  } finally {
    await langfuseClient.shutdown();
  }
}

run().catch(err => {
  console.error('ワークフロー失敗:', err);
  process.exit(1);
});
