# 团子猫 × 荷花十二大师（特别篇 15 秒，方案 A）
- 素材来源：zhaoyao75/colab-code 分支 tuanzi-cat-assets（`scene/head5.html` 的猫和场景函数、站酷快乐体、ESC-50 猫叫 A/C）。
- `scene.html` = head5.html + 本篇场景脚本（`R(t)` 按时间渲染）。运行目录需有 `fonts/ZCOOLKuaiLe-Regular.ttf` 和 `p/*.jpg`（12 幅荷花画缩到 700×933）。
- `render.js`：Playwright 6 进程并行截 450 帧（1080×1920，30fps），再用 ffmpeg 合成。
- 配音：edge-tts zh-CN-XiaoyiNeural，rate -4%；需先 `certifi.where=lambda:'/root/.ccr/ca-bundle.crt'` 再 import edge_tts。
- 许可：猫叫 CC BY-NC，不可商用；配音商用前请确认 edge-tts 使用条款。
