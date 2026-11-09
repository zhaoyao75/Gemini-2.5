# 《手感，是错觉吗？》— 热手谬误（视频）

代码生成的知识动画，流水线和上一条《为什么朋友都比你受欢迎》相同（Canvas 画面 → Playwright 逐帧 → ffmpeg；numpy 合成 77 BPM 配乐）。

- 成片：`exports/hot_hand.mp4`（52.9 秒，1920×1080，30fps，-14.7 LUFS，无人声，中英双语字幕）
- 事实核查：`FACTS.md`；分镜：`STORYBOARD.md`；数字复算：`python3 verify_streak_bias.py`
- 场景时间在 `src/timeline.json`（按拍数；标题卡 `intro_seconds` = 1 秒，其余顺延）；水印也在那里改
- 视频里不含声明/参考页，参考文献放发布时的置顶评论

## 发布文案
- 标题：`Vibe知识大赏｜《手感，是错觉吗？》科学家错了30年？`
- 标签：`#vibe知识大赏 #热手谬误 #统计学 #篮球 #概率`
- 置顶评论：① Gilovich, Vallone & Tversky (1985), *The hot hand in basketball: On the misperception of random sequences*, Cognitive Psychology 17(3), 295–314；② Miller & Sanjurjo (2018), *Surprised by the Hot Hand Fallacy? A Truth in the Law of Small Numbers*, Econometrica 86(6), 2019–2047（arXiv:1902.01265）；③ 视频里「46.1% / 53.9%」是本片 20 万次模拟（脚本：`verify_streak_bias.py`）；④ 本片由 AI 编写代码生成，无实拍素材。
- 发布页勾选「内容由AI生成」。

## 重新出片
```bash
npm install                      # 字体；本地开发时 node_modules 是指向上一个项目的软链接
node src/render.js --keyframes   # 16 帧拼图 -> build/keyframes.png
python3 src/bgm.py && node src/render.js   # 全片 -> exports/hot_hand.mp4（约 2 分钟）
```
