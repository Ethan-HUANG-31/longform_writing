# V1 Iteration 01 盲评结果与下一轮修订目标

## 1. 结论摘要

V1 iteration 01 已完成 harness-level 真实文本验证：`direct_write`、`simple_engineered`、`full_unrevised`、`full_revised` 四路样本均已生成 blind package，并由两个独立 evaluator 完成盲评。

结论是：

- `full_revised` 相比 `full_unrevised` 在三个 case 中都有提升；
- `case_07` 的复杂结构回归通过，`full_revised` 被两个 evaluator 都排在第一；
- 但主目标未通过：在 `case_05` 和 `case_10` 中，`full_revised` 仍然输给 `direct_write`；
- 因此 V1 revision loop 需要进入 iteration 02，而不能宣称已经完成最终验收。

这次失败不是“工程化工作流完全无效”，而是说明当前 revision loop 的质量增益不够。它证明了修订环节有方向上的价值，但修订策略太保守，无法充分修复 full skill 文本中最影响阅读体验的问题。

## 2. Blind Mapping

iteration 01 的私有映射如下：

| Case | A | B | C | D |
|---|---|---|---|---|
| case_05 | direct_write | simple_engineered | full_unrevised | full_revised |
| case_10 | direct_write | simple_engineered | full_unrevised | full_revised |
| case_07 | direct_write | simple_engineered | full_unrevised | full_revised |

两个 evaluator 在评测时均未查看 mapping，只能看到匿名样本 A/B/C/D。

## 3. Rubric Judge 结果

Rubric Judge 使用 `longform_text_quality_rubric_v1` 做结构化评测。

| Case | 排名 | 关键结论 |
|---|---|---|
| case_05 | A > D > C > B | A 最好；D 比 C 好，但仍有程序化、重复处理证据的问题 |
| case_10 | A > D > C > B | A 最像完成度高的轻推理；D/C 保留线索但推导过程笨重 |
| case_07 | D > C > B > A | D 完成四段录像结构，责任链最清楚 |

Rubric Judge 给出的核心证据：

- `case_05`：A 胜在“scene、clue escalation、emotional consequence”的平衡；D 有更强线索连续性，但反复处理同一类证据，阅读上像流程记录。
- `case_10`：A 的 reader-facing payoff 更完整；D/C 虽然更像 fair-play deduction，但密码推导显得过度加工。
- `case_07`：D 胜在完整结构和责任链，但仍有结尾重复、总结式收束的问题。

## 4. Reader/Editor Judge 结果

Reader/Editor Judge 不使用 rubric，只按真实阅读体验判断。

| Case | 排名 | 关键结论 |
|---|---|---|
| case_05 | A > D > C > B | A 最完整、最顺；D/C 证据细节更锐，但重复削弱叙事力 |
| case_10 | A > D > C > B | A 最有阅读满足感；D/C 解谜过程更工程化 |
| case_07 | D > C > A > B | D 最完整，也有最清楚的责任链 |

Reader/Editor Judge 的核心判断是：好的样本不是证据最多的样本，而是能让证据改变主角自我理解的样本。弱样本的问题主要是两个：

- 只停在开头，结构不完整；
- 或者把推理写成程序化记账，而不是场景驱动的悬疑。

## 5. V1 Skill 当前的优点

虽然主验收未通过，但 iteration 01 说明 full skill 仍有明确优势：

### 5.1 复杂结构下的完整性更强

`case_07` 是双时间线 / 多录像结构，direct 和 simple 都没有完整完成核心结构。`full_revised` 被两个 evaluator 排在第一。

这说明 full skill 的中间工程表示、章节拆分、summary-after、revision loop 对复杂结构是有价值的。它能稳定维护“第几段录像揭示什么、责任链如何递进”这类长程结构。

### 5.2 revision loop 确实能提升 full skill

三个 case 中，`full_revised` 都排在 `full_unrevised` 前面：

- `case_05`: D > C
- `case_10`: D > C
- `case_07`: D > C

这说明 review -> plan -> rewrite 这条链路不是空转。它能把已有 full skill draft 往更好的方向推。

### 5.3 线索和事实一致性优于简单写法

在 `case_05` 和 `case_10` 中，D/C 经常被评价为线索连续性更强、fair-play deduction 更完整。问题不在于完全没有结构，而是结构痕迹过重，叙事表达不够自然。

这给下一轮优化提供了明确方向：不是废弃工程化结构，而是让工程化结构退到幕后，把事实和线索转化成读者可感知的场景压力。

## 6. 失败原因

### 6.1 当前 revision loop 太保守

iteration 01 中，只有被 review 判定有 blocking issue 的章节才会进入 rewrite。没有 blocking issue 的章节被原样保留。

实际生成记录显示：

| Case | 被重写章节 | 原样保留章节 |
|---|---|---|
| case_05 | chapter_01, chapter_05 | chapter_02, chapter_03, chapter_04 |
| case_10 | chapter_01, chapter_02 | chapter_03, chapter_04 |
| case_07 | chapter_01-04 | 无 |

这直接解释了为什么 `case_05` 和 `case_10` 仍然输给 direct_write：最影响阅读体验的中段推理 / 证据处理章节没有被重写。

### 6.2 review 判定标准偏“硬错误”，不够关注阅读质量

当前 review 更容易发现：

- 重复句；
- checklist-like marker；
- 明显 beat 泄漏；
- 明显 continuity 问题。

但它不够敏感于以下真实文本质量问题：

- 证据只是被列出来，没有变成主角压力；
- 推理过程像 worksheet，不像小说场景；
- 章节结尾用抽象总结代替动作、图像或决定；
- 线索推进正确，但阅读节奏笨重；
- 人物的心理变化被解释出来，而不是通过选择呈现。

这就是为什么 `full_revised` 能比 `full_unrevised` 好，但仍不如 `direct_write` 顺。

### 6.3 工程结构没有充分转译成小说表达

full skill 的优势是结构清楚、事实稳定、上下文一致；但 iteration 01 的文本经常把这些中间表示直接暴露给读者。

读者看到的不是“主角被证据逼到必须承认责任”，而是“主角逐项检查线索并得出结论”。这会让文本显得可追踪，但不够有小说阅读感。

## 7. Iteration 02 优化目标

iteration 02 的目标不是增加更多工程文件，而是修改 revision loop 的行为，让它真正承担“文本质量修订器”的角色。

### 7.1 所有章节都进入 revision rewrite

即使某章没有 blocking issue，也应该进入 rewrite prompt。区别只在于：

- 有 blocking issue：必须修复事实、结构、重复、泄漏等硬问题；
- 无 blocking issue：执行 quality polish，提升场景化、节奏、人物压力和结尾力度。

只有模型 rewrite 失败或返回空文本时，才 fallback 原文。

### 7.2 增加默认质量目标

每章 revision plan 都应包含默认 quality targets：

- 把线索 / 证据转化为人物压力和选择；
- 减少程序化记录、清单式推导和 worksheet 感；
- 用场景、对话、动作承载信息；
- 章节结尾避免抽象总结，用具体动作、图像或决定收束；
- 保持事实、reveal order 和长程连续性，不提前揭示。

### 7.3 扩展 built-in review 的启发式

built-in review 应能保守识别：

- 过多“线索一 / 线索二 / 对应关系成立”式表达；
- 反复计算、反复试错但没有新的情绪或行动推进；
- 证据日志式段落；
- 结尾总结式说明。

这些 heuristic 不是最终价值体系，但能作为低成本 guard，帮助 revision loop 更稳定地触发文本质量修订。

### 7.4 支持独立 iteration 02 产物

runner 需要支持 `--start-iteration 2`，使第二轮输出到：

```text
runs/*_v1_revision_iter_02/
revision_eval_runs/v1_chapter_revision/iter_02/
```

不能覆盖 iteration 01，否则无法做横向对比和汇报。

## 8. Iteration 02 验收标准

iteration 02 仍按 Stage A harness-level 文本质量验收：

- `case_05` 和 `case_10` 中，`full_revised` 需要整体超过 `direct_write`；
- `full_revised` 必须继续超过 `full_unrevised`；
- `case_07` 不退化，至少不能低于 `full_unrevised`，理想情况下继续保持第一；
- evaluator 必须基于真实文本证据，而不是工程流程或文件完整性。

如果 iteration 02 仍未通过，则进入 iteration 03。三轮后仍失败，需要输出路线失败报告，说明当前 full skill + revision loop 为什么无法超过 direct_write，并提出 V1.1 方向。
