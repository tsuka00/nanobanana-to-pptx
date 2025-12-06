const { Langfuse } = require('langfuse');

let instance = null;

/**
 * Langfuseクライアントを取得（シングルトン）
 * 環境変数が設定されていない場合はnullを返す
 */
function getLangfuse() {
  if (instance) return instance;

  const hasCreds = process.env.LANGFUSE_PUBLIC_KEY && process.env.LANGFUSE_SECRET_KEY;
  if (!hasCreds) return null;

  instance = new Langfuse({
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'
  });

  return instance;
}

/**
 * トレースを作成
 * @param {Object} options
 * @param {string} options.id - トレースID
 * @param {string} options.name - トレース名
 * @param {Object} [options.input] - 入力データ
 * @param {Object} [options.metadata] - メタデータ
 * @param {string[]} [options.tags] - タグ
 * @returns {Object|null} トレースオブジェクトまたはnull
 */
function createTrace({ id, name, input, metadata, tags }) {
  const langfuse = getLangfuse();
  if (!langfuse) return null;

  return langfuse.trace({ id, name, input, metadata, tags });
}

/**
 * Generation（LLM呼び出し）を記録
 * @param {Object} options
 * @param {string} options.traceId - 親トレースID
 * @param {string} options.name - 生成名
 * @param {string} options.model - モデル名
 * @param {Object} options.input - 入力データ
 * @param {Object} [options.output] - 出力データ
 * @param {Object} [options.usage] - トークン使用量 { input, output, total }
 * @param {string[]} [options.tags] - タグ
 * @param {Object} [options.metadata] - メタデータ
 */
function recordGeneration({ traceId, name, model, input, output, usage, tags, metadata }) {
  const langfuse = getLangfuse();
  if (!langfuse) return;

  langfuse.generation({
    traceId,
    name,
    model,
    input,
    output,
    usage,
    tags,
    metadata
  });
}

/**
 * Langfuseをシャットダウン（バッファをフラッシュ）
 */
async function shutdown() {
  if (instance) {
    await instance.shutdownAsync();
    instance = null;
  }
}

/**
 * レスポンスからトークン使用量を抽出
 * @param {Object} response - Gemini APIレスポンス
 * @returns {Object} 使用量情報
 */
function extractUsage(response) {
  const u = response?.usageMetadata || {};
  return {
    promptTokens: u.promptTokenCount ?? null,
    candidatesTokens: u.candidatesTokenCount ?? null,
    totalTokens: u.totalTokenCount ?? null,
    promptTokensDetails: u.promptTokensDetails ?? null,
    candidatesTokensDetails: u.candidatesTokensDetails ?? null
  };
}

/**
 * 使用量をLangfuse形式に変換
 * @param {Object} usage - extractUsage()の戻り値
 * @returns {Object|undefined} Langfuse usage形式
 */
function formatUsage(usage) {
  if (!usage.promptTokens && !usage.totalTokens) return undefined;
  return {
    input: usage.promptTokens ?? undefined,
    output: usage.candidatesTokens ?? undefined,
    total: usage.totalTokens ?? undefined
  };
}

module.exports = {
  getLangfuse,
  createTrace,
  recordGeneration,
  shutdown,
  extractUsage,
  formatUsage
};
