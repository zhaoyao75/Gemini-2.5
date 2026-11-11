# 团子猫入画（15 秒）：猫进入梵高、克里姆特、毕加索、蒙克、利希滕斯坦的荷花画
流程：
1. `sprite.html` + `sprite.js`：用归档的 head5.html 把团子猫渲染成透明 PNG（4 种表情）。
2. `style_cat.html` + `style.js`：把猫的 PNG 按大师风格重绘（canvas 画笔触/金箔/切面/波浪/网点），每种 6 个随机种子，播放时轮换产生"手绘抖动"。
3. `scene2.html` + `render.js`：粉紫房间 → 猫跳进画 → 5 幅画里的猫 → 掉回纸箱 → 结尾卡；Playwright 截 450 帧，ffmpeg 合成。
目录需要：`fonts/ZCOOLKuaiLe-Regular.ttf`、`p/`（12 幅荷花画 700×933）、`p2/`（5 幅 1080×1440）、`styled/`、`head5.html`（来自 colab-code 分支 tuanzi-cat-assets）。
许可：猫叫 ESC-50 为 CC BY-NC，不可商用；配音 edge-tts 商用前请确认条款。
