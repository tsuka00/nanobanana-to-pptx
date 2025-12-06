const path = require('path');
const fs = require('fs');
const sharp = require('sharp');
const { Resvg } = require('@resvg/resvg-js');

const FONTS = {
  'noto-sans-jp': {
    name: 'Noto Sans CJK JP',
    file: path.join(__dirname, 'NotoSansCJKjp-Regular.otf'),
    weights: ['regular']
  }
};

const DEFAULT_FONT = 'noto-sans-jp';

/**
 * フォントパスを取得
 * @param {string} [fontKey='noto-sans-jp'] - フォントキー
 * @returns {string} フォントファイルパス
 */
function getFontPath(fontKey = DEFAULT_FONT) {
  const font = FONTS[fontKey];
  if (!font) {
    throw new Error(`Font not found: ${fontKey}`);
  }
  return font.file;
}

/**
 * 利用可能なフォント一覧を取得
 * @returns {Object} フォント情報
 */
function listFonts() {
  return FONTS;
}

/**
 * テキストをSVGとして生成
 * @param {Object} options
 * @param {string} options.text - テキスト
 * @param {number} [options.fontSize=48] - フォントサイズ
 * @param {string} [options.color='#000000'] - 文字色
 * @param {string} [options.fontFamily='Noto Sans CJK JP'] - フォントファミリー
 * @returns {string} SVG文字列
 */
function createTextSvg({ text, fontSize = 48, color = '#000000', fontFamily = 'Noto Sans CJK JP' }) {
  const lines = text.split('\n');
  const lineHeight = fontSize * 1.4;
  const width = Math.max(...lines.map(l => l.length)) * fontSize;
  const height = lines.length * lineHeight;

  const textElements = lines.map((line, i) =>
    `<text x="0" y="${(i + 1) * lineHeight - fontSize * 0.3}" font-family="${fontFamily}" font-size="${fontSize}" fill="${color}">${escapeXml(line)}</text>`
  ).join('\n');

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
  ${textElements}
</svg>`;
}

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * テキストを画像としてレンダリング
 * @param {Object} options
 * @param {string} options.text - テキスト
 * @param {number} [options.fontSize=48] - フォントサイズ
 * @param {string} [options.color='#000000'] - 文字色
 * @param {string} [options.backgroundColor] - 背景色（透明の場合は省略）
 * @param {string} [options.fontKey='noto-sans-jp'] - フォントキー
 * @returns {Promise<Buffer>} PNG画像バッファ
 */
async function renderText({ text, fontSize = 48, color = '#000000', backgroundColor, fontKey = DEFAULT_FONT }) {
  const fontPath = getFontPath(fontKey);
  const fontData = fs.readFileSync(fontPath);

  const svg = createTextSvg({ text, fontSize, color });

  const resvg = new Resvg(svg, {
    font: {
      fontFiles: [fontPath],
      loadSystemFonts: false,
      defaultFontFamily: FONTS[fontKey].name
    },
    background: backgroundColor
  });

  const pngData = resvg.render();
  return pngData.asPng();
}

/**
 * 画像にテキストをオーバーレイ
 * @param {Object} options
 * @param {Buffer|string} options.image - 元画像（バッファまたはパス）
 * @param {string} options.text - テキスト
 * @param {number} [options.fontSize=48] - フォントサイズ
 * @param {string} [options.color='#000000'] - 文字色
 * @param {string} [options.position='bottom'] - 位置 ('top', 'bottom', 'center')
 * @param {number} [options.padding=20] - パディング
 * @returns {Promise<Buffer>} 合成後のPNG画像バッファ
 */
async function overlayText({ image, text, fontSize = 48, color = '#000000', position = 'bottom', padding = 20 }) {
  const textBuffer = await renderText({ text, fontSize, color });
  const textMeta = await sharp(textBuffer).metadata();

  const baseImage = sharp(image);
  const baseMeta = await baseImage.metadata();

  let top;
  let left;
  const centerY = Math.floor((baseMeta.height - textMeta.height) / 2);
  const centerX = Math.floor((baseMeta.width - textMeta.width) / 2);

  switch (position) {
    case 'top':
      top = padding;
      left = centerX;
      break;
    case 'top-left':
      top = padding;
      left = padding;
      break;
    case 'top-right':
      top = padding;
      left = baseMeta.width - textMeta.width - padding;
      break;
    case 'center':
      top = centerY;
      left = centerX;
      break;
    case 'center-top':
      top = centerY - textMeta.height - padding;
      left = centerX;
      break;
    case 'center-bottom':
      top = centerY + textMeta.height + padding;
      left = centerX;
      break;
    case 'bottom':
      top = baseMeta.height - textMeta.height - padding;
      left = centerX;
      break;
    case 'bottom-left':
      top = baseMeta.height - textMeta.height - padding;
      left = padding;
      break;
    case 'bottom-right':
      top = baseMeta.height - textMeta.height - padding;
      left = baseMeta.width - textMeta.width - padding;
      break;
    default:
      top = baseMeta.height - textMeta.height - padding;
      left = centerX;
  }

  return baseImage
    .composite([{
      input: textBuffer,
      top: Math.max(0, top),
      left: Math.max(0, left)
    }])
    .png()
    .toBuffer();
}

module.exports = {
  FONTS,
  DEFAULT_FONT,
  getFontPath,
  listFonts,
  createTextSvg,
  renderText,
  overlayText
};
