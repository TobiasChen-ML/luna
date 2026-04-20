/**
 * PWA 图标生成脚本
 * 
 * 使用方法:
 * 1. 安装 sharp: npm install sharp --save-dev
 * 2. 运行: node scripts/generate-pwa-icons.js
 * 
 * 或者使用在线工具：
 * - https://realfavicongenerator.net/
 * - https://www.pwabuilder.com/imageGenerator
 */

import sharp from 'sharp';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');

// SVG 源文件
const svgPath = join(publicDir, 'favicon.svg');

// 需要生成的图标配置
const icons = [
  { name: 'favicon.ico', size: 32 },
  { name: 'favicon-16x16.png', size: 16 },
  { name: 'favicon-32x32.png', size: 32 },
  { name: 'apple-touch-icon.png', size: 180 },
  { name: 'pwa-192x192.png', size: 192 },
  { name: 'pwa-512x512.png', size: 512 },
];

// iOS 启动画面配置 (可选)
const splashScreens = [
  { name: 'apple-splash-2048-2732.png', width: 2048, height: 2732 },
  { name: 'apple-splash-1170-2532.png', width: 1170, height: 2532 },
  { name: 'apple-splash-1125-2436.png', width: 1125, height: 2436 },
  { name: 'apple-splash-1242-2688.png', width: 1242, height: 2688 },
  { name: 'apple-splash-828-1792.png', width: 828, height: 1792 },
  { name: 'apple-splash-1284-2778.png', width: 1284, height: 2778 },
  { name: 'apple-splash-1179-2556.png', width: 1179, height: 2556 },
  { name: 'apple-splash-1290-2796.png', width: 1290, height: 2796 },
];

async function generateIcons() {
  console.log('🎨 开始生成 PWA 图标...\n');
  
  if (!existsSync(svgPath)) {
    console.error('❌ 未找到 favicon.svg，请先创建源图标文件');
    process.exit(1);
  }
  
  const svgBuffer = readFileSync(svgPath);
  
  // 生成各尺寸图标
  for (const icon of icons) {
    try {
      const outputPath = join(publicDir, icon.name);
      
      if (icon.name.endsWith('.ico')) {
        // ICO 格式需要特殊处理，这里生成 PNG 作为替代
        await sharp(svgBuffer)
          .resize(icon.size, icon.size)
          .png()
          .toFile(outputPath.replace('.ico', '.png'));
        console.log(`✅ 生成: ${icon.name.replace('.ico', '.png')} (${icon.size}x${icon.size})`);
      } else {
        await sharp(svgBuffer)
          .resize(icon.size, icon.size)
          .png()
          .toFile(outputPath);
        console.log(`✅ 生成: ${icon.name} (${icon.size}x${icon.size})`);
      }
    } catch (error) {
      console.error(`❌ 生成 ${icon.name} 失败:`, error.message);
    }
  }
  
  console.log('\n📱 生成 iOS 启动画面...\n');
  
  // 生成启动画面 (带有居中图标和背景色)
  for (const splash of splashScreens) {
    try {
      const outputPath = join(publicDir, splash.name);
      const iconSize = Math.min(splash.width, splash.height) * 0.3; // 图标占画面30%
      
      // 先将 SVG 调整为合适大小
      const iconBuffer = await sharp(svgBuffer)
        .resize(Math.round(iconSize), Math.round(iconSize))
        .png()
        .toBuffer();
      
      // 创建启动画面背景
      await sharp({
        create: {
          width: splash.width,
          height: splash.height,
          channels: 4,
          background: { r: 26, g: 26, b: 46, alpha: 1 } // #1a1a2e
        }
      })
        .composite([{
          input: iconBuffer,
          gravity: 'center'
        }])
        .png()
        .toFile(outputPath);
      
      console.log(`✅ 生成: ${splash.name} (${splash.width}x${splash.height})`);
    } catch (error) {
      console.error(`❌ 生成 ${splash.name} 失败:`, error.message);
    }
  }
  
  console.log('\n🎉 PWA 图标生成完成！');
}

generateIcons().catch(console.error);
