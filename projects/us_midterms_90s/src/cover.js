// node src/cover.js       ->  exports/cover.png    (1080x1440, 3:4)
// node src/cover.js 43    ->  exports/cover_4x3.png (1440x1080, 4:3)
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const wide = process.argv[2] === '43';
  const page = await browser.newPage({ viewport: wide ? { width: 1440, height: 1080 } : { width: 1080, height: 1440 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'cover.html') + (wide ? '#43' : '')); await page.evaluate(() => window.ready);
  const out = path.join(__dirname, '..', 'exports', wide ? 'cover_4x3.png' : 'cover.png'); fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, Buffer.from((await page.evaluate(() => document.getElementById('c').toDataURL('image/png'))).split(',')[1], 'base64'));
  await browser.close(); console.log('cover ->', out);
})();
