const { chromium } = require('playwright'); const path=require('path'); const fs=require('fs');
const jobs=[['vangogh','half_n'],['klimt','half_n'],['picasso','dot_w'],['munch','dot_big'],['lichtenstein','half_n']];
const SEEDS=+process.argv[2]||6;
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});fs.mkdirSync('styled',{recursive:true});
await Promise.all(jobs.map(async([st,pose])=>{const p=await b.newPage();p.on('pageerror',e=>console.log('ERR',st,e.message));
 for(let s=1;s<=SEEDS;s++){await p.goto(`file://${path.resolve('style_cat.html')}?style=${st}&pose=${pose}&seed=${s}`);await p.waitForFunction('window.DONE===true',null,{timeout:120000});
  const u=await p.evaluate(()=>document.getElementById('c').toDataURL('image/png'));fs.writeFileSync(`styled/${st}_${s}.png`,Buffer.from(u.split(',')[1],'base64'));}
}));await b.close();console.log('ok');})();
