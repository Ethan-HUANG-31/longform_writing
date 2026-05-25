# V1 Chapter Revision Loop 路线失败报告与 V1.1 建议

## 1. 最终结论

V1 chapter revision loop 已按计划完成 3 轮 harness-level 迭代验证。最终结果是：

- `case_05`：失败，`direct_write` 仍然优于 `full_revised`；
- `case_10`：失败，`direct_write` 仍然优于 `full_revised`；
- `case_07`：通过回归，`full_revised` 稳定优于 `direct_write`、`simple_engineered` 和 `full_unrevised`；
- `full_revised` 在三轮里均优于 `full_unrevised`，说明 revision loop 有增益；
- 但主目标没有达成：`full_revised` 没能在主要测试 `case_05` 和 `case_10` 中整体超过 `direct_write`。

因此，V1 当前路线不能标记为“通过最终验收”。根据任务停止条件，3 轮后应停止继续微调，沉淀失败原因并进入 V1.1 设计。

## 2. 三轮迭代概览

| Iteration | 主要改动 | Blind Result | 结论 |
|---|---|---|---|
| iter_01 | 初版 chapter review -> plan -> rewrite，只修 blocking issue 章节 | 05/10: A > D > C > B；07: D > C > ... | revision 有增益，但 05/10 仍输给 direct |
| iter_02 | 所有章节都进入 rewrite；增加默认 quality targets | 05/10: A > D > C > B；07: D > C > ... | 跳过章节问题解决，但仍有 procedural prose |
| iter_03 | 增加 manuscript-level revision context、previous revised tail、跨章节重复控制 | 05/10: A > D > C > B；07: D > C > ... | prose flow 有局部改善，但主目标仍失败 |

Blind mapping 在三轮中保持一致：

| Sample | Method |
|---|---|
| A | direct_write |
| B | simple_engineered |
| C | full_unrevised |
| D | full_revised |

## 3. Iteration 03 最终盲评结果

### 3.1 Rubric Judge

| Case | Ranking | 关键判断 |
|---|---|---|
| case_05 | A > D > C > B | A 线索最终压到“我签了但没看”的责任承认；D 有完整线索链但物件检视和重复动作仍偏程序化 |
| case_10 | A > D > C > B | A 的社区图书馆谜题更自然，情感落点更完整；D 推理链清楚但解释性段落较重 |
| case_07 | D > C > A > B | D 四段录像逐步升级，结尾以不拨电话和扣下手机收束 |

### 3.2 Reader/Editor Judge

| Case | Ranking | 关键判断 |
|---|---|---|
| case_05 | A > D > C > B | A 的完整性和人物推动最强；D 的本地 prose flow 更稳，但完成感弱于 A |
| case_10 | A > D > C > B | A 最像可读短篇；D 推理更公平，但整体更像侦查笔记 |
| case_07 | D > C > B > A | D 完整性、情绪压力、章节衔接最强 |

## 4. 已经证明有效的部分

### 4.1 工程化 workflow 对复杂长程结构有效

`case_07` 是双时间线 / 四段录像 / 延迟责任揭示结构。三轮盲评中，`full_revised` 都是最强样本。

这说明以下能力成立：

- 章节级拆分能稳定维护复杂结构；
- previous summaries 和 revised summaries 能保持长程连续性；
- revision loop 能让责任链更清楚；
- 在 direct/simple 只能写出开局或早段录像时，full skill 能完成完整长程结构。

所以 V1 不是“工程化写作完全失败”，而是“当前工程化写作在中等复杂度、读者流畅度优先的任务上没有超过 direct_write”。

### 4.2 revision loop 确实带来增益

每一轮里 `full_revised` 都优于 `full_unrevised`：

- `case_05`: D > C
- `case_10`: D > C
- `case_07`: D > C

这说明 review -> plan -> rewrite 不是空转，能稳定减少一部分重复、增强结尾动作、改善局部 prose flow。

### 4.3 V1.0 的评测闭环成立

已验证：

- 可以生成 `direct_write` / `simple_engineered` / `full_unrevised` / `full_revised` 四路对照；
- 可以生成 blind public package 和 private mapping；
- 可以用 Rubric Judge 与 Reader/Editor Judge 做互补评测；
- 可以从盲评证据反推下一轮 prompt 和 runner 改动；
- 外部模型 transient failure 已加重试，长程运行稳定性提升。

这套评测闭环是 V1 的重要资产，应保留到 V1.1。

## 5. 失败原因

### 5.1 当前 workflow 把“事实正确”放在“阅读体验”之前

V1 的写作链路是：

```text
request -> project brief -> codex -> outline -> chapter summary -> scene beats -> beat prose -> summary_after -> chapter review -> revision plan -> chapter rewrite
```

这个链路能保证事实、线索、章节功能和 reveal order，但也会让模型倾向于逐项执行中间表示。结果是：

- 线索链清楚；
- 推理公平；
- 结构完整；
- 但读者经常看到“证据如何被确认”，而不是“证据如何逼迫人物改变行动”。

direct_write 在 `case_05` 和 `case_10` 中胜出，是因为它不被中间工程表示绑住，能从一开始按完整短篇的阅读体验组织材料。

### 5.2 Chapter-level revision 太局部，无法彻底修复全篇阅读弧

iteration 02 和 03 已经让所有章节都进入 rewrite，也加入了 manuscript-level bad smell。

但最终仍失败，说明问题不只是某章局部重复，而是更上层的叙事组织：

- 哪个线索该保留为场景，哪个线索只应成为一句后果；
- 哪些推理过程应该压缩，哪些应该展开；
- 结尾应该完成怎样的情感闭合；
- 哪些章节应承担“调查”，哪些章节应承担“承认/选择”。

这些决策应该在 outline / chapter summary / scene beat 之前或之中完成。等正文已经按工程化 beats 写出来，再逐章 rewrite，只能做局部修补。

### 5.3 Revision prompt 仍被“preserve facts”约束过强

为了避免 hallucination 和提前泄露，V1 rewrite prompt 强调：

- preserve all required facts；
- do not add major events；
- preserve reveal order；
- preserve chapter function。

这些约束必要，但当前没有给模型足够权力做“叙事性重组”。例如：

- 删除重复证据动作；
- 合并两次相似的确认；
- 把推理从解释段落改成对话冲突；
- 把结尾从“意识到责任”改成“承担责任的具体行动”。

模型因此常选择保守改写：文字更顺，但结构仍像证据表。

### 5.4 中等复杂度 case 暴露了 skill 的真实短板

`case_07` 很复杂，direct/simple 容易写不完整，full skill 的结构优势明显。

但 `case_05` 和 `case_10` 是中等复杂度任务，direct_write 可以一次性看到全篇目标，写出完整且更自然的短篇。这类任务对 full skill 更苛刻：

- 只做到“完整”和“一致”不够；
- 必须同时做到“好读”“有温度”“人物被推动”；
- 不能让读者感觉在看工程化线索执行记录。

这说明 V1.1 的目标应该是让工程化 workflow 获得 direct_write 的整体叙事感，而不是继续堆更多局部检查。

## 6. V1.1 建议

### 6.1 在正文生成前增加 Reader-Facing Story Spine

在 outline 和 chapter summary 之间增加一个新的中间表示：

```text
reader_facing_story_spine
```

它不记录工程步骤，而记录读者体验：

- 每章读者应该感到什么变化；
- 每个关键线索如何改变主角的行动或自我认知；
- 哪些信息只需要压缩交代；
- 哪些场景必须展开；
- 结尾要留下什么具体动作、图像或决定。

这一步的作用是把“工程结构”转译成“阅读结构”，让后续 beat 不再只是执行线索链。

### 6.2 把 beat generation 改成 Scene Outcome Beats

当前 beats 容易变成：

```text
发现线索 -> 检查线索 -> 确认线索 -> 得出结论
```

V1.1 应改成：

```text
场景目标 -> 冲突/阻力 -> 线索进入方式 -> 人物压力变化 -> 具体选择或行动后果
```

每个 beat 必须说明：

- 这个 beat 让主角失去什么、承认什么、选择什么；
- 如果只是“确认线索”，必须压缩或合并；
- 不能连续两个 beat 都只是检查物件或解释推理。

### 6.3 增加 Manuscript-Level Structural Rewrite

chapter rewrite 之后，应增加一次全篇结构修订，不是逐章 polish，而是整体判断：

- 哪些段落重复证明同一事实；
- 哪些章节结尾没有行动；
- 哪些线索没有转化为人物压力；
- 哪些场景可以压缩、合并或改成对话冲突；
- 全篇结尾是否完成 central dramatic question。

这一步应输出：

```text
manuscript_revision_plan.json
final_structural_rewrite.md
```

它比 chapter-level rewrite 权限更高，但仍受 reveal order 和事实一致性约束。

### 6.4 区分两种任务路线

V1.1 不应所有任务都走同一强工程流程。

建议按复杂度路由：

| 任务类型 | 推荐路线 |
|---|---|
| 中短篇、单主角、线索少 | direct-style holistic draft + light structure tracking + final review |
| 中等复杂度、多章但单主线 | story spine + outcome beats + chapter write + manuscript-level rewrite |
| 高复杂度、多时间线/多 POV/多设定 | 当前 full skill workflow + stronger structural rewrite |

`case_05` 和 `case_10` 说明：过重的工程化流程会伤害本来可以自然完成的故事。V1.1 应允许“轻工程路线”。

### 6.5 调整评测目标

V1.1 的验收不应只问：

```text
full_revised 是否超过 direct_write？
```

还应拆成：

```text
1. 复杂结构下是否明显优于 direct？
2. 中等复杂度下是否不弱于 direct？
3. 工程化路线是否带来可解释、可修复、可复用的质量收益？
4. 是否能根据任务复杂度选择合适路线？
```

否则会把一个 heavy workflow 强行用于所有任务，导致中等复杂度任务被流程拖累。

## 7. 当前交付状态

已交付：

- V1 chapter-level revision loop；
- `final_unrevised.md` / `final_revised.md` 产物；
- 三轮 blind package；
- two-judge blind evaluation 流程；
- iteration 01/02 报告；
- route failure report；
- 外部模型 transient failure 重试；
- 单元测试覆盖 V1 helper、blind package、iteration routing、rewrite prompt slots、retry。

未达成：

- `case_05` 和 `case_10` 中 `full_revised` 超过 `direct_write`。

因此，V1 当前状态应被标记为：

```text
Engineering loop implemented and validated.
Revision loop improves full skill drafts.
Main text-quality acceptance failed after 3 iterations.
Proceed to V1.1 redesign.
```
