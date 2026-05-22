# Smoke Test 04: Checkpoint Interaction

## Purpose

Validate that the skill can pause at key milestones, accept user feedback, update upstream artifacts, and continue without losing workflow traceability.

This test should not check fine-grained prose quality. It checks user alignment behavior.

This test should be run as a dual-agent or dual-role interaction:

1. User simulator provides scripted milestone feedback.
2. Writing executor uses the skill in `milestone_review` mode and may call the cheap DeepSeek-backed model runner for generation.

## Initial User Request

写一个 3 章密室心理惊悚短篇。主角叫小帅，旧同事叫小美。小帅醒在选择室里，被迫重新面对三年前一次项目选择。不要血腥、肢体伤害或超自然解释，风格冷静克制。

Use `milestone_review` mode.

## Simulated Checkpoint Feedback

### Checkpoint 1: Requirement Alignment

User feedback:

```text
方向对，但小美不要作为现实中出场的人物，她只通过旧录音和屏幕资料出现。故事重点放在小帅如何为自己的选择辩解。
```

Expected behavior:

- `01_project_brief.md` updates this constraint.
- later Codex marks 小美 as an old-case related person, not an active present-room participant.
- `writing_log.md` records the feedback.
- trace records a checkpoint step.

### Checkpoint 2: Story Plan Alignment

User feedback:

```text
第三章再揭示小帅当年的选择真正伤害了小美，第一章和第二章不要说破。
```

Expected behavior:

- `03_outline.json` keeps the final reveal in chapter 3.
- chapter 1 and chapter 2 summaries/beats do not reveal the full harm.
- beat validation or prompt constraints prevent premature reveal.
- trace records downstream regeneration if outline changed.

### Checkpoint 3: First Chapter Direction Check

User feedback:

```text
第一章风格可以，但小帅的产品经理式自我辩解再明显一点，减少抽象的压迫感描写。
```

Expected behavior:

- style/character instruction is applied upstream, not only patched in final manuscript.
- either `01_project_brief.md`, `02_codex.json`, or chapter 1 regeneration context records the change.
- chapter 2 prose continues with this adjusted characterization.

## Required Artifacts

- all normal smoke-test artifacts
- `run_records/step_manifest.jsonl`
- rendered prompts
- checkpoint entries in the manifest
- `acceptance_report.md`

## Acceptance Checks

- A user simulator and writing executor interaction is represented, either through agents or a scripted harness.
- Checkpoint entries exist for requirement alignment, story plan alignment, and first chapter direction check.
- User feedback is summarized in `writing_log.md`.
- Feedback changes upstream artifacts before downstream generation continues.
- 小美 does not become an active present-room character after checkpoint 1.
- Chapter 1 and chapter 2 do not reveal the full harm to 小美 after checkpoint 2.
- Chapter 3 contains the reveal.
- Chapter 2+ prompts include prior summary_after and adjusted characterization context.
- The run remains traceable after regeneration.

## Dual-Agent Process Checks

- The writing executor does not receive checkpoint 2 feedback before checkpoint 2.
- The writing executor does not receive checkpoint 3 feedback before checkpoint 3.
- The user simulator only gives the scripted feedback for the current checkpoint.
- The executor pauses and waits for feedback at each checkpoint.
- After feedback, the executor records which upstream files changed and which downstream steps were invalidated.
- Final `acceptance_report.md` separates functional output checks from process compliance checks.
