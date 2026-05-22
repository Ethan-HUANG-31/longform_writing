# User Decision Brief

This file records the remaining decisions needed before fully automated development of `longform_writing_skill_v0`.

The goal is to avoid blocking on every small choice. Each item has a recommended default. If the user does not override it, use the default.

## A. Decisions That Need User Confirmation

### 1. First Target Platform

Recommended default: Codex skill first, with a platform-neutral `core_spec/`.

Reason: the current workspace is Codex, and `skill-creator` validation can verify Codex skill structure. Keeping `core_spec/` makes later Claude Code packaging easier.

Options:

- Codex-first
- Claude Code-first
- platform-neutral spec only

### 2. Delivery Location

Recommended default: create `longform_writing_skill_v0/` inside this repo first.

Reason: this keeps the work reviewable before installing it globally. After validation, copy or install into `$CODEX_HOME/skills`.

Options:

- repo-local only
- install directly into `$CODEX_HOME/skills`
- repo-local first, then install after approval

### 3. Execution Mode

Recommended default: workflow skill plus helper scripts, not a full autonomous model-calling CLI yet.

Reason: V0 should make Codex/Claude follow the workflow and produce files. A fully automated API runner needs provider credentials, cost limits, retry policy, and model selection. That can be a later runtime layer.

Options:

- guidance/workflow skill only
- workflow skill plus deterministic helper scripts
- full CLI that calls models automatically

Updated note: for cheaper longform acceptance tests, V0 may include an optional external model runner script. Codex still orchestrates/reviews, but writing-generation steps can call a configured external API such as DeepStack. See `design_context/16_external_model_acceptance_runner.md`.

### 4. Human Intervention

Recommended default: fully automatic for smoke tests, with optional user checkpoints in normal usage.

Reason: automatic tests need no pauses, but real writing may benefit from confirming brief, codex, or outline.

Options:

- fully automatic after initial request
- pause after project brief
- pause after outline
- pause on validation failure only

### 5. First Output Language

Recommended default: Chinese-first, inherit the user's request language for final prose.

Reason: the source exploration and intended smoke tests are Chinese. Intermediate files can use the same language as the request unless schema keys require English.

Options:

- Chinese-first
- English-first
- bilingual

## B. Defaults I Will Use Unless Overridden

### Story Scale

- Default smoke test length: 3 chapters.
- Default beats per chapter: 5-8 beats.
- Default prose per beat: 300-700 Chinese characters.
- Default manuscript length for smoke tests: short draft, not polished novella.

### Runtime Directory

Use:

```text
runs/{project_slug}/
```

Slug rule:

- lowercase ASCII when possible
- replace spaces with hyphens
- strip unsafe characters
- append numeric suffix on collision
- chapters use `chapter_01`, `chapter_02`, etc.

### Validation Failure Behavior

Default:

1. Write validation result.
2. Regenerate or patch invalid beats once.
3. Re-run validation.
4. If still failing, stop before prose and report the issue.

Never silently write prose from invalid beats.

### Resume and Overwrite Behavior

Default:

- Do not overwrite `00_request.md`.
- If a step output already exists and is non-empty, treat it as completed unless the user asks to rerun.
- On rerun, write backups only for generated artifacts that are about to be replaced.
- Resume from the first missing or invalid required file.

### JSON Strictness

Default:

- Schemas define required fields for `codex`, `outline`, `scene_beats`, and `beat_validation`.
- JSON files must parse.
- Do not allow markdown fences inside JSON outputs.
- Include stable IDs where useful, but keep V0 schemas minimal.

### Context Selection

Default:

- For planning steps, allow full `project_brief` and full minimal `codex`.
- For beat-to-prose, use relevant Codex selected by explicit names in chapter summary and beats.
- If relevant selection is ambiguous and Codex is small, include full Codex.
- Never include future chapter summaries during current chapter drafting unless explicitly required.

### Logging

`writing_log.md` should record:

- step name
- input files
- output files
- validation status
- retry count
- brief error note if any

V0 does not need complete model call tracing.

## C. Test Suite To Use

Initial test cases:

- `test_cases/00_test_strategy.md`
- `test_cases/01_single_protagonist_choice_room_smoke.md`
- `test_cases/02_single_protagonist_continuity_smoke.md`
- `test_cases/03_single_protagonist_beat_validation_guard.md`
- `test_cases/04_checkpoint_interaction_smoke.md`

These cover:

- NovelCrafter-like psychological thriller workflow
- cross-chapter continuity
- validation before prose generation
- user checkpoint and feedback alignment behavior

Additional useful tests later:

- one English request if English support is required
- one contradictory request that should ask for clarification
- one oversized request that should be scoped down

## D. Recommended Long-Running Automation Loop

Use this two-phase loop:

1. Skill Create: main/worker agent builds or patches `longform_writing_skill_v0/`.
2. Structural Review: reviewer checks implementation against `design_context/`.
3. Skill Acceptance: fresh agent uses the skill on `test_cases/01_single_protagonist_choice_room_smoke.md`.
4. Acceptance Report: fresh agent reports artifact, trace, prompt assembly, and content failures.
5. Patch: main/worker agent patches the skill based on concrete failures.
6. Re-run Acceptance: fresh agent reruns the same or next test case.
7. Repeat until smoke, continuity, and validation-guard tests pass.
8. Finalize and optionally install the skill.

Do not begin prompt quality polishing until all required files and workflow contracts pass.

See `design_context/11_skill_create_acceptance_loop.md` for the detailed protocol.

## E. Definition of Done For This Development Task

The automated development task is done when:

1. `longform_writing_skill_v0/` exists.
2. It has a valid `SKILL.md`.
3. It has a platform-neutral core spec.
4. It has prompt templates for every workflow step.
5. It has schemas for the key JSON outputs.
6. It has a writing project template.
7. It has a runtime contract mapping reads and writes.
8. It passes basic skill validation.
9. It passes static artifact checks for the required structure.
10. It can complete at least one smoke test or produce a clear failure report before prose generation.

Optional extension:

- It can run acceptance in static/mock mode without external API calls.
- It can later run generation steps through an external low-cost model runner when credentials are configured.
