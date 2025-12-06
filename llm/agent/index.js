/**
 * LLM Agent: Strands Agent ラッパー
 * Python の DesignerAgent を Node.js から呼び出す
 */

const { spawn } = require('child_process');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const AGENTS_DIR = path.join(PROJECT_ROOT, 'agents');

/**
 * Designer Agent を実行
 * @param {Object} options
 * @param {string} options.userPrompt - ユーザーの自然言語指示
 * @param {string} [options.imageBase64] - 元画像のBase64データ
 * @param {string} [options.mimeType] - 画像のMIMEタイプ
 * @returns {Promise<Object>} 生成結果
 */
async function runDesignerAgent({ userPrompt, imageBase64, mimeType = 'image/png' }) {
  return new Promise((resolve, reject) => {
    const input = JSON.stringify({
      userPrompt,
      imageBase64,
      mimeType
    });

    const pythonProcess = spawn('python3', ['-m', 'agents.designer_agent'], {
      cwd: PROJECT_ROOT,
      env: { ...process.env }
    });

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (err) {
        reject(new Error(`Failed to parse Python output: ${stdout}`));
      }
    });

    pythonProcess.on('error', (err) => {
      reject(err);
    });

    pythonProcess.stdin.write(input);
    pythonProcess.stdin.end();
  });
}

module.exports = {
  runDesignerAgent
};
