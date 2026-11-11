const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const N = 360, FPS = 30, W = 6;
(async () => {
  fs.mkdirSync('frames3', { recursive: true });
  const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
  const run = async w => {
    const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    p.on('pageerror', e => { console.log('ERR', e.message); process.exit(1); });
    await p.goto('file://' + path.resolve('scene3.html'));
    await p.evaluate(() => document.fonts.load('40px KuaiLe'));
    await p.waitForTimeout(800);
    for (let i = w; i < N; i += W) {
      if (only && !only.includes(i)) continue;
      await p.evaluate(t => window.R(t), i / FPS);
      await p.screenshot({ path: `frames3/f${String(i).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 93 });
    }
    await b.close();
  };
  await Promise.all([...Array(W).keys()].map(run));
  console.log('done');
})();
