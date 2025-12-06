const fs = require('fs-extra');
const path = require('path');
const dotenv = require('dotenv');
const readline = require('readline');
const llm = require('#llm/01');
const langfuseClient = require('#langfuse');

const envLocalPath = path.resolve('.env.local');
const envPath = path.resolve('.env');
if (fs.existsSync(envLocalPath)) {
  dotenv.config({ path: envLocalPath });
} else if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

const { MODEL, SAFETY_SETTINGS } = llm;
const INPUT_DIR = path.resolve('workflow/image-to-image/data-asset');
const OUTPUT_DIR = path.resolve('workflow/image-to-image/output');

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
  if (!val) {
    throw new Error(`${key} is required`);
  }
  return val;
}

function loadImageBase64(imagePath) {
  const abs = path.resolve(imagePath);
  if (!fs.existsSync(abs)) {
    throw new Error(`Image not found: ${abs}`);
  }
  const buf = fs.readFileSync(abs);
  return buf.toString('base64');
}

function randomSuffix() {
  return Math.floor(1000 + Math.random() * 9000).toString();
}

function ask(question, fallback) {
  return new Promise(resolve => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(fallback ? `${question} [${fallback}]: ` : `${question}: `, answer => {
      rl.close();
      if (answer && answer.trim()) return resolve(answer.trim());
      return resolve(fallback || '');
    });
  });
}


async function generateWithImage({ prompt, imagePath, id }) {
  const imgB64 = loadImageBase64(imagePath);

  const res = await llm.generateImage({
    apiKey: requireEnv('GOOGLE_API_KEY'),
    prompt,
    imageBase64: imgB64
  });

  const parts = res?.candidates?.[0]?.content?.parts || [];
  for (const part of parts) {
    if (part.inlineData?.data) {
      const buf = Buffer.from(part.inlineData.data, 'base64');
      const outName = `${id}-${randomSuffix()}.png`;
      const outPath = path.join(OUTPUT_DIR, outName);
      await fs.ensureDir(path.dirname(outPath));
      await fs.writeFile(outPath, buf);
      return { outPath, outName, response: res };
    }
  }
  throw new Error('Gemini response did not include an image');
}


async function run() {
  const args = parseArgs();
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
  const imagePath =
    args.image ||
    path.join(INPUT_DIR, `id-${id}.png`);

  let prompt = args.prompt;
  if (!prompt || prompt === true) {
    prompt = await ask('生成プロンプトを入力してください', `Replicate the style of ${id}`);
  }

  const trace = langfuseClient.createTrace({
    id: `train-${id}-${Date.now()}`,
    name: 'nanobanana-train',
    input: { prompt, imagePath },
    metadata: {
      category: 'train',
      id,
      model: MODEL,
      params: {
        generationConfig: { responseMimeType: 'image/png' },
        safetySettings: SAFETY_SETTINGS
      }
    },
    tags: ['train']
  });
  const span = trace?.span({
    name: 'gemini.generateContent',
    input: { prompt, imagePath, model: MODEL },
    metadata: { category: 'train' }
  });

  try {
    const { outPath, outName, response } = await generateWithImage({ prompt, imagePath, id });
    const usage = langfuseClient.extractUsage(response);
    span?.end({
      output: { outPath, outName, usage },
      metadata: { finishReason: response?.candidates?.[0]?.finishReason, usage }
    });
    trace?.update({
      output: { outPath, outName },
      metadata: { usage }
    });
    if (trace) {
      langfuseClient.recordGeneration({
        traceId: trace.id,
        name: 'gemini.generateContent',
        model: MODEL,
        input: { prompt, imagePath },
        output: { outPath, outName },
        usage: langfuseClient.formatUsage(usage),
        tags: ['train', 'image'],
        metadata: { finishReason: response?.candidates?.[0]?.finishReason }
      });
    }
    console.log(`✓ Generated image saved to ${outPath}`);

    const feedback = await ask('結果はどうでしたか？ (good/bad/skip)', 'skip');
    if (feedback && feedback.toLowerCase() !== 'skip') {
      const value = feedback.toLowerCase() === 'good' ? 1 : 0;
      trace?.score({ name: 'user_feedback', value, comment: feedback });
      if (trace) {
        langfuseClient.recordGeneration({
          traceId: trace.id,
          name: 'user_feedback',
          input: { feedbackPrompt: 'good/bad/skip' },
          output: { feedback },
          model: 'user',
          usage: { input: 0, output: 0, total: 0 },
          tags: ['train', 'feedback'],
          metadata: { feedback, score: value }
        });
      }
    }
  } catch (err) {
    span?.end({ output: { error: err.message } });
    trace?.update({ output: { error: err.message } });
    throw err;
  } finally {
    trace?.update({ metadata: { endedAt: new Date().toISOString() } });
    await langfuseClient.shutdown();
  }
}

run().catch(err => {
  console.error('Train workflow failed', err);
  process.exit(1);
});
