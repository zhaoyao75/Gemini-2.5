# 美国中期选举一次看懂（85.7 秒）

沿用 `../douyin_vibe_friendship_paradox` 的工程做法：Canvas 画面（每帧只由时间 t 决定）→ Playwright 逐帧截图 → numpy 合成 77 BPM 配乐 → ffmpeg 合成。

- 成片：`exports/us_midterms_90s.mp4`（85.66 秒，1920×1080，30fps，-14.6 LUFS，无人声，中英双语字幕）
- 封面：`exports/cover.png`（3:4，1080×1440）
- 风格沿用 LESSONS.md 的偏好：纯黑底 + 金色点缀；标题卡 1 秒放最前；节奏 77 BPM；文字尽量少；水印 @比特双子；不放声明/参考页。
- 结构（按拍）：标题 → 什么是中期选举 → 国会的四张牌 → 历史规律 → 选前局势 → 参议院（100 点阵，7 席翻转）→ 众议院（435 点阵，过半线 218）→ 州长 → 原因 → 接下来 → 收束提问

## 重新出片
```bash
npm install
python3 src/bgm.py && node src/render.js     # -> exports/us_midterms_90s.mp4（约 2.5 分钟）
node src/render.js --keyframes               # 关键帧拼图
node src/cover.js                            # 封面
```

## 数据与出处（截至 2026-11-09，计票仍在继续）
| 内容 | 数字 | 出处 |
|---|---|---|
| 参议院 | 选前 53:47；民主党翻转 KS/IA/TX/OH/ME/NC/SC 共 7 席，至少 54 席；AK、MS 未定 | Northeastern Global News；CBS News；AP（转载） |
| 众议院 | 民主党转为多数，CBS 预测 251–268 席 | CBS News（11/4 更新）。AP 早期计票数字各版不一致，**未采用** |
| 州长 | 选前 R26:D24；目前 D26、R20、4 个未定；德州 1995 年以来首位民主党州长 | AP（转载）；Northeastern |
| 历史规律 | 二战后总统所在党平均丢约 25–26 席；仅 1998、2002 例外；支持率 <50% 平均约 37，>50% 约 14 | Gallup；FiveThirtyEight |
| 原因 | 物价、伊朗战争与油价、总统支持率、候选人争议、选区重划 | Northeastern（分析人士观点） |
| 后续 | 议长约翰逊不再寻求领导职务；杰弗里斯「有望」出任；舒默「立法铁丝网」 | CBS News；Yahoo/AP |

**待更新**：众议院最终席位、AK/MS 结果、4 个未定州长——计票结束后改 `src/index.html` 里 `sceneHouse / sceneSenate / sceneGov` 和字幕，重新渲染。
"参议院改选约三分之一""36 个州选州长"取自赛前通行说法/AP，未逐条核对一手来源。

## 发布文案建议
标题：`美国中期选举，一次看懂｜民主党夺回两院意味着什么？`
标签：`#美国中期选举 #美国政治 #知识科普 #AI把知识拍成大片了`
置顶评论：数据来源（见上表）+「本片由 AI 编写代码生成，无实拍素材；数据截至 11 月 9 日」
