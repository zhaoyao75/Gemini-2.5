// node src/storyboard.js -> exports/storyboard_v2/s1..s9.png + sheet.png (design stills for the 「两口钟」 redesign)
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const { execFileSync } = require('child_process');
(async () => {
  const TL = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
  const out = path.join(__dirname, '..', 'exports', 'storyboard_v2'); fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch(); const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.addInitScript(tl => { window.TL = tl; }, TL); await page.goto('file://' + path.join(__dirname, 'storyboard.html'));
  const n = await page.evaluate(() => window.ready);
  for (let i = 0; i < n; i++) fs.writeFileSync(path.join(out, `s${i + 1}.png`), Buffer.from((await page.evaluate(k => { window.drawFrame(k); return document.getElementById('c').toDataURL('image/png'); }, i)).split(',')[1], 'base64'));
  await browser.close();
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-start_number', '1', '-i', path.join(out, 's%d.png'), '-vf', 'scale=960:-1,tile=3x3:padding=8:color=0x222222', '-frames:v', '1', path.join(out, 'sheet.png')]);
  console.log('storyboard ->', out, n, 'frames');
})().catch(e => { console.error(e); process.exit(1); });
