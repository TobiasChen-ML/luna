/**
 * Generate manifest icons into public/icons/
 * Run: node scripts/generate-manifest-icons.js
 */
import sharp from 'sharp';
import { readFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');
const svgPath = join(publicDir, 'favicon.svg');
const iconsDir = join(publicDir, 'icons');

const iconSizes = [72, 96, 128, 144, 152, 192, 384, 512];

async function generate() {
  if (!existsSync(iconsDir)) mkdirSync(iconsDir, { recursive: true });
  const svgBuffer = readFileSync(svgPath);

  for (const size of iconSizes) {
    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(join(iconsDir, `icon-${size}x${size}.png`));
    console.log(`icon-${size}x${size}.png`);
  }
  console.log('Done!');
}

generate().catch(console.error);
