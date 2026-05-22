# User Checkpoint Policy V0

This document defines where `longform_writing_skill_v0` should pause for user feedback during real writing runs.

The goal is to let users correct direction at important milestones without turning the workflow into line-by-line manual editing.

## Modes

V0 supports two execution modes.

### 1. Full Auto

Use for:

- smoke tests
- acceptance runs
- cheap model end-to-end checks
- users who explicitly ask for no pauses

Behavior:

- run from request to manuscript without user checkpoints
- still record all prompts, outputs, and trace files
- if validation fails, stop before prose or regenerate once according to validation policy

### 2. Milestone Review

Use for:

- real writing tasks where user wants direction control
- uncertain requirements
- longer stories
- first run of a new style/genre

Behavior:

- pause only at major milestones
- summarize current artifacts
- ask for targeted feedback
- apply feedback to the appropriate upstream files
- continue after alignment

## Recommended Checkpoints

### Checkpoint 1: Requirement Alignment

Timing:

After `00_request.md` and `01_project_brief.md` are created, before Codex and outline generation.

Purpose:

Confirm the skill understood the user's core intent.

Show user:

- title or working title
- genre
- premise
- protagonist
- main conflict
- tone
- hard constraints
- default assumptions

Ask:

```text
这是我理解的写作需求。请确认是否方向正确，或者指出需要改的地方：题材、主角、核心冲突、禁忌、风格、章节数。
```

If user changes direction:

- update `01_project_brief.md`
- append feedback to `writing_log.md`
- record the checkpoint in `run_records/step_manifest.jsonl`
- rerun downstream steps from `build_codex`

### Checkpoint 2: Story Plan Alignment

Timing:

After `02_codex.json` and `03_outline.json` are generated, before chapter summaries and beats.

Purpose:

Confirm story structure before generating prose.

Show user:

- major Codex entries, especially global/always-include entries
- chapter list
- each chapter's one-paragraph summary
- planned reveal timing
- what will not be revealed early

Ask:

```text
这是设定库和三章大纲。请重点看：人物是否对、章节推进是否符合预期、反转是否放在正确位置、有没有不该出现的内容。
```

If user changes plan:

- update `02_codex.json` if facts or constraints change
- update `03_outline.json`
- append feedback to `writing_log.md`
- rerun downstream chapter summary and prose steps

### Checkpoint 3: First Chapter Direction Check

Timing:

After `chapters/chapter_01/02_draft.md` and `chapters/chapter_01/03_summary_after.md` are generated.

Purpose:

Catch style, pacing, POV, and premise mismatch early, before producing the whole manuscript.

Show user:

- chapter 1 draft excerpt or full chapter if short
- chapter 1 summary_after
- a short note about which beats were covered

Ask:

```text
第一章已经生成。请确认风格、节奏、主角感觉、惊悚强度是否合适。你可以提出方向性修改，不需要逐句改。
```

If user requests changes:

- classify feedback as style, premise, codex, outline, or chapter-level issue
- patch the closest upstream artifact
- regenerate chapter 1 if needed
- do not proceed to chapter 2 until chapter 1 direction is accepted

### Optional Checkpoint 4: Final Review

Timing:

After `manuscript/draft_full.md` is generated.

Purpose:

Let user decide whether V0 final equals draft or whether future revision is needed.

V0 should not perform complex revision unless explicitly asked and supported by a later version.

## What Not To Ask

Do not ask after:

- every beat
- every paragraph
- every Codex entry
- every prompt render
- every validation pass unless it fails

Too many checkpoints defeat the purpose of automation.

## Feedback Application Rules

User feedback should be applied upstream, not patched only in final prose.

Examples:

- "小帅不应该这么软弱" -> update Codex and regenerate affected chapter prose.
- "不要这么早揭示钥匙用途" -> update outline / chapter summary / beat validation.
- "风格太夸张" -> update project brief style constraints and prose prompt context.
- "小美不要出场，只作为录音里的声音" -> update Codex and outline.

## Trace Requirements

Each checkpoint should be recorded in `run_records/step_manifest.jsonl`:

```json
{
  "step_id": "checkpoint_02_story_plan_alignment",
  "workflow_step": "user_checkpoint",
  "input_files": ["01_project_brief.md", "02_codex.json", "03_outline.json"],
  "output_files": ["writing_log.md"],
  "status": "accepted",
  "user_feedback_summary": "用户确认大纲，但要求第三章才揭示蓝色钥匙用途。"
}
```

If feedback causes regeneration, record:

- which upstream files changed
- which downstream steps were invalidated
- where regeneration resumed

## Default For V0

For normal user-facing writing:

- use Milestone Review by default
- include Checkpoint 1, 2, and 3

For automated acceptance testing:

- use Full Auto unless the test explicitly covers checkpoint behavior

