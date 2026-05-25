# Claude Code 交接文档：Longform Writing Skill 项目

## 1. 项目一句话介绍

本项目在开发一个用于长程小说 / 长篇故事创作的 `longform-writing` skill。

它的核心思想不是让模型直接从用户需求一次性写完整篇，而是把长程写作拆成可追踪、可检查、可修订的工程化流程：

```text
用户需求
-> project brief
-> Codex / story bible
-> outline
-> chapter summary
-> scene beats
-> beat-level prose
-> chapter summary_after
-> manuscript
-> review / revision
-> blind evaluation
```

项目的最终目标是：**让结构化长程写作 skill 在真实文本质量上超过直接写作，同时保留长程一致性、上下文管理、可审计轨迹和可迭代修订能力。**

## 2. 最终目标

最终要产出的不是单篇小说，而是一套可复用的写作 skill / workflow：

1. 用户给出较粗的创作需求后，系统能自动澄清、规划并生成长程文本。
2. 写作过程中维护中间工程表示，包括 project brief、Codex、outline、chapter summary、scene beats、draft、summary_after。
3. 后续章节写作时能使用前文 summary 和当前 text_before，保持章节衔接和上下文一致性。
4. 能在关键里程碑让用户介入 review，然后根据反馈修订上游结构并继续推进。
5. 能对生成文本进行质量评估和 revision loop，而不是只生成一次。
6. 能生成完整运行轨迹，包括 prompt 拼接记录、步骤 manifest、写作日志和验收报告。
7. 能用 blind evaluation 比较不同写作路线：
   - `direct_write`
   - `simple_engineered`
   - `full_unrevised`
   - `full_revised`
8. 长期目标是形成“写作生成器 + 写作评价器”互相迭代的闭环，为后续更高质量的长程写作 skill 以及可能的 SFT 轨迹数据积累打基础。

## 3. 当前总进度

当前分支：

```bash
codex/v1-chapter-revision-loop
```

该分支已 push 到 GitHub。最近关键提交：

```text
6f8bce1 Document V1 revision route failure
b7dccf3 Retry transient DeepSeek response failures
8b2f938 Add manuscript-level V1 revision guidance
10df2b9 Strengthen V1 revision iteration strategy
ff3e1b9 Harden V1 against incomplete V0 drafts
ebe0726 Document V1 final acceptance strategy
2690fbf Require explicit approval for V1 external model export
```

当前状态可以概括为：

```text
V0 基础写作 workflow 已完成。
V1 chapter revision loop 已完成并跑完 3 轮真实验证。
V1 工程闭环成立，revision loop 有增益。
V1 文本质量主目标失败，需要进入 V1.1 重新设计。
```

## 4. V1 最终结论

V1 的目标是：在 `case_05` 和 `case_10` 上，让 `full_revised` 在真实文本盲评中超过 `direct_write`；同时 `case_07` 不能退化。

我们跑了 3 轮：

| Iteration | 主要改动 | 结果 |
|---|---|---|
| iter_01 | 初版 chapter review -> plan -> rewrite，只修 blocking issue 章节 | `case_05/10` 失败，`case_07` 通过 |
| iter_02 | 所有章节都进入 rewrite，增加默认 quality targets | `case_05/10` 仍失败，`case_07` 通过 |
| iter_03 | 增加 manuscript-level revision context 和 previous revised tail | `case_05/10` 仍失败，`case_07` 通过 |

最终盲评排序：

```text
case_05: direct_write > full_revised > full_unrevised > simple_engineered
case_10: direct_write > full_revised > full_unrevised > simple_engineered
case_07: full_revised > full_unrevised > direct/simple
```

关键判断：

- `full_revised` 每轮都优于 `full_unrevised`，说明 revision loop 不是空转。
- `case_07` 复杂结构中，full skill 明显有优势。
- `case_05` 和 `case_10` 中，direct write 的整体阅读体验、情感闭合和自然 prose flow 更好。
- 继续小修 V1 不值得，应进入 V1.1 设计。

最重要的结论文档：

```text
design_context/31_v1_route_failure_report.md
```

Claude Code 接手后应先读这个文件。

## 5. 下一阶段：V1.1 方向

V1.1 不应继续只做 chapter-level patch。当前失败说明问题在更上游：工程化中间表示把模型导向“事实正确 / 线索清楚”，但没有把这些事实转译成读者体验。

建议 V1.1 方向：

1. 增加 `reader_facing_story_spine`
   - 放在 outline 和 chapter summary 之间。
   - 描述每章读者应感到的变化、人物压力、场景展开 / 压缩策略、结尾动作或图像。

2. 把 scene beats 改成 `scene outcome beats`
   - 不是“发现线索 -> 检查线索 -> 确认线索”。
   - 而是“场景目标 -> 冲突/阻力 -> 线索进入方式 -> 人物压力变化 -> 具体选择或行动后果”。

3. 增加 manuscript-level structural rewrite
   - chapter rewrite 之后，再做一次全篇结构修订。
   - 重点处理：重复证明、章节结尾弱、线索未转化为人物压力、全篇 central dramatic question 是否闭合。

4. 按任务复杂度路由
   - 简单 / 中短篇：direct-style holistic draft + light structure tracking。
   - 中等复杂度：story spine + outcome beats + chapter write + manuscript-level rewrite。
   - 高复杂度：当前 full workflow + stronger structural rewrite。

## 6. 目录结构说明

### 6.1 根目录

```text
.
├── .env.example
├── .gitignore
├── NovelCrafter Developmental Editor 写作评价准则拆解.md
├── design_context/
├── docs/superpowers/
├── longform-writing/
├── scripts/
└── test_cases/
```

说明：

- `.env.example`
  - DeepSeek API 配置模板。
  - `.env` 被 git ignore，不会提交。

- `.gitignore`
  - 忽略 `.env`、生成产物和本地运行目录。
  - 特别注意：`runs/`、`baseline_runs/`、`revision_eval_runs/` 都被忽略。
  - Claude Code 从 GitHub clone 后不会拿到这些生成样本。

- `NovelCrafter Developmental Editor 写作评价准则拆解.md`
  - 从 NovelCrafter Developmental Editor prompt 提炼出的质量评价准则。
  - 后续 rubric 设计的重要来源。

### 6.2 `design_context/`

这是项目设计、决策、阶段报告和失败分析的主目录。Claude Code 应优先阅读这里，而不是直接从代码猜背景。

关键文件：

- `01_novelcrafter_observations.md`
  - 对 NovelCrafter 工作流和 prompt 行为的观察。

- `02_longform_writing_skill_v0_scope.md`
  - V0 skill 的范围。

- `03_writing_project_v0_directory.md`
  - V0 写作项目目录结构设想。

- `04_skill_v0_directory.md`
  - skill 本身目录结构设想。

- `05_prompt_patterns_from_novelcrafter.md`
  - 从 NovelCrafter 借鉴的 prompt pattern。

- `06_context_policy.md`
  - 上下文拼接策略早期设计。

- `07_acceptance_checklist.md`
  - V0 验收清单。

- `08_autodev_execution_plan.md`
  - 初始自动开发执行计划。

- `09_user_decision_brief.md`
  - 用户需求和关键决策摘要。

- `10_execution_trace_testing.md`
  - 运行轨迹测试思路。

- `11_skill_create_acceptance_loop.md`
  - skill 创建和验收循环。

- `12_prompt_source_requests.md`
  - 需要用户补充的 prompt source 请求。

- `13_prompt_design_decisions.md`
  - prompt 设计决策。

- `14_novelcrafter_macro_mapping.md`
  - NovelCrafter `include(...)` 宏到本项目 context slot 的映射。

- `15_codex_design.md`
  - Codex / story bible 设计，包括 global entry、relevant codex。

- `16_external_model_acceptance_runner.md`
  - 外部模型 API 验收 runner 设计。

- `17_user_request_contract.md`
  - 用户输入需求 contract。

- `18_user_checkpoint_policy.md`
  - milestone review / user checkpoint 策略。

- `19_dual_agent_checkpoint_acceptance.md`
  - 用双 agent 模拟用户 checkpoint 的设计。

- `20_phase_b_complexity_validation.md`
  - Phase B 复杂度验证设计。

- `21_phase_c_dynamic_genre_prompt_routing.md`
  - Phase C 动态 genre prompt routing 设计。

- `22_baseline_comparison_controls.md`
  - direct/simple baseline 对照设计。

- `23_phase_b_c_integration_report.md`
  - Phase B/C 集成报告。

- `24_quality_rubric_calibration_report.md`
  - 文本质量 rubric 校准报告。

- `25_blind_real_text_quality_calibration_report.md`
  - 真实文本盲评校准报告。

- `26_direct_vs_full_skill_text_quality_gap_report.md`
  - direct write 和 full skill 的质量差异分析。V1/V1.1 都要读。

- `27_v1_revision_loop_task7_status.md`
  - V1 task 7 状态和 blocker 记录。

- `28_v1_final_acceptance_strategy.md`
  - Harness-Level 与 Agent-Level 验收区别。非常重要。

- `29_v1_iteration_01_blind_eval_report.md`
  - V1 第一轮盲评报告。

- `30_v1_iteration_02_blind_eval_report.md`
  - V1 第二轮盲评报告。

- `31_v1_route_failure_report.md`
  - V1 最终路线失败报告和 V1.1 建议。接手必读。

- `32_claude_code_handoff.md`
  - 当前交接文档。

### 6.3 `docs/superpowers/`

这是使用 `superpowers` 工作流生成的设计和执行计划。

```text
docs/superpowers/specs/
docs/superpowers/plans/
```

关键文件：

- `docs/superpowers/specs/2026-05-24-blind-real-text-quality-calibration-design.md`
  - blind real text quality calibration 的设计。

- `docs/superpowers/specs/2026-05-24-v1-chapter-revision-loop-design.md`
  - V1 chapter revision loop 的设计。

- `docs/superpowers/plans/2026-05-24-v1-chapter-revision-loop.md`
  - V1 执行计划。里面包含 TDD、任务拆分、文件修改计划。

Claude Code 若要延续同一风格，应先读这些，理解之前的“设计 -> plan -> subagent-driven execution -> review -> verification”流程。

### 6.4 `longform-writing/`

这是最终 skill 本体。

```text
longform-writing/
├── SKILL.md
├── agents/
├── core_spec/
├── references/
├── scripts/
├── templates/
└── tests/
```

#### `longform-writing/SKILL.md`

Codex skill 的入口说明。

定义：

- 什么时候使用这个 skill；
- V0 核心 workflow；
- operating modes；
- context rules；
- V1 revision mode；
- acceptance standard。

Claude Code 接手后，如果要真正让 Claude/Cloud 环境调用这个 skill，需要确认该环境是否支持类似 Codex skill discovery 的机制。如果没有，就只能把 `SKILL.md` 当作 workflow spec，而不是自动发现的 tool/skill。

#### `longform-writing/agents/`

当前只有：

```text
openai.yaml
```

这里是 agent 配置占位 / 早期配置文件。当前主流程主要由 Python runner 和 Codex subagents 驱动，不是由这个 yaml 独立调度。

#### `longform-writing/core_spec/`

skill 的核心规范目录。

```text
core_spec/
├── context_policy.md
├── workflow.md
├── runtime_contract.yaml
├── prompts/
└── schemas/
```

- `workflow.md`
  - V0/V1 工作流顺序。
  - 说明每一步读什么、写什么。

- `context_policy.md`
  - context 拼接规则。
  - 包括 project brief、codex、previous summaries、text_before、relevant codex 等。

- `runtime_contract.yaml`
  - 运行时文件输入输出 contract。

#### `longform-writing/core_spec/prompts/`

所有 workflow prompt 模板。

V0 prompt：

- `01_parse_request.md`
- `02_build_project_brief.md`
- `03_build_codex.md`
- `04_generate_outline.md`
- `05_generate_chapter_summary.md`
- `06_generate_scene_beats.md`
- `07_validate_scene_beats.md`
- `08_write_beat_prose.md`
- `09_summarize_chapter.md`
- `10_merge_manuscript.md`
- `11_user_checkpoint.md`

V1 prompt：

- `12_review_chapter_quality.md`
- `13_plan_chapter_revision.md`
- `14_rewrite_chapter.md`
- `15_summarize_revised_chapter.md`
- `16_merge_revised_manuscript.md`

当前打开的两个文件：

- `12_review_chapter_quality.md`
  - 章节质量 review prompt。
  - 检查重复、程序化 prose、evidence-log、summary-like conclusion、dialogue pressure 等。

- `14_rewrite_chapter.md`
  - 章节 rewrite prompt。
  - 当前 V1.3 已加入 `previous_revised_tail` 和 `manuscript_revision_context`。
  - 但最终仍未解决 case_05/10 输给 direct 的问题。

V1.1 不建议只继续改这两个 prompt。失败报告指出应改更上游的 story spine / beats / manuscript-level structure。

#### `longform-writing/core_spec/schemas/`

JSON schema / contract 文件：

- `beat_validation.schema.json`
- `chapter_review.schema.json`
- `chapter_revision_plan.schema.json`
- `codex.schema.json`
- `outline.schema.json`
- `revision_acceptance.schema.json`
- `scene_beats.schema.json`

这些用于约束模型输出和测试 prompt contract。

#### `longform-writing/references/`

评价体系参考：

- `quality_rubric_v1.md`
  - 早期质量 rubric。

- `longform_text_quality_rubric_v1.md`
  - V1 主要使用的长程文本质量 rubric。
  - Rubric Judge 盲评时使用。

#### `longform-writing/scripts/`

核心运行脚本。

- `run_acceptance.py`
  - V0 acceptance runner。
  - 使用 DeepSeek API 或 mock provider。
  - 负责从 test case 生成 project brief、codex、outline、chapter drafts、summary_after、final manuscript、run records。
  - 已加入 DeepSeek transient failure retry。

- `run_v1_revision_loop.py`
  - V1 revision loop runner。
  - 在 V0 full draft 基础上做 chapter review、revision plan、rewrite、revised summary、final revised manuscript。
  - 生成四路 blind package。
  - 支持 `--start-iteration`，可单独跑 iter_02 / iter_03。

- `run_baseline_comparison.py`
  - 生成 direct/simple/full 等 baseline 对照的脚本。

- `run_quality_calibration.py`
  - 质量 rubric 校准相关脚本。

- `create_blind_quality_eval.py`
  - 早期 blind quality eval package 工具。

#### `longform-writing/templates/`

写作项目目录模板。

```text
templates/writing_project_v0/
```

包含：

- `00_request.md`
- `01_project_brief.md`
- `02_codex.json`
- `03_outline.json`
- `run_records/step_manifest.jsonl`
- `writing_log.md`

#### `longform-writing/tests/`

当前主要测试：

- `test_v1_revision_helpers.py`

覆盖：

- prompt/schema contract；
- external model export approval；
- blind package builder；
- iteration root；
- start iteration；
- incomplete V0 guard；
- no-must-fix 也 rewrite；
- manuscript-level revision context；
- DeepSeek retry。

当前测试命令：

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

当前通过结果：

```text
Ran 29 tests
OK
```

### 6.5 `scripts/`

根目录脚本，目前主要有：

- `scripts/test_deepseek_api.py`

用于单独测试 DeepSeek API 是否能连通。

### 6.6 `test_cases/`

测试用例目录。

关键 case：

- `01_single_protagonist_choice_room_smoke.md`
  - 最早的单主角简单烟测。

- `02_single_protagonist_continuity_smoke.md`
  - continuity smoke。

- `03_single_protagonist_beat_validation_guard.md`
  - beat validation guard。

- `04_checkpoint_interaction_smoke.md`
  - milestone review / checkpoint 交互测试。

- `05_medium_length_single_protagonist.md`
  - V1 主攻 case。中等长度、单主角、密室 / 道德责任线。

- `06_supporting_cast_codex_routing.md`
  - supporting cast / Codex routing。

- `07_dual_timeline_continuity.md`
  - V1 回归 case。双时间线 / 四段录像 / 复杂责任链。full skill 表现最好。

- `08_genre_romance_adapter_smoke.md`
  - romance genre adapter。

- `09_genre_fantasy_adapter_smoke.md`
  - fantasy genre adapter。

- `10_mystery_clue_fairness_smoke.md`
  - V1 主攻 case。社区图书馆 / 轻推理 / fair-play clue。

- `11_direct_write_baseline_control.md`
  - direct write baseline control。

- `12_simple_engineered_baseline_control.md`
  - simple engineered baseline control。

### 6.7 Ignored artifact directories

这些目录存在于本地，但不会通过 GitHub 传给 Claude Code：

```text
runs/
baseline_runs/
quality_calibration_runs/
blind_quality_eval_runs/
revision_eval_runs/
GPT对话记录/
```

重要影响：

- `runs/` 里有真实生成过程、prompt records、final manuscripts。
- `revision_eval_runs/` 里有 blind package 和 private mapping。
- `baseline_runs/` 里有 direct/simple baseline 输出。

如果 Claude Code 需要原始样本文本，有三种办法：

1. 在当前本机继续访问这些 ignored 目录。
2. 重新运行脚本生成。
3. 手动打包这些 artifact 给 Claude Code。

如果只需要继续设计 V1.1，先读 `design_context/31_v1_route_failure_report.md` 足够。

## 7. 环境与配置

### 7.1 Python

脚本使用 Python 3 标准库为主，没有复杂依赖。

常用命令：

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_acceptance.py longform-writing/scripts/run_v1_revision_loop.py
git diff --check
```

### 7.2 DeepSeek API

`.env.example`：

```text
DEEPSEEK_API_KEY=replace-with-your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LONGFORM_MODEL_PROVIDER=deepseek
```

`.env` 不提交，需要本地自己配置。

V1 runner 调用外部 API 时必须显式加：

```bash
--allow-external-model-export
```

原因：会把本地 test case、context 和 manuscript 发给 DeepSeek 外部 API。

### 7.3 运行 V1 revision loop

主命令：

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --allow-external-model-export \
  --provider deepseek \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --start-iteration 3 \
  --max-iterations 3
```

说明：

- `--start-iteration 1` 生成 `iter_01`。
- `--start-iteration 2` 生成 `iter_02`。
- `--start-iteration 3` 生成 `iter_03`。
- 当前脚本一次 invocation 只跑一轮，跑完会 `break`。

输出：

```text
runs/<case>_v1_revision_iter_XX/
revision_eval_runs/v1_chapter_revision/iter_XX/blind/
```

## 8. Codex 开发期间用到的能力

这一节对 Claude Code 接手很重要。之前开发不是单纯手写代码，而是利用 Codex app 的一些 agentic 能力。

### 8.1 `/goal` 长程任务机制

Codex 中使用了 goal 机制维护长任务目标：

```text
在 codex/v1-chapter-revision-loop 分支上按 Subagent-Driven 执行 V1 chapter revision loop 实现计划。
实现 full skill + chapter-level revision loop，生成 full revised draft，并用 direct/simple/full unrevised/full revised 四路盲评验证。
主攻 case_05 和 case_10，case_07 做回归；最多 3 轮迭代。
停止条件是 full skill revised 在真实文本盲评中整体超过 direct write，且 case_07 不退化；
若 3 轮后仍失败，输出路线失败分析和 V1.1 建议。
```

这个 goal 机制的作用：

- 长任务不会因为单次对话中断而丢失目标。
- 每次恢复时都对照原始 objective。
- 不允许把成功标准缩小成已经完成的部分。
- 如果没达成主目标，但达到“3 轮失败后输出失败报告”的停止条件，也可以结束任务。

Claude Code 接手前需要确认：

- 是否有等价的 long-running objective / plan / resume 机制。
- 是否能在长任务中持久保存目标、停止条件、当前轮次、验证证据。
- 如果没有，需要手动建立一个 `TASK_STATE.md` 或类似文件，记录目标、当前阶段、下一步、停止条件。

建议新建：

```text
design_context/33_v1_1_task_state.md
```

记录 V1.1 长任务状态，避免 Claude Code 长上下文中断后漂移。

### 8.2 Subagent-Driven Development

开发中使用了 `superpowers:subagent-driven-development` 风格：

```text
主线程：负责目标、设计、集成、最终判断。
worker subagent：负责实现具体代码 patch。
reviewer / judge subagent：负责评测、盲评、代码或规范检查。
```

实际用过的 agent 类型：

1. 实现 worker
   - 修改 runner、prompt、tests。
   - 主线程 review 后统一 commit。

2. Rubric Judge
   - 只读取 blind public package 和 rubric。
   - 不读取 private mapping、runs、baseline、git。
   - 输出结构化文本质量评测。

3. Reader/Editor Judge
   - 只读取 blind public package。
   - 不看 rubric。
   - 模拟真实读者 / 编辑判断。

关键隔离原则：

- Judge 不能看到 private mapping。
- Judge 不能读取 `runs/` 或 `baseline_runs/`，否则会破盲。
- 主线程只有在两个 judge 完成后才 reveal `private_mapping.json`。

Claude Code 接手前需要确认：

- 是否支持并行 / 子 agent。
- 是否支持给子 agent 限定可读路径。
- 是否支持等待子 agent 完成并汇总报告。
- 如果不支持路径隔离，应改用手工复制 blind public package 到一个临时目录，只把该目录交给评测 agent。

### 8.3 Blind Evaluation 机制

每轮生成四路样本：

```text
A/B/C/D anonymous samples
```

`private_mapping.json` 保存：

```text
A -> direct_write
B -> simple_engineered
C -> full_unrevised
D -> full_revised
```

评测顺序必须是：

1. 构建 blind public package。
2. 派 Rubric Judge 和 Reader/Editor Judge。
3. 确认两个 judge 都完成。
4. 再读取 private mapping。
5. 根据 mapping 得出 direct/full_revised 谁胜。

不要让评测 agent 看 mapping。

### 8.4 Superpowers skills

Codex 中安装并使用过 `superpowers`：

- `brainstorming`
- `writing-plans`
- `subagent-driven-development`
- `systematic-debugging`
- `test-driven-development`
- `verification-before-completion`
- `using-git-worktrees`

它们的主要价值：

- 先设计再实现；
- 用 implementation plan 拆任务；
- subagent 分工；
- 遇到错误先 root cause，不乱修；
- 先写测试再改功能；
- 完成前必须跑验证。

Claude Code 里不一定有这些 skill。接手时应确认：

- 是否有等价的 plan mode；
- 是否有 Task / subagent 工具；
- 是否有持久任务状态；
- 是否有自动测试 / verification gate；
- 是否能创建 isolated worktree 或至少新分支。

如果没有，需要用 repo 文件替代这些机制：

```text
design_context/33_v1_1_design.md
design_context/34_v1_1_implementation_plan.md
design_context/35_v1_1_task_state.md
```

## 9. 接手建议流程

### Step 1: Checkout 分支

```bash
git fetch origin
git checkout codex/v1-chapter-revision-loop
```

确认：

```bash
git status --short --branch
git log --oneline -8
```

### Step 2: 阅读必读文件

按顺序读：

```text
design_context/31_v1_route_failure_report.md
design_context/28_v1_final_acceptance_strategy.md
design_context/26_direct_vs_full_skill_text_quality_gap_report.md
docs/superpowers/specs/2026-05-24-v1-chapter-revision-loop-design.md
docs/superpowers/plans/2026-05-24-v1-chapter-revision-loop.md
longform-writing/SKILL.md
longform-writing/core_spec/workflow.md
```

### Step 3: 确认 Claude Code 能力

在开始 V1.1 前，先确认：

- 有没有 subagent / Task 工具。
- 有没有 plan / long-running objective 机制。
- 有没有路径隔离能力，用于 blind judge。
- 能否调用 DeepSeek API。
- 能否长期运行超过数小时。
- 如果不能长跑，是否能把状态写入 `design_context/*task_state.md` 并分多次恢复。

### Step 4: 不要直接实现，先写 V1.1 设计

下一步应先写：

```text
design_context/33_v1_1_design.md
```

设计至少覆盖：

- `reader_facing_story_spine`
- `scene_outcome_beats`
- `manuscript_level_structural_rewrite`
- complexity routing
- new acceptance criteria
- new blind eval cases
- how to preserve existing V1 assets

### Step 5: 再写 implementation plan

设计确认后写：

```text
design_context/34_v1_1_implementation_plan.md
```

计划应明确：

- 新增哪些 prompt；
- 新增哪些 schema；
- 修改哪些 runner；
- 保留哪些 V1 tests；
- 新增哪些 V1.1 tests；
- 如何跑最小验证；
- 如何跑完整 blind eval。

## 10. 常见误区

### 10.1 不要把 V1 失败理解为工程化无用

`case_07` 已证明工程化 workflow 对复杂结构有效。

真正问题是：中等复杂度任务中，当前 heavy workflow 伤害了自然阅读体验。

### 10.2 不要继续只改 `12_review` 和 `14_rewrite`

V1 已经尝试过：

- 只修 blocking issue；
- 所有章节 rewrite；
- 加 manuscript-level bad smell；
- 加 previous revised tail。

仍然失败。

所以 V1.1 应改更上游的 story representation，而不是继续 prompt polish。

### 10.3 不要用工程轨迹替代文本质量评估

本项目最重要的评价对象是最终文本质量。

轨迹完整、prompt 拼接正确、文件齐全，只能证明 workflow 执行正确，不能证明小说写得好。

### 10.4 不要让 judge 看到 mapping

blind eval 的公信力来自隔离。评测时必须只给 public package。

### 10.5 不要假设 GitHub 分支包含生成产物

`runs/`、`baseline_runs/`、`revision_eval_runs/` 被 ignore。Cloud Code 如果只 clone GitHub，不会看到三轮原始样本。

## 11. 当前可用命令

测试：

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_acceptance.py longform-writing/scripts/run_v1_revision_loop.py
git diff --check
```

DeepSeek 连通性：

```bash
python3 scripts/test_deepseek_api.py
```

V1 revision loop：

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --allow-external-model-export \
  --provider deepseek \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --start-iteration 1 \
  --max-iterations 3
```

V0 acceptance runner 可从脚本 help 查看参数：

```bash
python3 longform-writing/scripts/run_acceptance.py --help
```

## 12. 建议给 Claude Code 的启动 prompt

可以直接把下面这段给 Claude Code：

```text
你正在接手 longform_writing 项目。当前分支是 codex/v1-chapter-revision-loop。

请先阅读：
- design_context/32_claude_code_handoff.md
- design_context/31_v1_route_failure_report.md
- design_context/28_v1_final_acceptance_strategy.md
- design_context/26_direct_vs_full_skill_text_quality_gap_report.md
- longform-writing/SKILL.md
- longform-writing/core_spec/workflow.md

当前状态：
V0 长程写作 workflow 已完成。
V1 chapter-level revision loop 已实现并完成 3 轮 harness-level blind evaluation。
结论是：revision loop 能提升 full_unrevised，复杂 case_07 中 full_revised 表现最好，但 case_05 和 case_10 中 full_revised 仍输给 direct_write。因此 V1 主验收失败，下一步应进入 V1.1 设计。

在开发前，请先确认你当前环境是否支持：
1. 长程 goal / objective 持久化；
2. subagent / Task 分工；
3. blind judge 路径隔离；
4. DeepSeek API 调用；
5. 多小时任务的 resume 机制。

如果没有，请先设计替代机制，例如用 design_context/35_v1_1_task_state.md 保存任务状态，用临时目录隔离 blind public package。

不要直接实现。第一步是写 V1.1 design doc，重点包括 reader_facing_story_spine、scene_outcome_beats、manuscript-level structural rewrite 和 complexity routing。
```

## 13. 推荐的 V1.1 成功标准草案

V1.1 不应重复 V1 的单一标准，而应拆成层级：

1. `case_07` 复杂结构：必须保持 full route 明显优于 direct/simple。
2. `case_05` / `case_10` 中等复杂度：full route 至少不弱于 direct，并且不能明显更机械。
3. `full_revised` 必须继续优于 `full_unrevised`。
4. 如果启用 complexity routing，系统必须能解释为什么某 case 走 light route / medium route / full route。
5. Blind judge evidence 必须基于文本，而不是基于流程文件。
6. run records 必须仍能审计 prompt 拼接和上下文使用。

## 14. 最后提醒

当前项目的核心经验是：

```text
长程写作不能只工程化上下文。
工程化结构必须先被转译成读者体验结构。
否则 workflow 越完整，文本越容易像执行记录。
```

V1.1 的重点就是解决这件事。
