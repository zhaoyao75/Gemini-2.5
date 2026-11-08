// node render.js <style> <out.png> [width]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [style, out, w = '900'] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage();
  await p.goto('file://' + path.join(__dirname, 'index.html') + `?style=${style}&w=${w}`, { waitUntil: 'commit', timeout: 0 });
  await p.waitForFunction('window.DONE === true', null, { timeout: 300000, polling: 500 });
  const url = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
  fs.writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
  await b.close(); console.log('saved', out);
})();
