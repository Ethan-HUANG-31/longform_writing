# Acceptance Checklist

Use this checklist to review any generated `longform_writing_skill_v0`.

Acceptance should be run in a fresh context or fresh agent after the skill is created. The acceptance agent should use the skill as a normal workflow and produce `acceptance_report.md` under the test run directory.

## Structure

- The implementation contains a platform-neutral core spec or clearly separated workflow files.
- It includes a writing project template.
- It creates a new runtime project directory per writing task.
- It does not require the user to manually create or paste the project directory.
- It includes `run_records/step_manifest.jsonl` and `run_records/rendered_prompts/` for trace-based validation.

## Workflow Completeness

- The workflow runs from user request to final manuscript.
- It can parse a concise natural-language user request into an actionable project brief.
- It includes project brief generation.
- It includes Codex generation.
- It includes outline generation.
- It includes chapter summary generation.
- It includes scene beat generation.
- It includes scene beat validation before prose generation.
- It includes beat-level prose generation.
- It includes summary-after generation.
- It includes manuscript merge.

## Step I/O

- Every step declares what it reads.
- Every step declares what it writes.
- Every downstream input is produced by an earlier step or provided by the user.
- No required runtime file is orphaned or unused without explanation.
- Every model-generation step records its prompt template, input files, rendered prompt path, output files, and status.

## Prompt Templates

- Every prompt file has Purpose, Inputs, Output, Constraints, Prompt Template, and Failure Cases.
- Prompt templates preserve NovelCrafter-style mechanisms without copying platform-specific syntax.
- Prompt templates use platform-neutral context slots instead of NovelCrafter `include(...)` macros.
- Beat-to-prose prompts use story so far, text before, current beat, relevant Codex, and project brief.
- Codex entries distinguish global/always-include context from relevant/on-demand context.
- Beat and chapter planning outputs expose `required_codex` when possible.
- Summarization prompts produce factual memory, not critique.
- Beat validation checks timeline and chapter-summary alignment.
- Rendered prompts can be inspected to verify the expected context sections were assembled.

## V0 Scope Control

- No complex revision workflow.
- No SFT export.
- No preference pairs.
- No multi-agent orchestration.
- No complex subplot tracker.
- No full evaluator/scoring framework.
- No requirement to optimize literary quality before the first runnable version.

## Smoke Test

A minimal task should theoretically produce:

- `00_request.md`
- `01_project_brief.md`
- `02_codex.json`
- `03_outline.json`
- at least three chapter folders
- each chapter's summary, beats, draft, and summary after
- `manuscript/draft_full.md`
- `manuscript/final.md`
- `run_records/step_manifest.jsonl`
- rendered prompts for the main workflow steps

## Trace Checks

- `step_manifest.jsonl` is valid JSONL.
- Each step references a prompt template that exists.
- Each step's input files exist at the time they are used.
- Each step's output files exist after the step succeeds.
- Prose generation occurs only after beat generation and beat validation.
- Chapter 2+ prose generation references earlier `03_summary_after.md`.
- Beat-to-prose rendered prompts include current beat and text before.
- Beat-to-prose rendered prompts do not include future chapter summaries.

## Acceptance Report

- `acceptance_report.md` exists for each test run.
- It states Pass or Fail.
- It separates artifact checks, workflow trace checks, prompt assembly checks, and content checks.
- It lists critical failures before minor issues.
- It gives concrete patch recommendations when failing.

## User Checkpoint Checks

For milestone-review mode:

- Requirement alignment checkpoint occurs after project brief and before Codex/outline generation.
- Story plan checkpoint occurs after Codex/outline and before prose generation.
- First chapter direction checkpoint occurs after chapter 1 draft and summary_after.
- User feedback is applied to upstream artifacts before downstream generation continues.
- Checkpoint decisions and feedback summaries are recorded in `writing_log.md` and `step_manifest.jsonl`.
- Checkpoint acceptance can be run with separate user-simulator and writing-executor roles.
- The writing executor does not receive later checkpoint feedback before the relevant checkpoint.
- Acceptance report distinguishes final output quality from process compliance.
