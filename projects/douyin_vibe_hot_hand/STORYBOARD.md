# 《手感，是错觉吗？》分镜表

> 选题：热手谬误被翻案（友谊悖论同系列：取样方式带来的偏差）。核查结果见 `FACTS.md`，数字复算见 `verify_streak_bias.py`。
> 规格沿用上一条的偏好：标题卡 1 秒放最前、纯黑底、视频里不出现「VIBE知识大赏」、水印「@比特双子」、77 BPM、无声明/参考页（参考文献放置顶评论）、中英双语字幕、字少。
> 预计时长 **52.9 秒**（标题 1 秒 + 66 拍 × 0.779 秒 + 尾部 0.5 秒），1920×1080，30fps。

## 标题卡（0.0–1.0 s）
《手感，是错觉吗？》 / 热手谬误 / The Hot Hand Fallacy。第 0 帧完整显示，金色高光扫过，0.85 秒淡出。

## 场景表

| 场景 | 拍 | 时间 | 画面 | 字幕（中 / 英） | 音效 | 事实 |
|---|---|---|---|---|---|---|
| **A 钩子** | 3 | 1.0–3.3s | Tim 一排 3 个金色篮球依次亮起，第 4 个是闪烁的「?」；顶部标签「手感」 | 连中 3 球后，下一球更容易进吗？ / After three makes in a row, is the next shot more likely to go in? | 开场短促钢琴音；3 次 tick 对应 3 球亮起 | — |
| **B 球迷都信** | 3 | 3.3–5.7s | 一屏小圆点（球迷），逐个亮成金色，中央大字「手感」 | 几乎所有球迷和教练，都相信有「手感」 / Nearly every fan and coach believes in the hot hand. | 圆点亮起的细碎 tick | #1 |
| **C 1985 论文** | 6 | 5.7–10.4s | 做旧纸质论文页：COGNITIVE PSYCHOLOGY · 1985 / The Hot Hand in Basketball / Gilovich · Vallone · Tversky；第 3 拍盖红章「手感是错觉」；下方注：76 人队投篮 · 凯尔特人罚球 · 康奈尔球员实验；标「图为示意」 | 1985 年，三位心理学家分析了投篮数据 / In 1985, three psychologists analysed shooting data.<br>结论：「手感」只是错觉 / Their verdict: the hot hand is a fallacy. | 纸张滑入 whoosh；盖章 thud | #2 #3 |
| **D 影响** | 4 | 10.4–13.5s | 三个线条图标依次浮现：股市曲线、骰子、彩票球 | 这个结论成了经典，被用来解释股市、赌博和彩票 / It became canonical — used to explain markets, gambling and lotteries. | 3 次 tick | #4 |
| **E 转折** | 4 | 13.5–16.6s | 第二张论文页：ECONOMETRICA · NOVEMBER 2018 / Surprised by the Hot Hand Fallacy? / Miller · Sanjurjo；盖红章「方法有偏差」；画面整体色调变冷再回暖 | 这个结论，科学家错了 30 年 / Scientists got this wrong for 30 years —<br>直到 2018 年，统计方法的偏差才被发现 / until 2018, when the method's bias was found. | swell 上扬；盖章 thud | #5 |
| **F1 规则** | 4 | 16.6–19.7s | 规则卡：① 抛 3 次公平硬币 ② 只看每个「正面」之后的那一次 ③ 算这些次里正面占几成；金/黑硬币图标，下划线 = 被记录的那一次 | 抛 3 次公平硬币，只看每个「正面」后的那一次 / Flip a fair coin 3 times. Only look at the flip right after each head. | 规则逐条 tick | #6 |
| **F2 8 种结果** | 8 | 19.7–25.9s | 8 行表格，每拍出一行：HHH→100%，HHT→50%，HTH→0，HTT→0，THH→100%，THT→0，TTH→—，TTT→—；被记录的硬币加下划线；最后两行置灰划掉 | 8 种结果，出现的机会一样大 / Eight outcomes, all equally likely.<br>后两行没有可记的，作废 / The last two rows have nothing to record — discard. | 每行出现一次硬币 tick | #6 |
| **F3 平均** | 4 | 25.9–29.1s | 算式 (100% + 50% + 0 + 0 + 100% + 0) ÷ 6 → 5/12 → 大号数字滚到 41.7%；旁边一条 50% 虚线，差距高亮 | 「正面」之后还是正面，平均只有 41.7% / Heads after heads: only 41.7% on average. | 数字滚动 tick，落定 ding | #6 |
| **G 模拟 100 球** | 6 | 29.1–33.7s | Tim（纯随机射手，命中率恒 50%）投 100 球：一条条 100 格色条快速堆叠成密集的纹理（种子固定的真实模拟），随后出现两根柱：连中 3 球后 46.1% / 连丢 3 球后 53.9%；小注「本片模拟 20 万次，每次 100 球」 | Tim 是个命中率恒为 50% 的纯随机射手 / Tim is a pure random shooter: a constant 50% hit rate.<br>连中 3 球后 46.1%，连丢 3 球后反而 53.9% / After 3 makes: 46.1%. After 3 misses: 53.9%. | 色条堆叠的颗粒 tick；两根柱落定各一声 | #8 |
| **H 校正** | 6 | 33.7–38.4s | 一根「+3」的短柱，被「扣除偏差」的箭头推高到「+13」，p < 0.01；小注「康奈尔球员 26 人 × 100 球」 | 把这个偏差扣掉，再看 1985 年的投篮实验—— / Remove the bias and revisit the 1985 shooting experiment —<br>连中 3 球后比连丢 3 球后，命中率高 13 个百分点 / After 3 makes vs after 3 misses: 13 points higher. | 柱子上推时音高上行；到 +13 ding | #9 |
| **I 参照** | 4 | 38.4–41.5s | 0–15 个百分点的标尺：「13」金色标记；对照一条「NBA 2015–16：中位三分射手 vs 顶级三分射手 = 12」 | 相当于 NBA 普通三分射手和顶级射手的差距 / About the gap between an average and an elite NBA three-point shooter. | 两个标记落定 tick | #10 |
| **J 保留** | 5 | 41.5–45.4s | 三张便签依次落下：「比赛里有防守」「只有 26 人 × 100 球」「后续研究并不一致」 | 但争议没有结束：样本只有 26 名球员 / But it's not settled: only 26 players.<br>后续研究，有的找到手感，有的没有 / Later studies disagree. | 便签 thud 轻 | #9 #11 #12 |
| **K 落点** | 5 | 45.4–49.3s | 3 个金色圆点连亮，之后第 4 个半亮半暗；字出现，圆点光晕呼吸 | 手感，不是魔法 / The hot hand isn't magic —<br>但也未必是错觉 / but it may not be an illusion either. | 钢琴单音，鼓点撤掉 | — |
| **L 结尾提问** | 4 | 49.3–52.4s | 全黑，一颗金色圆点；问题浮现 | 你最近一次「手感来了」，是什么时候？ / When did you last feel “hot”? | 结尾 ding | — |

## timeline.json 草案（拍数）

```json
{ "bpm": 77, "intro_seconds": 1.0, "total_beats": 70, "tail_seconds": 0.5, "scenes_beats": {
  "D_title": [0, 4],
  "A_hook": [4, 7],
  "B_belief": [7, 10],
  "C_1985": [10, 16],
  "D_impact": [16, 20],
  "E_twist": [20, 24],
  "F1_rules": [24, 28],
  "F2_table": [28, 36],
  "F3_avg": [36, 40],
  "G_sim": [40, 46],
  "H_correct": [46, 52],
  "I_benchmark": [52, 56],
  "J_caveat": [56, 61],
  "K_landing": [61, 66],
  "L_end": [66, 70]
}, "watermark": "@比特双子" }
```

## 视觉与复用

- 沿用「黑金 + 纸卡 + 红印章」母题：两张论文页复用上一条的纸卡与盖章代码，换文字即可。
- 新增三块：硬币 8 行表格（逐行出现）、100 格投篮色条的种子模拟（用本目录脚本同一算法，保证画面与 46.1% / 53.9% 一致）、「+3 → +13」柱与 NBA 标尺。
- 「手感」「Tim」贯穿：开头 Tim 连中 3 球，中段 Tim 是纯随机射手（保持上一条的人物名一致）。

## 要特别小心的地方

1. **措辞红线**：「科学家错了 30 年」经确认保留（指 1985 年研究的结论被后来的分析翻转，见 FACTS.md）；不说「手感被证明存在」，结尾只说「未必是错觉」。
2. **选择偏差很抽象**：靠 F2 的 8 行表格讲清楚，宁可多停两拍；G 的模拟是给「球场不是抛硬币」的观众一个落点。
3. **「+13」只来自一组 26 人的控制实验**：H 场景必须带「26 人 × 100 球」小注，J 场景明说争议未完。
4. **所有示意画面标注**：论文页「图为示意」；G 场景标「本片模拟」；开头 Tim 与球迷圆点是示意，不是真实数据。

## 发布文案草稿

- 标题：`Vibe知识大赏｜《手感，是错觉吗？》科学家错了30年？`
- 标签：`#vibe知识大赏 #热手谬误 #统计学 #篮球 #概率`
- 置顶评论：参考文献 ① Gilovich, Vallone & Tversky (1985), Cognitive Psychology 17(3), 295–314；② Miller & Sanjurjo (2018), Econometrica 86(6), 2019–2047（arXiv:1902.01265）；③ 「46.1% / 53.9%」为本片 20 万次模拟，脚本见仓库 `projects/douyin_vibe_hot_hand/verify_streak_bias.py`；④「本片由 AI 编写代码生成，无实拍素材」。
- 发布页勾选「内容由AI生成」。

## 待你确认

1. 片名：《手感，是错觉吗？》OK？备选《连赢三把，是手感还是运气？》。
2. 预计约 53 秒，比上一条短；要更长的话，可在 G 后加「连续 4 个、5 个」的对比，或加一段「游戏连胜」的场景。
3. 开头用 Tim 当投手、中段 Tim 当纯随机射手，是否保留？
