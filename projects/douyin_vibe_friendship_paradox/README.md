# 《为什么朋友都比你受欢迎》— 完整版（友谊悖论）

代码生成的知识动画：Canvas 画面（每帧只由时间 t 决定）→ Playwright 逐帧截图 → numpy 合成 77 BPM 配乐 → ffmpeg 合成 MP4。

- 成片：`exports/sample.mp4`（62.3 秒，1920×1080，30fps，-14.5 LUFS，无人声，中英双语字幕）
- 标题卡停留 1 秒（intro_seconds），其余场景按拍子顺延；视频内不含声明和参考页，参考文献放发布时的置顶评论。
- 视频内不出现「VIBE知识大赏」——参赛信息放在发布标题和话题标签里。
- 结构：标题卡 → 朋友圈卡片 → 星网 → 6 人网演示（5/6）→ 1991 论文 → 原理（每条友谊两端各记一次）→ 721 万 Facebook 用户 92.7% → 动态流（示意）→ 比较对象 → 暖色收束 → 结尾提问
- 数据出处：Feld (1991) AJS 96(6)；Ugander et al. (2011) arXiv:1111.4503（已对照原文）。示意网络的 3.4 / 4.0 由画面中的网络实际算出。

## 发布文案建议
标题：`Vibe知识大赏｜《为什么朋友都比你受欢迎》你的朋友，真的比你更受欢迎吗？`
标签：`#vibe知识大赏 #友谊悖论 #社会学 #统计 #AI把知识拍成大片了`
置顶评论：参考文献两条 + 「本片由 AI 编写代码生成，无实拍素材」

## 重新出片
```bash
npm install                      # 字体：思源宋体 / 思源黑体 / EB Garamond
node src/render.js --keyframes   # 16 张关键帧拼图 -> build/keyframes.png
python3 src/bgm.py && node src/render.js   # 全片 -> exports/sample.mp4（约 2 分钟）
```
场景时间、音效都在 `src/timeline.json`（按拍数）；水印文字也在那里改。
