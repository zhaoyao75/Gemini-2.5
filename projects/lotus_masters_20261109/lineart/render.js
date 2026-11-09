const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const out = process.argv[2] || 'peony_lineart_vangogh.png', page = process.argv[3] || 'paint.html';
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage();
  p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => { console.log('err:', e.stack); process.exit(1); });
  await p.goto('file://' + path.join(__dirname, page.split('?')[0]) + (page.includes('?') ? '?' + page.split('?')[1] : ''), { waitUntil: 'commit', timeout: 0 });
  await p.waitForFunction('window.DONE === true', null, { timeout: 240000, polling: 500 });
  const url = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
  fs.writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
  await b.close(); console.log('saved', out);
})();
