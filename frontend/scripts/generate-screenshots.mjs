/**
 * Generate placeholder screenshots for manifest.json
 * Run: node scripts/generate-screenshots.mjs
 */
import sharp from 'sharp';
import { existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');
const screenshotsDir = join(publicDir, 'screenshots');

async function generate() {
  if (!existsSync(screenshotsDir)) mkdirSync(screenshotsDir, { recursive: true });

  await sharp({
    create: {
      width: 540,
      height: 720,
      channels: 4,
      background: { r: 26, g: 26, b: 46, alpha: 1 }
    }
  })
    .png()
    .toFile(join(screenshotsDir, 'chat.png'));
  console.log('chat.png (540x720)');

  await sharp({
    create: {
      width: 1080,
      height: 720,
      channels: 4,
      background: { r: 26, g: 26, b: 46, alpha: 1 }
    }
  })
    .png()
    .toFile(join(screenshotsDir, 'characters.png'));
  console.log('characters.png (1080x720)');

  console.log('Placeholder screenshots generated. Replace with actual app screenshots later.');
}

generate().catch(console.error);