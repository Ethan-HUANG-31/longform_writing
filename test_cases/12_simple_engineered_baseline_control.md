# Control Test 12: Simple Engineered Baseline

## Purpose

Measure how well a lightweight writing pipeline performs compared with the full longform-writing skill.

This baseline represents a minimal engineering approach:

```text
request -> outline -> chapter drafts -> manuscript
```

It tests whether the full skill's additional artifacts are actually useful.

## Baseline Method

Use two or three prompts.

### Step 1: Outline

```text
请根据用户需求生成章节大纲。只输出每章标题、目标、关键事件和不能提前揭示的信息。
```

### Step 2: Write Chapters

```text
请根据用户需求和章节大纲，按章节写完整正文。
请保持连续性，不要提前揭示大纲中标注为后续章节的信息。
```

Optional Step 3:

```text
请合并章节并做轻微润色，不要改变剧情事实。
```

## Expected Artifacts

```text
baseline_runs/simple_engineered/<case_name>/
  request.md
  outline_prompt.md
  outline.md
  prose_prompt.md
  chapter_01.md
  chapter_02.md
  ...
  manuscript.md
  baseline_report.md
```

## Recommended Source Requests

Run this baseline against:

- `05_medium_length_single_protagonist`
- `06_supporting_cast_codex_routing`
- `07_dual_timeline_continuity`
- `10_mystery_clue_fairness_smoke`

## Checks

### Requirement Fulfillment

- Does the outline cover the required story promise?
- Does the manuscript actually write what the outline planned?
- Are forbidden elements absent?

### Continuity

- Does chapter writing preserve earlier facts?
- Does it remember supporting character roles?
- Does it distinguish past event time from present reveal time?

### Reveal Control

- Does the outline mark protected future information?
- Does the prose obey those reveal boundaries?
- Does the final reveal appear in the correct chapter?

### Intermediate Artifact Usefulness

- Is the outline specific enough to guide writing?
- Can a failure be traced to the outline or prose step?
- Are there enough intermediate artifacts for targeted revision?

### Comparison Against Full Skill

Compare simple engineered output with the full skill on:

- Codex grounding
- beat-level executability
- summary-after memory
- prompt traceability
- localized patchability

## Expected Weaknesses

Simple engineering may outperform direct writing on chapter structure, but it is expected to remain weaker than the full skill on:

- character/entity grounding
- beat-to-prose fidelity
- protecting reveal information from prose context
- revision readiness
- fine-grained traceability

## Pass / Fail Use

This baseline should be treated as a serious competitor.

If simple engineered writing performs similarly to the full skill on Phase B/C tasks, then the full skill should justify or simplify its intermediate representation.

