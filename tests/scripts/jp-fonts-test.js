/**
 * jp-fonts プラグインテスト
 *
 * 使用方法:
 *   node tests/jp-fonts-test.js
 */

const fs = require('fs-extra');
const path = require('path');
const jpFonts = require('#plugin/jp-fonts');

const OUTPUT_DIR = path.resolve('tests/output');

async function test() {
  console.log('=== jp-fonts Plugin Test ===\n');

  // フォント一覧
  console.log('1. Available fonts:');
  console.log(jpFonts.listFonts());
  console.log();

  // フォントパス
  console.log('2. Font path:');
  console.log(jpFonts.getFontPath());
  console.log();

  // 出力ディレクトリ作成
  await fs.ensureDir(OUTPUT_DIR);

  // テキストレンダリング
  console.log('3. Rendering text to image...');
  const textBuffer = await jpFonts.renderText({
    text: 'こんにちは\n日本語フォント',
    fontSize: 64,
    color: '#333333'
  });
  const textOutPath = path.join(OUTPUT_DIR, 'jp-text-test.png');
  await fs.writeFile(textOutPath, textBuffer);
  console.log(`   Saved: ${textOutPath}`);
  console.log();

  // 画像にテキストオーバーレイ
  console.log('4. Overlay text on image...');
  const sampleImage = path.resolve('workflow/image-to-image/data-asset/id-0001.png');
  if (await fs.pathExists(sampleImage)) {
    const overlayBuffer = await jpFonts.overlayText({
      image: sampleImage,
      text: 'テスト画像',
      fontSize: 48,
      color: '#ffffff',
      position: 'bottom'
    });
    const overlayOutPath = path.join(OUTPUT_DIR, 'jp-overlay-test.png');
    await fs.writeFile(overlayOutPath, overlayBuffer);
    console.log(`   Saved: ${overlayOutPath}`);
  } else {
    console.log(`   Skipped: sample image not found`);
  }

  console.log('\n=== Test Complete ===');
}

test().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
