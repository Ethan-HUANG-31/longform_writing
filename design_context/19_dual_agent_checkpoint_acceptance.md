# Dual-Agent Checkpoint Acceptance

This document defines how to test `milestone_review` mode.

Checkpoint behavior cannot be validated by a single static run. It should be tested as a simulated interaction between two roles:

1. User simulator
2. Writing executor

The writing executor may use the low-cost DeepSeek-backed runner for generation.

## Roles

### User Simulator

Purpose:

- simulate the real user's feedback at milestones
- follow the scripted feedback in `test_cases/04_checkpoint_interaction_smoke.md`
- avoid helping the writing executor debug implementation details

Inputs:

- test case
- checkpoint prompt from writing executor
- current checkpoint summary/artifacts if shown by executor

Outputs:

- user feedback message
- optional accept/reject decision

The user simulator should not inspect hidden design documents unless the test case explicitly includes them.

### Writing Executor

Purpose:

- use `longform_writing_skill_v0` normally
- run the workflow in `milestone_review` mode
- generate artifacts using the configured cheap model backend when available
- pause at checkpoints and request feedback
- apply feedback upstream
- continue generation
- record trace and acceptance report

Inputs:

- skill path
- test case path
- output run directory
- model configuration, usually DeepSeek

Outputs:

- writing project artifacts
- `run_records/step_manifest.jsonl`
- rendered prompts
- checkpoint records
- `acceptance_report.md`

## Interaction Flow

Use this flow for `test_cases/04_checkpoint_interaction_smoke.md`:

```text
Writing Executor starts run in milestone_review mode
  -> creates request and project brief
  -> pauses at Checkpoint 1
User Simulator sends Requirement Alignment feedback
Writing Executor updates upstream artifacts and continues
  -> creates codex and outline
  -> pauses at Checkpoint 2
User Simulator sends Story Plan Alignment feedback
Writing Executor updates upstream artifacts and continues
  -> generates chapter 1 summary, beats, validation, prose, summary_after
  -> pauses at Checkpoint 3
User Simulator sends First Chapter Direction feedback
Writing Executor updates upstream artifacts and continues
  -> completes remaining chapters
  -> merges manuscript
  -> writes acceptance report
```

## What This Test Verifies

This test verifies two layers.

### Functional Output

- required story artifacts exist
- story follows adjusted user requirements
- chapter 3 contains the delayed reveal
- chapter 1 and chapter 2 do not reveal too early
- 小美 remains a non-present character after checkpoint feedback

### Process Compliance

- checkpoint prompts happen at the expected milestones
- user feedback is recorded
- feedback is applied to upstream artifacts
- downstream steps resume from the correct point
- prompt assembly reflects updated requirements
- `step_manifest.jsonl` records checkpoints and regenerated steps
- prose is still generated after beats and validation
- rendered prompts exist for regenerated steps

## Required Trace Evidence

The run must provide evidence for each checkpoint:

```json
{
  "workflow_step": "user_checkpoint",
  "checkpoint_name": "story_plan_alignment",
  "status": "feedback_received",
  "user_feedback_summary": "第三章再揭示小帅当年的选择真正伤害了小美。",
  "upstream_files_changed": ["03_outline.json"],
  "downstream_steps_invalidated": ["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"]
}
```

It should also record if the user accepted a checkpoint without changes:

```json
{
  "workflow_step": "user_checkpoint",
  "checkpoint_name": "requirement_alignment",
  "status": "accepted_without_changes"
}
```

## Acceptance Report Requirements

For checkpoint tests, `acceptance_report.md` must include:

- whether all checkpoint prompts appeared
- whether simulator feedback was applied
- which files changed after each feedback item
- whether downstream regeneration happened
- whether final story reflects feedback
- any compliance failures

## Failure Examples

Critical failures:

- writing executor ignores a checkpoint and continues
- feedback is recorded but not applied upstream
- prose continues from stale outline after checkpoint feedback
- no trace exists for checkpoint or regeneration
- user simulator feedback leaks hidden expected solution beyond the scripted feedback

Major failures:

- checkpoint appears too late
- final story follows feedback but trace does not show how
- prompt assembly omits updated context after feedback

Minor failures:

- checkpoint wording is clunky
- feedback summary is incomplete but downstream behavior is correct

## Implementation Note

In the current Codex environment, the user simulator can be a spawned subagent or a scripted test harness. The writing executor can be:

- a fresh Codex agent using the skill manually, or
- a Python acceptance runner that calls DeepSeek for generation steps.

The important property is separation of roles: the writing executor should not know future feedback until the simulated user provides it at the checkpoint.

