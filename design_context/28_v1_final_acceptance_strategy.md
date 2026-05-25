# V1 最终验收策略：Harness-Level 与 Agent-Level

## 1. 背景

V1 chapter revision loop 当前包含两类不同的验证问题：

1. 这套 prompt / context / revision loop 本身是否能提升真实文本质量；
2. `longform-writing` skill 是否能被 Codex agent 在真实使用场景中稳定执行。

这两件事相关，但不是同一个验收层级。后续不能把其中一个结果直接等同于另一个。

## 2. Harness-Level 验收

Harness-level 验收由 `run_v1_revision_loop.py` 执行。

它验证的是：

- prompt 模板是否能被稳定拼接；
- Codex / previous summaries / chapter text / revision plan 是否能按预期进入上下文；
- chapter review -> revision plan -> rewrite -> revised summary -> final revised manuscript 是否能形成闭环；
- `direct_write` / `simple_engineered` / `full_unrevised` / `full_revised` 四路 blind package 是否能生成；
- `full_revised` 是否在真实文本盲评中超过 `direct_write` 和 `full_unrevised`。

它不验证：

- Codex agent 是否会自主发现并调用这个 skill；
- agent 在没有 runner 强约束时是否会漏步骤；
- agent 是否会严格遵守文件 contract 和记录 contract；
- agent 面对异常时是否会正确恢复。

Harness-level 的价值是经济、可重复、可批量、可追踪。它适合用于早期迭代 prompt、context policy、revision loop 和 rubric。

## 3. Agent-Level 验收

Agent-level 验收应在 harness-level 通过之后执行。

它验证的是：

- 新开 Codex agent 后，agent 是否能根据 `longform-writing/SKILL.md` 正确理解任务；
- agent 是否按 skill 的工作流执行，而不是直接整篇写作；
- agent 是否生成 project brief、Codex、outline、chapter summaries、beats、drafts、summary_after、revised drafts、final revised manuscript；
- agent 是否保留 prompt / run record / writing log 等轨迹；
- agent 是否能在真实对话中执行 checkpoint 或 milestone review；
- agent 是否能把最终产物组织成可评测的 blind package。

Agent-level 的价值是验证 skill 在 Codex 生态里的真实可用性。它成本更高、随机性更强，也更难定位失败来源，所以不适合作为早期 prompt 迭代的唯一手段。

## 4. 两层验收的差异

| 维度 | Harness-Level | Agent-Level |
|---|---|---|
| 测试对象 | prompt/context/revision loop | skill 被 agent 实际使用 |
| 执行者 | Python runner + 模型 API | Codex agent |
| 可重复性 | 高 | 中等 |
| 成本 | 低到中 | 高 |
| 轨迹稳定性 | 高 | 依赖 agent 执行质量 |
| 主要风险 | runner 过度理想化执行流程 | agent 漏步骤或擅自简化 |
| 适合阶段 | 设计迭代、质量对比、rubric 校准 | 最终验收、真实使用验证 |

结论：harness-level 是经济的实验台，不是最终产品验收的全部；agent-level 是最终 skill 验收必需的一环，但应建立在 harness 已经证明 revision loop 有文本质量收益之后。

## 5. 推荐最终验收顺序

### Stage A: Harness-Level 文本质量验收

运行：

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --allow-external-model-export \
  --provider deepseek \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --max-iterations 3
```

生成：

```text
runs/*_v1_revision_iter_01/manuscript/final_unrevised.md
runs/*_v1_revision_iter_01/manuscript/final_revised.md
revision_eval_runs/v1_chapter_revision/iter_01/blind/public/
revision_eval_runs/v1_chapter_revision/iter_01/blind/private_mapping.json
```

然后派两个 blind evaluator：

- Rubric Judge：使用 `longform-writing/references/longform_text_quality_rubric_v1.md`；
- Reader/Editor Judge：不看 rubric，只按真实阅读质量判断。

Stage A 通过条件：

- `case_05` 和 `case_10` 中，`full_revised` 整体排名超过 `direct_write`；
- `full_revised` 同时超过 `full_unrevised`，证明 revision loop 有增益；
- `case_07` 不退化，即 longform continuity 和复杂结构不弱于原 full skill；
- blind judge 的证据必须来自文本本身，而不是工程流程。

如果 Stage A 失败：

- 最多执行 3 轮 revision loop / prompt 修订；
- 每轮必须沉淀 failure modes 和下一轮 revision strategy；
- 3 轮后仍失败，则输出 route-failure report 和 V1.1 建议。

### Stage B: Agent-Level Skill 使用验收

在 Stage A 通过后，新开 Codex agent 或独立 thread，给出同一类测试 case，让 agent 使用 `longform-writing` skill 完成写作。

Agent 不应直接调用 `run_v1_revision_loop.py` 代替执行全部思考，而应按 skill contract 生成并维护中间文件。

Stage B 检查点：

- agent 是否明确加载并遵守 `longform-writing/SKILL.md`；
- 是否生成完整中间工程表示；
- chapter 2+ 是否使用 previous summaries；
- revision loop 是否产生 `04_chapter_review`、`05_revision_plan`、`02_revised_draft`、`03_summary_after_revised`；
- 是否生成 `final_unrevised.md` 与 `final_revised.md`；
- 是否生成可盲评的四路对照包；
- writing log 和 prompt/run record 是否足以审计执行轨迹。

Stage B 通过条件：

- agent 执行轨迹符合 skill contract；
- 没有直接整篇写作绕过工作流；
- 最终文本在 blind evaluation 中不明显低于 Stage A 的 harness 结果；
- 如果出现执行偏差，偏差必须可通过 skill 文档或 runner contract 修复。

## 6. 当前 V1 的定位

当前 V1 长程任务尚未完成最终验收。

已完成的是：

- V1 runner 与 revision loop 工程实现；
- prompt/schema/helper/test/docs；
- external DeepSeek path 的显式授权开关；
- Task 7 blocker 文档。

未完成的是：

- DeepSeek-backed harness-level 真实生成；
- 四路 blind evaluation；
- 根据盲评反馈进行 revision loop 迭代；
- agent-level 最终验收。

因此，当前不能声称 V1 skill 已经满足最终需求。下一步应先完成 Stage A，再进入 Stage B。
