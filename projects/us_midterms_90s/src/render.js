// Render src/index.html frame by frame with headless Chromium, then mux with the BGM.
//   node src/render.js --keyframes   -> build/keyframes.png (3x3 contact sheet for QA)
//   node src/render.js               -> exports/sample.mp4
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const BUILD = path.join(ROOT, 'build');
const TL = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
const WORKERS = Math.max(1, Math.min(4, require('os').cpus().length));

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.addInitScript(tl => { window.TL = tl; }, TL);
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  const info = await page.evaluate(() => window.ready);
  return { page, info };
}

async function grab(page, t, frame) {
  const url = await page.evaluate(([t, f]) => { window.render(t, f); return document.getElementById('c').toDataURL('image/png'); }, [t, frame]);
  return Buffer.from(url.split(',')[1], 'base64');
}

async function main() {
  const keyframes = process.argv.includes('--keyframes');
  const dir = path.join(BUILD, keyframes ? 'keyframes' : 'frames');
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch();
  const first = await openPage(browser);
  const { duration, frames } = first.info;

  if (keyframes) {
    const beat = 60 / TL.bpm;
    const TB = TL.scenes_beats.D_title[1];
    const T = n => n < TB ? n / TB * TL.intro_seconds : TL.intro_seconds + (n - TB) * beat;
    const times = [0.05, ...[5, 9, 14, 18, 23, 28, 33, 37, 42, 45, 47.5, 51, 56, 62, 72, 86].map(T)];
    for (let i = 0; i < times.length; i++) {
      fs.writeFileSync(path.join(dir, `k${i}.png`), await grab(first.page, times[i], Math.round(times[i] * TL.fps)));
    }
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(dir, 'k%d.png'), '-vf', 'scale=480:-1,tile=4x4', '-frames:v', '1', path.join(BUILD, 'keyframes.png')]);
    console.log('keyframes ->', path.join(BUILD, 'keyframes.png'), 'times', times.join(', '));
    await browser.close();
    return;
  }

  const pages = [first.page];
  for (let i = 1; i < WORKERS; i++) pages.push((await openPage(browser)).page);
  let next = 0, done = 0;
  const t0 = Date.now();
  await Promise.all(pages.map(async page => {
    while (true) {
      const f = next++;
      if (f >= frames) return;
      fs.writeFileSync(path.join(dir, `f${String(f).padStart(5, '0')}.png`), await grab(page, f / TL.fps, f));
      if (++done % 60 === 0) console.log(`${done}/${frames} frames, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  }));
  await browser.close();

  const wav = path.join(BUILD, 'bgm.wav');
  if (!fs.existsSync(wav)) execFileSync('python3', [path.join(__dirname, 'bgm.py')], { stdio: 'inherit' });
  const out = path.join(ROOT, 'exports', 'us_midterms_90s.mp4');
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(TL.fps), '-i', path.join(dir, 'f%05d.png'), '-i', wav,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
  console.log('video ->', out, `(${duration.toFixed(2)}s, ${frames} frames)`);
}
main().catch(e => { console.error(e); process.exit(1); });
