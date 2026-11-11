const { chromium } = require('playwright'); const path=require('path');
const poses={half_n:['half','n'],dot_w:['dot','w'],dot_big:['dot','big'],c_n:['c','n']};
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+path.resolve('sprite.html'));await p.evaluate(()=>document.fonts.ready);
for(const [k,[e,m]] of Object.entries(poses)){await p.evaluate(([e,m])=>window.pose(e,m),[e,m]);await p.screenshot({path:`sprites/${k}.png`,omitBackground:true,clip:{x:0,y:0,width:780,height:600}});}
await b.close();console.log('ok');})();
