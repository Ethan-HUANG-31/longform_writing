# V1 Iteration 02 盲评结果与 Iteration 03 调整

## 1. 结论

V1 iteration 02 已完成真实生成和双 judge 盲评。第二轮改动让所有章节都进入 model rewrite，不再跳过无 blocking issue 的章节。

结果：

- `full_revised` 仍然稳定优于 `full_unrevised`；
- `case_07` 回归继续通过，`full_revised` 被两个 judge 都排在第一；
- `case_05` 和 `case_10` 中，`direct_write` 仍然排在 `full_revised` 前；
- 因此 iteration 02 没有通过主验收，需要进入 iteration 03。

这说明“所有章节都 rewrite”是必要但不充分的。问题已经从“部分章节没修”转移为“逐章修订仍被原章节结构和推理表达方式绑住”。

## 2. Blind Mapping

| Case | A | B | C | D |
|---|---|---|---|---|
| case_05 | direct_write | simple_engineered | full_unrevised | full_revised |
| case_10 | direct_write | simple_engineered | full_unrevised | full_revised |
| case_07 | direct_write | simple_engineered | full_unrevised | full_revised |

## 3. Judge 结果

### Rubric Judge

| Case | Ranking | 结论 |
|---|---|---|
| case_05 | A > D > C > B | D 比 C 好，但仍有大量“触摸纸纤维、比对签名、三处涂黑”的重复观察 |
| case_10 | A > D > C > B | D 线索链更公平，但第四章仍像“推理过程”笔记 |
| case_07 | D > C > B > A | D 长程压力最稳，两条时间线清楚 |

### Reader/Editor Judge

| Case | Ranking | 结论 |
|---|---|---|
| case_05 | A > D > C > B | A 线索推动人物责任更自然；D/C 核心反转更锐，但流程感重 |
| case_10 | A > D > C > B | A 的线索更有温度；D/C 仍像解题说明 |
| case_07 | D > C > B > A | D 的四段录像递进和情绪场景化最好 |

## 4. 关键证据

### 4.1 case_05

`full_revised` 的优点是第五章责任揭示更锐：封面纸团、撕痕、红字和小帅过去动作形成强反转。

但两个 judge 都指出它的问题：

- 多次重复“纸纤维”“涂黑”“签名”等证据动作；
- 证据被反复证明，而不是转化成新的行动或选择；
- 读者能看出工程化线索链，但感受到的叙事推进不如 `direct_write` 自然。

简单统计也支持这个判断：

| 文本 | `纸纤维` | `涂黑` | `签名` |
|---|---:|---:|---:|
| direct_write | 0 | 7 | 6 |
| full_revised | 15 | 16 | 31 |

这说明 iteration 02 的 rewrite 没有真正压缩“重复证明”。

### 4.2 case_10

`full_revised` 的 fair-play 线索更清楚：借书卡、小美办卡时间、书号密码、储物柜、阿强信封之间的关系完整。

但 judge 仍认为 `direct_write` 更好，因为：

- `direct_write` 把陈秀兰和阿强写成有温度的人，而不只是谜题节点；
- `full_revised` 的后段仍直接列“第一、第二、第三”；
- 线索解释正确，但读感像 worksheet。

### 4.3 case_07

`full_revised` 继续胜出，说明工程化 workflow 在复杂结构上有价值：

- 四段录像顺序完整；
- 第一章到第四章的责任链稳定；
- 过去录像和现在审判互相推进；
- 小美离开前看小帅“一秒”等细节能把责任场景化。

这个 case 证明不应该放弃 full skill，而是要让它在简单 / 中等复杂度文本上也具备 direct_write 的 prose flow 和情感闭合能力。

## 5. Root Cause

iteration 01 的 root cause 是修订器太保守，只修了部分章节。

iteration 02 修复了这个问题，但暴露出更深一层 root cause：

> 当前 revision 是逐章的，它能看到当前章和 previous summaries，但看不到整篇层面的重复词、重复证明动作、重复结尾方式。因此它会在每章内部“认真修”，但合并后仍像重复执行同一种推理流程。

更具体地说：

- rewrite prompt 要求“preserve all facts”，模型倾向于保留每一个证据动作，而不是压缩为一个更有力的场景后果；
- chapter-level review 只能判断单章问题，不知道“纸纤维 / 签名 / 第一第二第三”已经在全篇中过量；
- previous summaries 只提供事实，不提供 prose 边界和前章结尾质感，导致章节之间容易重复同一类动作或情绪结论；
- prompt 虽然说“不要 worksheet”，但没有给模型足够明确的禁止项和替代动作。

## 6. Iteration 03 调整

iteration 03 不再只加强“每章 rewrite”，而是加入 manuscript-level revision context。

具体调整：

1. 每章 rewrite prompt 增加 `previous_revised_tail`
   - 让模型看到前一章 revised 结尾，避免下一章重复同一类动作、意象或情绪总结。

2. 每章 rewrite prompt 增加 `manuscript_revision_context`
   - 只暴露文本层面的全篇坏味道，例如某些泛化证据词过量、编号式推理过量；
   - 不暴露未来剧情内容，避免提前泄露。

3. 增加强约束
   - 禁止“第一、第二、第三”“线索一/二/三”等编号式推理；
   - 禁止反复证明已经成立的线索；
   - 要求线索再次出现时必须造成行动、承认、冲突或决定。

4. 扩展测试
   - 测试 rewrite prompt 包含 `previous_revised_tail`；
   - 测试 rewrite prompt 包含 `manuscript_revision_context`；
   - 测试 manuscript-level context 能识别过量证据词和编号式推理。

## 7. Iteration 03 验收

iteration 03 仍按原目标验收：

- `case_05` / `case_10`: `full_revised` 需要超过 `direct_write`；
- `case_07`: 不退化，至少 `full_revised` > `full_unrevised`；
- 盲评 evidence 必须来自文本阅读质量，而不是工程过程；
- 如果 iteration 03 仍失败，则按原计划输出 route failure report 和 V1.1 建议。
