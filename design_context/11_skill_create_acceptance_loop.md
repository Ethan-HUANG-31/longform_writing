# Skill Create And Acceptance Loop

This document defines the iterative development loop for `longform_writing_skill_v0`.

The process has two major phases:

1. Skill Create
2. Skill Acceptance

The loop repeats until the skill passes the agreed tests.

## Phase 1: Skill Create

Purpose: create or patch the reusable skill itself.

Inputs:

- `design_context/*.md`
- `test_cases/*.md`
- previous acceptance reports, if any

Outputs:

- `longform_writing_skill_v0/`
- updated prompts, schemas, workflow, context policy, helper scripts, or templates
- a short change summary

Responsibilities:

- Follow the V0 design scope.
- Keep the skill as one composite workflow skill.
- Preserve the NovelCrafter-style workflow.
- Generate traceable runtime artifacts.
- Do not optimize for complex literary quality before workflow correctness.

Allowed improvements during creation:

- tighten prompt templates
- add missing step I/O contracts
- add deterministic validation scripts
- improve trace logging
- improve JSON schemas
- clarify context assembly rules
- patch defects found during acceptance

Not allowed in V0:

- complex revision loop
- SFT export
- preference pair export
- multi-agent writing runtime
- seven-character stress-test as primary acceptance
- full evaluator/scoring framework

## Phase 2: Skill Acceptance

Purpose: validate the skill as if it were being used in a fresh writing task.

The acceptance run should happen in a fresh context or fresh agent. It should not rely on hidden knowledge from the creation phase.

Acceptance agent receives only:

- path to `longform_writing_skill_v0/`
- one test case from `test_cases/`
- instruction to use the skill normally
- output directory for the run

Acceptance agent should produce:

- a writing project under `runs/{test_slug}/`
- all expected writing artifacts
- `run_records/step_manifest.jsonl`
- `run_records/rendered_prompts/`
- an acceptance report

## Acceptance Report Format

Each acceptance run should produce:

```text
runs/{test_slug}/acceptance_report.md
```

Required sections:

```markdown
# Acceptance Report

## Test Case

## Pass / Fail

## Artifact Checks

## Workflow Trace Checks

## Prompt Assembly Checks

## Content Checks

## Critical Failures

## Minor Issues

## Patch Recommendations
```

## Failure Classification

Use these categories so the create phase can patch efficiently.

### Critical

- required files missing
- JSON files fail to parse
- prose generated before beats
- prose generated before beat validation
- rendered prompts missing
- step manifest missing or invalid
- chapter 2+ prose prompt lacks previous summaries
- manuscript generated directly from original request instead of chapter drafts
- validation failure ignored and prose continues silently

### Major

- required context section missing from rendered prompt
- output exists but cannot be consumed by next step
- outline chapter count and chapter folders mismatch
- summary_after does not record key continuity facts
- prohibited content appears despite clear request

### Minor

- awkward prose
- weak style adherence
- repetitive language
- non-blocking naming inconsistency
- trace metadata incomplete but core order is clear

## Iteration Loop

Use this loop:

```text
Skill Create
  -> Structural Review
  -> Skill Acceptance in fresh context
  -> Acceptance Report
  -> Patch Skill
  -> Re-run Acceptance
  -> Repeat until pass
```

## Acceptance Agent Prompt Pattern

Use a prompt like:

```text
Use the longform writing skill at:
{skill_path}

Run this test case:
{test_case_path}

Create the writing project under:
{run_output_dir}

Use the skill as a normal user-facing workflow. Produce the required project artifacts, run records, rendered prompts, and an acceptance report. Do not inspect design_context unless the skill itself instructs you to. Report failures instead of silently repairing the skill.
```

## Anti-Contamination Rule

The acceptance agent should not receive:

- the creator's diagnosis
- expected patch list
- hidden implementation notes
- prior failed rendered prompts unless this is a targeted regression test

It should test whether the skill itself is clear and usable.

## Dual-Agent Acceptance For Checkpoints

For `milestone_review` checkpoint tests, use a dual-role setup:

- User simulator: provides only the scripted checkpoint feedback from the test case.
- Writing executor: uses the skill normally and pauses at milestones.

The writing executor should not receive later checkpoint feedback early. The acceptance report must verify both final artifacts and process compliance.

See `design_context/19_dual_agent_checkpoint_acceptance.md`.

## Stop Condition

The loop can stop when:

- `01_single_protagonist_choice_room_smoke` passes
- `02_single_protagonist_continuity_smoke` passes
- `03_single_protagonist_beat_validation_guard` passes or produces the required pre-prose failure
- no critical failures remain
- major failures are either fixed or explicitly deferred
